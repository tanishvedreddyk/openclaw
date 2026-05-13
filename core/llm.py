"""
OpenClaw LLM Client — OpenAI-compatible, works with Ollama, OpenAI, Nvidia NIM, or any custom endpoint.
Supports streaming and full function-calling (tool use).
"""
import json
from typing import AsyncGenerator, List, Dict, Any
from openai import AsyncOpenAI
from core.config import cfg
from core.skills import TOOL_SCHEMAS, call_tool


def _make_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        base_url=cfg.LLM_BASE_URL,
        api_key=cfg.LLM_API_KEY,
    )


async def chat_stream(
    messages: List[Dict[str, Any]],
    model: str | None = None,
) -> AsyncGenerator[str, None]:
    """
    Stream a response from the LLM. Handles tool calls internally
    and yields final text tokens as they arrive.
    """
    client = _make_client()
    model  = model or cfg.LLM_MODEL
    tools  = TOOL_SCHEMAS if cfg.ENABLE_SKILLS else None

    # Add system prompt if not present
    full_messages = messages[:]
    if not full_messages or full_messages[0]["role"] != "system":
        full_messages.insert(0, {"role": "system", "content": cfg.SYSTEM_PROMPT})

    # Agentic loop — keep calling until no more tool calls
    while True:
        kwargs = dict(
            model=model,
            messages=full_messages,
            max_tokens=cfg.LLM_MAX_TOKENS,
            temperature=cfg.LLM_TEMPERATURE,
            stream=True,
        )
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        # Collect full response while streaming tokens
        collected_text   = ""
        collected_calls  = {}   # id -> {name, arguments_str}
        finish_reason    = None

        stream = await client.chat.completions.create(**kwargs)
        async for chunk in stream:
            delta  = chunk.choices[0].delta
            reason = chunk.choices[0].finish_reason

            if delta.content:
                collected_text += delta.content
                yield delta.content

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in collected_calls:
                        collected_calls[idx] = {
                            "id":   tc.id or f"call_{idx}",
                            "name": tc.function.name or "",
                            "args": ""
                        }
                    if tc.function.name:
                        collected_calls[idx]["name"] = tc.function.name
                    if tc.function.arguments:
                        collected_calls[idx]["args"] += tc.function.arguments

            if reason:
                finish_reason = reason

        # No tool calls — we're done
        if not collected_calls:
            break

        # Append assistant message with tool_calls
        tool_call_list = [
            {
                "id":       v["id"],
                "type":     "function",
                "function": {"name": v["name"], "arguments": v["args"]}
            }
            for v in collected_calls.values()
        ]
        full_messages.append({
            "role":       "assistant",
            "content":    collected_text or None,
            "tool_calls": tool_call_list,
        })

        # Execute tools and append results
        for tc in tool_call_list:
            fn   = tc["function"]
            name = fn["name"]
            try:
                args = json.loads(fn["arguments"])
            except json.JSONDecodeError:
                args = {}

            yield f"\n\n⚙️ *Using tool: `{name}`...*\n"
            result = call_tool(name, args)

            full_messages.append({
                "role":        "tool",
                "tool_call_id": tc["id"],
                "content":     result,
            })
            yield f"```\n{result[:800]}\n```\n\n"

        # Loop back to let LLM process tool results


async def chat_once(
    messages: List[Dict[str, Any]],
    model: str | None = None,
) -> str:
    """Non-streaming version — returns complete response string."""
    result = []
    async for token in chat_stream(messages, model=model):
        result.append(token)
    return "".join(result)
