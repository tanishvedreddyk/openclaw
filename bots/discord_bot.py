"""
OpenClaw Discord Bot
Commands:
  !chat <message>   — one-shot reply
  /chat             — slash command
  Mention bot       — triggers a reply
"""
import os, sys, asyncio, httpx
import discord
from discord.ext import commands
from discord import app_commands

sys.path.insert(0, "/app")
from core.config import cfg

if not cfg.DISCORD_TOKEN:
    print("[discord] DISCORD_TOKEN not set — bot disabled.")
    sys.exit(0)

CORE = cfg.CORE_API_URL

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=cfg.DISCORD_PREFIX, intents=intents)
tree = bot.tree


# ── Helper ─────────────────────────────────────────────────────────────────────
async def ask_openclaw(message: str, session_id: str) -> str:
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(f"{CORE}/api/chat",
                         json={"message": message, "session_id": session_id, "platform": "discord"})
        r.raise_for_status()
        return r.json()["reply"]


def chunk_text(text: str, limit: int = 1900):
    """Split long replies into Discord-safe chunks."""
    parts = []
    while len(text) > limit:
        split = text.rfind('\n', 0, limit)
        if split == -1: split = limit
        parts.append(text[:split])
        text = text[split:].strip()
    parts.append(text)
    return parts


# ── Events ─────────────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    await tree.sync()
    print(f"[discord] Logged in as {bot.user} ({bot.user.id})")
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.listening, name="your questions 🐾"))


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # Reply when mentioned
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        text = message.clean_content.replace(f"@{bot.user.display_name}", "").strip()
        if text:
            async with message.channel.typing():
                reply = await ask_openclaw(text, f"discord-{message.channel.id}")
            for chunk in chunk_text(reply):
                await message.reply(chunk)
            return

    await bot.process_commands(message)


# ── Prefix command ─────────────────────────────────────────────────────────────
@bot.command(name="chat", help="Chat with OpenClaw")
async def prefix_chat(ctx: commands.Context, *, message: str):
    async with ctx.typing():
        reply = await ask_openclaw(message, f"discord-{ctx.channel.id}")
    for chunk in chunk_text(reply):
        await ctx.reply(chunk)


@bot.command(name="reset", help="Reset this channel's conversation")
async def prefix_reset(ctx: commands.Context):
    async with httpx.AsyncClient() as c:
        await c.delete(f"{CORE}/api/chat/discord-{ctx.channel.id}")
    await ctx.reply("🔄 Conversation reset.")


# ── Slash commands ─────────────────────────────────────────────────────────────
@tree.command(name="chat", description="Chat with OpenClaw")
@app_commands.describe(message="Your message")
async def slash_chat(interaction: discord.Interaction, message: str):
    await interaction.response.defer(thinking=True)
    reply = await ask_openclaw(message, f"discord-{interaction.channel_id}")
    for chunk in chunk_text(reply):
        await interaction.followup.send(chunk)


@tree.command(name="reset", description="Reset this channel's conversation")
async def slash_reset(interaction: discord.Interaction):
    async with httpx.AsyncClient() as c:
        await c.delete(f"{CORE}/api/chat/discord-{interaction.channel_id}")
    await interaction.response.send_message("🔄 Conversation reset.", ephemeral=True)


@tree.command(name="help", description="Show OpenClaw capabilities")
async def slash_help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🐾 OpenClaw",
        description="A powerful, unrestricted AI assistant.",
        color=0x7c6af7
    )
    embed.add_field(name="Commands", value="`/chat` `/reset` `/help`\n`!chat` `!reset`\nOr just @mention me!", inline=False)
    embed.add_field(name="Skills", value="🔍 Web Search\n💻 Code Execution\n🐚 Shell Commands\n📁 File Operations\n🖥️ System Info", inline=True)
    embed.set_footer(text="OpenClaw — ghcr.io/tanishvedreddyk/openclaw")
    await interaction.response.send_message(embed=embed, ephemeral=True)


if __name__ == "__main__":
    bot.run(cfg.DISCORD_TOKEN)
