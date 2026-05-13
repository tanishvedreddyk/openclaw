"""
OpenClaw Skills — tools exposed to the LLM via function calling.
"""
import subprocess, json, os, datetime, math, platform, shutil, textwrap
from pathlib import Path

WORKSPACE = Path("/workspace")
WORKSPACE.mkdir(exist_ok=True)


# ─── Tool schemas (OpenAI format) ─────────────────────────────────────────────

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the internet for current information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_code",
            "description": "Execute Python code and return stdout/stderr. Great for calculations, data processing, or any computation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code":     {"type": "string", "description": "Python code to execute"},
                    "timeout":  {"type": "integer", "description": "Timeout in seconds (default 15)"}
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_shell",
            "description": "Execute a shell (bash) command. Use for system operations, file management, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Bash command to run"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds (default 10)"}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path (relative to /workspace)"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file in the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path":    {"type": "string", "description": "File path (relative to /workspace)"},
                    "content": {"type": "string", "description": "Content to write"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in the workspace directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path (default: /workspace)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": "Get current system info: CPU, RAM, disk, OS, uptime, date/time.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
]


# ─── Tool implementations ──────────────────────────────────────────────────────

def web_search(query: str) -> str:
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=5):
                results.append(f"**{r['title']}**\n{r['href']}\n{r['body']}\n")
        return "\n---\n".join(results) if results else "No results found."
    except Exception as e:
        return f"Search error: {e}"


def run_code(code: str, timeout: int = 15) -> str:
    try:
        result = subprocess.run(
            ["python3", "-c", code],
            capture_output=True, text=True,
            timeout=timeout
        )
        out = result.stdout.strip()
        err = result.stderr.strip()
        parts = []
        if out: parts.append(f"STDOUT:\n{out}")
        if err: parts.append(f"STDERR:\n{err}")
        return "\n".join(parts) or "(no output)"
    except subprocess.TimeoutExpired:
        return f"Timed out after {timeout}s"
    except Exception as e:
        return f"Error: {e}"


def run_shell(command: str, timeout: int = 10) -> str:
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True,
            text=True, timeout=timeout
        )
        out = result.stdout.strip()
        err = result.stderr.strip()
        parts = []
        if out: parts.append(out)
        if err: parts.append(f"STDERR: {err}")
        return "\n".join(parts) or "(no output)"
    except subprocess.TimeoutExpired:
        return f"Timed out after {timeout}s"
    except Exception as e:
        return f"Error: {e}"


def read_file(path: str) -> str:
    try:
        target = WORKSPACE / path
        return target.read_text()
    except Exception as e:
        return f"Error reading file: {e}"


def write_file(path: str, content: str) -> str:
    try:
        target = WORKSPACE / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        return f"Written {len(content)} bytes to {target}"
    except Exception as e:
        return f"Error writing file: {e}"


def list_files(path: str = "") -> str:
    try:
        target = Path(path) if path else WORKSPACE
        files = list(target.rglob("*"))
        return "\n".join(str(f.relative_to(WORKSPACE)) for f in files if f.is_file()) or "(empty)"
    except Exception as e:
        return f"Error: {e}"


def get_system_info() -> str:
    try:
        disk  = shutil.disk_usage("/")
        mem   = Path("/proc/meminfo").read_text()
        mem_total = next((l.split()[1] for l in mem.splitlines() if "MemTotal" in l), "?")
        mem_free  = next((l.split()[1] for l in mem.splitlines() if "MemAvailable" in l), "?")
        uptime = Path("/proc/uptime").read_text().split()[0]
        return (
            f"OS: {platform.system()} {platform.release()}\n"
            f"Arch: {platform.machine()}\n"
            f"CPUs: {os.cpu_count()}\n"
            f"RAM total: {int(mem_total)//1024} MB\n"
            f"RAM free: {int(mem_free)//1024} MB\n"
            f"Disk total: {disk.total//1024**3} GB\n"
            f"Disk free: {disk.free//1024**3} GB\n"
            f"Uptime: {float(uptime)/3600:.1f}h\n"
            f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    except Exception as e:
        return f"Error: {e}"


# ─── Dispatcher ───────────────────────────────────────────────────────────────

HANDLERS = {
    "web_search":     lambda a: web_search(**a),
    "run_code":       lambda a: run_code(**a),
    "run_shell":      lambda a: run_shell(**a),
    "read_file":      lambda a: read_file(**a),
    "write_file":     lambda a: write_file(**a),
    "list_files":     lambda a: list_files(**a),
    "get_system_info":lambda a: get_system_info(),
}

def call_tool(name: str, arguments: dict) -> str:
    handler = HANDLERS.get(name)
    if not handler:
        return f"Unknown tool: {name}"
    try:
        return str(handler(arguments))
    except Exception as e:
        return f"Tool error ({name}): {e}"
