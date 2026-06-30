import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import re
from datetime import datetime, timezone, timedelta
import database

def parse_duration(duration_str: str) -> timedelta:
    # Remove all whitespace to simplify validation
    clean_str = duration_str.replace(" ", "")
    
    # Supported units
    unit_pattern = r"(?:seconds?|sec|s|minutes?|min|m|hours?|hr|h|days?|d|weeks?|wk|w|months?|mo|years?|yr|y)"
    
    # Ensure the entire string strictly consists of digit+unit groups
    if not re.match(rf"^(\d+(?:\.\d+)?{unit_pattern})+$", clean_str, re.IGNORECASE):
        return None
        
    pattern = re.compile(rf"(\d+(?:\.\d+)?)\s*({unit_pattern})", re.IGNORECASE)
    matches = pattern.findall(clean_str)
    if not matches:
        return None
    
    total_seconds = 0.0
    for value_str, unit in matches:
        value = float(value_str)
        unit = unit.lower()
        if unit in ('s', 'sec', 'second', 'seconds'):
            total_seconds += value
        elif unit in ('m', 'min', 'minute', 'minutes'):
            total_seconds += value * 60
        elif unit in ('h', 'hr', 'hour', 'hours'):
            total_seconds += value * 3600
        elif unit in ('d', 'day', 'days'):
            total_seconds += value * 86400
        elif unit in ('w', 'wk', 'week', 'weeks'):
            total_seconds += value * 604800
        elif unit in ('mo', 'month', 'months'):
            total_seconds += value * 2592000
        elif unit in ('y', 'yr', 'year', 'years'):
            total_seconds += value * 31536000
            
    if total_seconds <= 0:
        return None
    return timedelta(seconds=total_seconds)

class Reminders(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_reminders_loop.start()

    def cog_unload(self):
        self.check_reminders_loop.cancel()

    @tasks.loop(seconds=10.0)
    async def check_reminders_loop(self):
        try:
            due = await database.get_due_reminders()
            for reminder in due:
                reminder_id = reminder['id']
                user_id = reminder['user_id']
                about = reminder['about']
                channel_id = reminder['channel_id']
                
                user = self.bot.get_user(user_id)
                if not user:
                    try:
                        user = await self.bot.fetch_user(user_id)
                    except discord.HTTPException:
                        # If we cannot fetch the user, delete the reminder to avoid looping on it
                        await database.delete_reminder(reminder_id)
                        continue
                
                created_at_str = reminder.get('created_at')
                if created_at_str:
                    try:
                        created_dt = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
                        unix_timestamp = int(created_dt.timestamp())
                    except ValueError:
                        unix_timestamp = int(datetime.now(timezone.utc).timestamp())
                else:
                    unix_timestamp = int(datetime.now(timezone.utc).timestamp())

                embed = discord.Embed(
                    title="Reminder",
                    description=f"<t:{unix_timestamp}:R> you asked to be reminded of \"{about}\".",
                    color=discord.Color.blue()
                )

                sent = False
                if channel_id:
                    channel = self.bot.get_channel(channel_id)
                    if not channel:
                        try:
                            channel = await self.bot.fetch_channel(channel_id)
                        except discord.HTTPException:
                            channel = None
                            
                    if channel:
                        try:
                            await channel.send(content=user.mention, embed=embed)
                            sent = True
                        except discord.HTTPException:
                            pass
                            
                # Fallback to DM if channel_id was not set or sending in channel failed
                if not sent:
                    try:
                        await user.send(embed=embed)
                    except discord.HTTPException:
                        pass
                
                # Clean up reminder after processing
                await database.delete_reminder(reminder_id)
        except Exception as e:
            print(f"Error in check_reminders_loop: {e}")

    @check_reminders_loop.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="remindme", description="Set a reminder")
    @app_commands.rename(in_time="in")
    @app_commands.describe(
        about="What you want to be reminded of",
        in_time="Time duration (e.g. 5m, 2h, 1d)",
        where="Channel to ping you in (type 'here' for current, mention a channel, or omit for DM)"
    )
    async def remindme(self, interaction: discord.Interaction, about: str, in_time: str, where: str = None):
        delta = parse_duration(in_time)
        if not delta:
            await interaction.response.send_message(
                "Invalid time format. Please use a format like `10s`, `5m`, `2h`, `1.5h`, `1d`, or `1h 30m`.",
                ephemeral=True
            )
            return

        channel_id = None
        if where:
            where_clean = where.strip()
            if where_clean.lower() == "here":
                if interaction.guild:
                    channel_id = interaction.channel.id
                else:
                    await interaction.response.send_message("You cannot use 'here' in direct messages.", ephemeral=True)
                    return
            else:
                mention_match = re.match(r"<#(\d+)>", where_clean)
                if mention_match:
                    channel_id = int(mention_match.group(1))
                elif where_clean.isdigit():
                    channel_id = int(where_clean)
                else:
                    if interaction.guild:
                        found_channel = discord.utils.get(interaction.guild.channels, name=where_clean)
                        if found_channel:
                            channel_id = found_channel.id
                        else:
                            await interaction.response.send_message(
                                f"Could not find a channel named '{where}'. Please mention it or use a channel ID.",
                                ephemeral=True
                            )
                            return
                    else:
                        await interaction.response.send_message(
                            "Channel names or mentions can only be resolved inside a server.",
                            ephemeral=True
                        )
                        return

        now_utc = datetime.now(timezone.utc)
        remind_at = now_utc + delta
        remind_at_str = remind_at.strftime('%Y-%m-%d %H:%M:%S')

        await database.add_reminder(
            user_id=interaction.user.id,
            about=about,
            remind_at=remind_at_str,
            channel_id=channel_id
        )

        # Generate a human readable confirmation message
        if channel_id:
            dest = f"<#{channel_id}>"
        else:
            dest = "your DMs"

        # Format remaining time nicely
        total_seconds = int(delta.total_seconds())
        parts = []
        if total_seconds >= 604800:
            weeks = total_seconds // 604800
            parts.append(f"{weeks}w")
            total_seconds %= 604800
        if total_seconds >= 86400:
            days = total_seconds // 86400
            parts.append(f"{days}d")
            total_seconds %= 86400
        if total_seconds >= 3600:
            hours = total_seconds // 3600
            parts.append(f"{hours}h")
            total_seconds %= 3600
        if total_seconds >= 60:
            minutes = total_seconds // 60
            parts.append(f"{minutes}m")
            total_seconds %= 60
        if total_seconds > 0 or not parts:
            parts.append(f"{total_seconds}s")
            
        duration_desc = " ".join(parts)

        await interaction.response.send_message(
            f"I will remind you about \"{about}\" in {duration_desc} ({dest}).",
            ephemeral=True
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(Reminders(bot))
