import asyncio
import nextcord

from typing import Optional
from datetime import datetime, time
from nextcord.utils import get
from dateutil import relativedelta
from nextcord.ext import commands, tasks

from ...utils.llm import llm_call
from ...utils.check import check_adminrole
from ...utils import embed_success, embed_error, build_embed
from ...db.models import Reminder as ReminderDb, Config, get_local_db


class Reminder(commands.Cog, name="Reminder"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.send_reminder.start()

    def cog_unload(self):
        self.send_reminder.cancel()

    @tasks.loop(time=[time(hour=h, minute=0) for h in range(24)])
    async def send_reminder(self):
        now = datetime.now()
        db = get_local_db()
        configs = db.session.query(Config).all()
        for config in configs:
            guild = self.bot.get_guild(config._guildId)
            if not guild:
                continue
            reminders = (
                db.session.query(ReminderDb).filter(ReminderDb._guildId == config._guildId).all()
            )
            for reminder in reminders:
                if reminder.nextDate and reminder.nextDate <= now:
                    chan = get(guild.text_channels, id=reminder.channel or config.notifChan)
                    if not chan:
                        continue
                    generated_response = None
                    if reminder.prompt:
                        loop = asyncio.get_running_loop()
                        generated_response = await loop.run_in_executor(
                            None, llm_call, reminder.prompt
                        )
                    embed = build_embed(
                        title=f"⏰ {reminder.name}",
                        description=generated_response or reminder.message,
                        colour=nextcord.Colour.purple(),
                    )
                    notify = None
                    if reminder.notifyMember:
                        notify = get(guild.members, id=reminder.notifyMember)
                    if reminder.notifyRole:
                        notify = get(guild.roles, id=reminder.notifyRole)
                    if notify:
                        await chan.send(notify.mention)
                    await chan.send(embed=embed)
                    if reminder.repeat:
                        if reminder.repeat == "Day":
                            reminder.nextDate += relativedelta.relativedelta(days=1)
                        if reminder.repeat == "Week":
                            reminder.nextDate += relativedelta.relativedelta(days=7)
                        if reminder.repeat == "2Week":
                            reminder.nextDate += relativedelta.relativedelta(days=14)
                        if reminder.repeat == "Month":
                            reminder.nextDate += relativedelta.relativedelta(months=1)
                        if reminder.repeat == "Year":
                            reminder.nextDate += relativedelta.relativedelta(years=1)
                    else:
                        reminder.nextDate = None
                    db.session.commit()

    @send_reminder.before_loop
    async def before_reminder(self):
        await self.bot.wait_until_ready()

    @nextcord.slash_command(name="reminder")
    async def reminder(self, interaction: nextcord.Interaction):
        """A command which show reminders.
        Usage:
        ```
        /reminder
        ```
        """
        db = get_local_db()
        reminders = (
            db.session.query(ReminderDb).filter(ReminderDb._guildId == interaction.guild.id).all()
        )
        embed = build_embed(title="⏰ Reminder", colour=nextcord.Colour.purple())
        embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
        for reminder in reminders:
            embed.add_field(
                name=reminder.name,
                value=f"{str(reminder.nextDate)} - {reminder.repeat}",
                inline=False,
            )
        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="add_reminder")
    async def add_reminder(
        self,
        interaction: nextcord.Interaction,
        name: str,
        start_hour: Optional[int] = 10,
        start_day: Optional[int] = int(datetime.now().day),
        start_week_day: Optional[int] = nextcord.SlashOption(
            choices={
                "Monday": 0,
                "Tuesday": 1,
                "Wednesday": 2,
                "Thursday": 3,
                "Friday": 4,
                "Saturday": 5,
                "Sunday": 6,
            },
            required=False,
        ),
        start_month: Optional[int] = int(datetime.now().month),
        start_year: Optional[int] = int(datetime.now().year),
        repeat: Optional[str] = nextcord.SlashOption(
            choices=["Day", "Week", "2Week", "Month", "Year"], required=False
        ),
        message: Optional[str] = None,
        prompt: Optional[str] = None,
        notify_member: nextcord.Member = None,
        notify_role: nextcord.Role = None,
        channel: nextcord.TextChannel = None,
    ):
        """A command which save reminder.
        Usage:
        ```
        /reminder date message
        ```
        """
        # check permissions
        if not any(
            [
                interaction.user.top_role.permissions.administrator,
                check_adminrole(interaction.guild, interaction.user),
            ]
        ):
            await interaction.response.send_message(
                embed=embed_error(title="", description="❌ Non, pas envie")
            )
            return

        try:
            startDate = datetime.strptime(
                f"{start_hour}-{start_day}-{start_month}-{start_year}", "%H-%d-%m-%Y"
            )
        except:
            await interaction.response.send_message(
                embed=embed_error(title="", description="❌ Invalid arguments")
            )
            return
        if start_week_day:
            if startDate.weekday() <= start_week_day:
                offset = start_week_day - startDate.weekday()
            else :
                offset = 7 - (startDate.weekday() - start_week_day)
            startDate += relativedelta.relativedelta(days=offset)
        db = get_local_db()
        reminder = ReminderDb()
        reminder._guildId = interaction.guild.id
        reminder._author = interaction.user.id
        reminder.name = name
        reminder.message = message
        reminder.prompt = prompt
        reminder.repeat = repeat
        reminder.startDate = startDate
        reminder.nextDate = startDate
        if notify_member:
            notify_member = notify_member.id
        reminder.notifyMember = notify_member
        if notify_role:
            notify_role = notify_role.id
        reminder.notifyRole = notify_role
        if channel:
            channel = channel.id
        reminder.channel = channel
        db.session.add(reminder)
        db.session.commit()
        await interaction.response.send_message(
            embed=embed_success(title="", description=f"✅ reminder {name} saved")
        )
        return

    @nextcord.slash_command(name="rm_reminder")
    async def rm_reminder(
        self,
        interaction: nextcord.Interaction,
        name: str,
    ):
        """A command which remove reminder.
        Usage:
        ```
        /reminder name
        ```
        """
        # check permissions
        if not any(
            [
                interaction.user.top_role.permissions.administrator,
                check_adminrole(interaction.guild, interaction.user),
            ]
        ):
            await interaction.response.send_message(
                embed=embed_error(title="", description="❌ Non, pas envie")
            )
            return
        db = get_local_db()
        reminder = db.session.query(ReminderDb).filter(ReminderDb.name == name).first()
        if reminder:
            db.session.delete(reminder)
            db.session.commit()
            await interaction.response.send_message(
                embed=embed_success(title="", description=f"✅ reminder {name} removed")
            )
            return
        await interaction.response.send_message(
            embed=embed_error(title="", description=f"❌ reminder {name} not found")
        )


# This function will be called when this extension is loaded.
# It is necessary to add these functions to the bot.
def setup(bot: commands.Bot):
    bot.add_cog(Reminder(bot))
