import discord, asyncio, os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print("Guilds:")
    for g in client.guilds:
        print(f"Name: {g.name} | ID: {g.id}")
    await client.close()

client.run(os.getenv("DISCORD_TOKEN"))
