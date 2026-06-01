import discord
from discord.ext import commands
import os
import database

class WarningTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.notice_channel_id = int(os.getenv("STAFF_NOTICE_CHANNEL_ID", 0))
        self.commands_channel_id = int(os.getenv("STAFF_COMMANDS_CHANNEL_ID", 0))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore bot messages
        if message.author.bot:
            return
            
        # Check if the message is in the staff-notice channel
        if message.channel.id != self.notice_channel_id:
            return
            
        # Check for user mentions
        if not message.mentions:
            return
            
        commands_channel = self.bot.get_channel(self.commands_channel_id)
        
        for user in message.mentions:
            # Ignore if a bot was mentioned
            if user.bot:
                continue
                
            # Add warning to database (saving message content)
            await database.add_warning(user.id, message.channel.id, message.id, message.content)
            
            # Check warning count for the last 3 months
            count = await database.get_warnings_count_last_3_months(user.id)
            
            # If 3 or more warnings, notify the staff commands channel
            if count >= 3 and commands_channel:
                last_warnings = await database.get_last_3_warnings(user.id)
                # Reverse so that the most recent warning is at the bottom of the list
                last_warnings.reverse()
                
                formatted_warnings = []
                for content, warned_at in last_warnings:
                    try:
                        from datetime import datetime, timezone
                        # Parse SQLite YYYY-MM-DD HH:MM:SS format
                        dt = datetime.strptime(warned_at, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
                        ts = int(dt.timestamp())
                        time_str = f"<t:{ts}:f>"
                    except Exception:
                        time_str = "Unknown Date"
                    
                    formatted_warnings.append(f"> - ({time_str}) {content}")
                
                warnings_str = "\n".join(formatted_warnings)
                await commands_channel.send(
                    f"{message.author.mention}, user {user.mention} has accumulated {count} verbal warning within 3 months. Please take immediate action.\n{warnings_str}"
                )

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def sync_warnings(self, ctx):
        notice_channel = self.bot.get_channel(self.notice_channel_id)
        if not notice_channel:
            await ctx.send("Error: Could not access the staff notice channel. Please verify the ID.")
            return

        status_msg = await ctx.send("Starting warning history sync (last 3 months)... This may take a moment.")
        
        imported_count = 0
        from datetime import timezone, datetime, timedelta
        
        # Fetch message history of the staff-notice channel from the last 3 months (90 days)
        three_months_ago = datetime.now(timezone.utc) - timedelta(days=90)
        async for message in notice_channel.history(limit=None, after=three_months_ago, oldest_first=True):
            if message.author.bot:
                continue
            if not message.mentions:
                continue
                
            warned_at_str = message.created_at.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            
            for user in message.mentions:
                if user.bot:
                    continue
                    
                # Check if already imported
                exists = await database.warning_exists(message.id, user.id)
                if not exists:
                    await database.add_warning(
                        user.id, 
                        message.channel.id, 
                        message.id, 
                        message.content, 
                        warned_at=warned_at_str
                    )
                    imported_count += 1

        await status_msg.edit(content=f"Sync complete! Imported {imported_count} historical warnings into the database.")

async def setup(bot):
    await bot.add_cog(WarningTracker(bot))
