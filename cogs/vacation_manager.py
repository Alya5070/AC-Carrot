import discord
from discord.ext import commands
from discord import app_commands
import database
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class VacationManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def start_vacation(self, guild: discord.Guild, member: discord.Member, reason: str = None) -> str:
        """Starts a staff member's vacation: saves roles, strips staff roles on both servers, adds Vacation role on Server 1."""
        # Check if user is already on vacation
        existing = await database.get_vacation_record(member.id, guild.id)
        if existing:
            raise ValueError("This staff member is already on vacation!")

        config = await database.get_guild_config(guild.id)
        vacation_role_id = config.get("vacation_role_id") or 0
        vacation_role_id_2 = config.get("vacation_role_id_2") or 0
        secondary_guild_id = config.get("vacation_secondary_guild_id") or 0
        
        # Parse roles to strip
        strip_roles_1 = []
        if config.get("vacation_strip_roles_1"):
            try:
                strip_roles_1 = [int(r.strip()) for r in config["vacation_strip_roles_1"].split(",") if r.strip()]
            except ValueError:
                pass
                
        strip_roles_2 = []
        if config.get("vacation_strip_roles_2"):
            try:
                strip_roles_2 = [int(r.strip()) for r in config["vacation_strip_roles_2"].split(",") if r.strip()]
            except ValueError:
                pass

        # 1. Strip roles on Server 1
        stripped_1 = []
        member_roles_1_ids = [r.id for r in member.roles]
        for rid in strip_roles_1:
            if rid in member_roles_1_ids:
                stripped_1.append(rid)
        
        roles_to_remove_1 = [guild.get_role(rid) for rid in stripped_1 if guild.get_role(rid)]
        if roles_to_remove_1:
            await member.remove_roles(*roles_to_remove_1, reason="Starting Vacation (Server 1)")

        # Assign Vacation role on Server 1
        vacation_role = guild.get_role(vacation_role_id)
        if vacation_role:
            await member.add_roles(vacation_role, reason="Starting Vacation")

        # 2. Strip roles on Server 2 (secondary guild)
        stripped_2 = []
        secondary_guild = None
        if secondary_guild_id:
            try:
                secondary_guild = self.bot.get_guild(secondary_guild_id)
                if not secondary_guild:
                    secondary_guild = await self.bot.fetch_guild(secondary_guild_id)
            except Exception as e:
                logger.error(f"Failed to fetch secondary guild {secondary_guild_id}: {e}")

        if secondary_guild:
            try:
                sec_member = await secondary_guild.fetch_member(member.id)
                if sec_member:
                    member_roles_2_ids = [r.id for r in sec_member.roles]
                    for rid in strip_roles_2:
                        if rid in member_roles_2_ids:
                            stripped_2.append(rid)
                    
                    roles_to_remove_2 = [secondary_guild.get_role(rid) for rid in stripped_2 if secondary_guild.get_role(rid)]
                    if roles_to_remove_2:
                        await sec_member.remove_roles(*roles_to_remove_2, reason="Starting Vacation (Server 2)")
                    
                    # Assign Vacation role on Server 2
                    vacation_role_2 = secondary_guild.get_role(vacation_role_id_2)
                    if vacation_role_2:
                        await sec_member.add_roles(vacation_role_2, reason="Starting Vacation (Server 2)")
            except Exception as e:
                logger.error(f"Failed to process roles on secondary guild for user {member.id}: {e}")

        # Save to database
        roles_server_1_str = ",".join(map(str, stripped_1))
        roles_server_2_str = ",".join(map(str, stripped_2))
        await database.add_vacation_record(member.id, guild.id, roles_server_1_str, roles_server_2_str, reason)



        return f"Successfully put {member.mention} on vacation."

    async def end_vacation(self, guild: discord.Guild, member: discord.Member) -> str:
        """Ends a staff member's vacation: restores saved roles, removes Vacation role on Server 1."""
        record = await database.get_vacation_record(member.id, guild.id)
        if not record:
            raise ValueError("This staff member is not currently on vacation!")

        config = await database.get_guild_config(guild.id)
        vacation_role_id = config.get("vacation_role_id") or 0
        vacation_role_id_2 = config.get("vacation_role_id_2") or 0
        secondary_guild_id = config.get("vacation_secondary_guild_id") or 0

        # Parse saved roles
        roles_1_ids = []
        if record.get("roles_server_1"):
            try:
                roles_1_ids = [int(r.strip()) for r in record["roles_server_1"].split(",") if r.strip()]
            except ValueError:
                pass
                
        roles_2_ids = []
        if record.get("roles_server_2"):
            try:
                roles_2_ids = [int(r.strip()) for r in record["roles_server_2"].split(",") if r.strip()]
            except ValueError:
                pass

        # 1. Restore roles on Server 1
        roles_to_restore_1 = [guild.get_role(rid) for rid in roles_1_ids if guild.get_role(rid)]
        if roles_to_restore_1:
            await member.add_roles(*roles_to_restore_1, reason="Ending Vacation (Server 1)")

        # Remove Vacation role on Server 1
        vacation_role = guild.get_role(vacation_role_id)
        if vacation_role and vacation_role in member.roles:
            await member.remove_roles(vacation_role, reason="Ending Vacation")

        # 2. Restore roles and remove vacation role on Server 2
        secondary_guild = None
        if secondary_guild_id:
            try:
                secondary_guild = self.bot.get_guild(secondary_guild_id)
                if not secondary_guild:
                    secondary_guild = await self.bot.fetch_guild(secondary_guild_id)
            except Exception as e:
                logger.error(f"Failed to fetch secondary guild {secondary_guild_id}: {e}")

        if secondary_guild:
            try:
                sec_member = await secondary_guild.fetch_member(member.id)
                if sec_member:
                    if roles_2_ids:
                        roles_to_restore_2 = [secondary_guild.get_role(rid) for rid in roles_2_ids if secondary_guild.get_role(rid)]
                        if roles_to_restore_2:
                            await sec_member.add_roles(*roles_to_restore_2, reason="Ending Vacation (Server 2)")
                    
                    # Remove Vacation role on Server 2
                    vacation_role_2 = secondary_guild.get_role(vacation_role_id_2)
                    if vacation_role_2 and vacation_role_2 in sec_member.roles:
                        await sec_member.remove_roles(vacation_role_2, reason="Ending Vacation (Server 2)")
            except Exception as e:
                logger.error(f"Failed to process roles restoration on secondary guild for user {member.id}: {e}")

        # Archive into vacation_history
        vacation_start = record.get("vacation_start", "")
        vacation_end = datetime.now(timezone.utc).isoformat()
        reason = record.get("reason", "")
        roles_server_1 = record.get("roles_server_1", "")
        roles_server_2 = record.get("roles_server_2", "")
        
        await database.add_vacation_history_record(
            user_id=member.id,
            guild_id=guild.id,
            username=str(member),
            avatar_url=member.display_avatar.url if member.display_avatar else "",
            vacation_start=vacation_start,
            vacation_end=vacation_end,
            reason=reason,
            roles_server_1=roles_server_1,
            roles_server_2=roles_server_2
        )

        # Delete active database record
        await database.remove_vacation_record(member.id, guild.id)

        return f"Successfully returned {member.mention} from vacation."

    async def _check_permissions(self, ctx: commands.Context) -> bool:
        """Verifies if the command author is Administrator or has Team Leader role."""
        if ctx.author.guild_permissions.administrator:
            return True
            
        config = await database.get_guild_config(ctx.guild.id)
        team_leader_role_id = config.get("team_leader_role_id") or 0
        if team_leader_role_id:
            author_role_ids = [r.id for r in ctx.author.roles]
            if team_leader_role_id in author_role_ids:
                return True
        return False

    @commands.command(name="givevac")
    async def givevac_cmd(self, ctx: commands.Context, target: discord.Member, *, reason: str = None):
        """Puts a staff member on vacation. Usage: !givevac @member [reason]"""
        if not await self._check_permissions(ctx):
            await ctx.send("You do not have permission to use this command (Administrator or Team Leader required).")
            return
            
        try:
            msg = await self.start_vacation(ctx.guild, target, reason)
            await ctx.send(msg)
        except Exception as e:
            logger.error(f"Error in givevac command: {e}")
            await ctx.send(f"Failed to start vacation: {e}")

    @commands.command(name="removevac")
    async def removevac_cmd(self, ctx: commands.Context, target: discord.Member):
        """Restores staff roles and returns a user from vacation. Usage: !removevac @member"""
        if not await self._check_permissions(ctx):
            await ctx.send("You do not have permission to use this command (Administrator or Team Leader required).")
            return
            
        try:
            msg = await self.end_vacation(ctx.guild, target)
            await ctx.send(msg)
        except Exception as e:
            logger.error(f"Error in removevac command: {e}")
            await ctx.send(f"Failed to end vacation: {e}")

    async def _check_permissions_slash(self, interaction: discord.Interaction) -> bool:
        """Verifies if the slash command author is Administrator or has Team Leader role."""
        if interaction.user.guild_permissions.administrator:
            return True
            
        config = await database.get_guild_config(interaction.guild.id)
        team_leader_role_id = config.get("team_leader_role_id") or 0
        if team_leader_role_id:
            author_role_ids = [r.id for r in interaction.user.roles]
            if team_leader_role_id in author_role_ids:
                return True
        return False

    @app_commands.command(name="addvac", description="Put a staff member on vacation")
    @app_commands.describe(target="The staff member to put on vacation", reason="Optional reason for the vacation")
    async def addvac_slash(self, interaction: discord.Interaction, target: discord.Member, reason: str = None):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        if not await self._check_permissions_slash(interaction):
            await interaction.response.send_message("You do not have permission to use this command (Administrator or Team Leader required).", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        try:
            msg = await self.start_vacation(interaction.guild, target, reason)
            await interaction.followup.send(msg)
        except Exception as e:
            logger.error(f"Error in addvac slash command: {e}")
            await interaction.followup.send(f"Failed to start vacation: {e}")

    @app_commands.command(name="removevac", description="Restore staff roles and return a user from vacation")
    @app_commands.describe(target="The staff member returning from vacation")
    async def removevac_slash(self, interaction: discord.Interaction, target: discord.Member):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        if not await self._check_permissions_slash(interaction):
            await interaction.response.send_message("You do not have permission to use this command (Administrator or Team Leader required).", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        try:
            msg = await self.end_vacation(interaction.guild, target)
            await interaction.followup.send(msg)
        except Exception as e:
            logger.error(f"Error in removevac slash command: {e}")
            await interaction.followup.send(f"Failed to end vacation: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(VacationManager(bot))
