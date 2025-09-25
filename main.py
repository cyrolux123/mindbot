import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os
import datetime

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Intents (must be enabled in the Dev Portal too!)
intents = discord.Intents.default()
intents.members = True  # needed to DM members
bot = commands.Bot(command_prefix="!", intents=intents)

# Channel where standup summaries will be posted
STANDUP_CHANNEL_ID = 1418133945484181564  # 🔹 replace with your channel ID

# Store responses per member (reset daily)
responses = {}

# ---------------- EVENTS ---------------- #
@bot.event
async def on_ready():
    print(f" Logged in as {bot.user}")
    standup_task.start()


# ---------------- DAILY STANDUP TASK ---------------- #
@tasks.loop(time=datetime.time(hour=10, minute=0))  # 🔹 10:00 AM every day
async def standup_task():
    guild = bot.guilds[0]  # get first server, or use bot.get_guild(ID)
    for member in guild.members:
        if not member.bot:
            try:
                await ask_questions(member)
            except Exception as e:
                print(f" Could not DM {member.name}: {e}")


# ---------------- ASK QUESTIONS IN DM ---------------- #
async def ask_questions(member):
    def check(m):
        return m.author == member and isinstance(m.channel, discord.DMChannel)

    responses[member.id] = {}

    # Q1
    await member.send("What did you work on yesterday?")
    msg1 = await bot.wait_for("message", check=check)
    responses[member.id]["yesterday"] = msg1.content

    # Q2
    await member.send("What are you working on today?")
    msg2 = await bot.wait_for("message", check=check)
    responses[member.id]["today"] = msg2.content

    # Q3
    await member.send("Any blockers or challenges?")
    msg3 = await bot.wait_for("message", check=check)
    responses[member.id]["blockers"] = msg3.content

    await member.send("Thanks! Your standup has been recorded.")

    # Post summary in channel
    await post_summary(member)


# ---------------- POST SUMMARY ---------------- #
async def post_summary(member):
    channel = bot.get_channel(STANDUP_CHANNEL_ID)
    if channel:
        summary = (
            f"Standup from {member.display_name}\n"
            f"📈 Previous work day progress\n{responses[member.id]['yesterday']}\n"
            f"📅 Plans for today\n{responses[member.id]['today']}\n"
            f"🔥 Any blockers?\n{responses[member.id]['blockers']}"
        )
        await channel.send(summary)


# ---------------- MANUAL TRIGGER ---------------- #
@bot.command()
async def standup(ctx):
    """Manually trigger standup for yourself"""
    await ask_questions(ctx.author)


# ---------------- RUN BOT ---------------- #
bot.run(TOKEN)

