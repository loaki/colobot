import nextcord
from db.models import Reminder as ReminderDb, Config, get_local_db
from utils import embed_success, embed_error, build_embed
from nextcord.ext import commands, tasks
from nextcord.utils import get
from utils.check import check_adminrole
from datetime import datetime
from dateutil import relativedelta
from typing import Optional


class Reminder(commands.Cog, name="Reminder"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.send_reminder.start()

    def cog_unload(self):
        self.send_reminder.cancel()

    @tasks.loop(hours=1)
    async def send_reminder(self):
        now = datetime.now()
        db = get_local_db()
        configs = db.session.query(Config).all()
        for config in configs:
            if not config.notifChan:
                continue
            guild = self.bot.get_guild(config._guildId)
            chan = get(guild.text_channels, id=config.notifChan)
            reminders = (
                db.session.query(ReminderDb).filter(ReminderDb._guildId == config._guildId).all()
            )
            for reminder in reminders:
                if reminder.nextDate <= now:
                    member = get(guild.members, id=reminder._author)
                    embed = build_embed(
                        title=f"⏰ {reminder.name}",
                        description=reminder.message,
                        footer=f"{member.name}",
                        colour=nextcord.Colour.blue(),
                    )
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
                        db.session.commit()

    @send_reminder.before_loop
    async def before_reminder(self):
        await self.bot.wait_until_ready()

    @nextcord.slash_command(name="reminder", guild_ids=[848117137397907466])
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
        embed = build_embed(
            title="⏰ Reminder", footer=f"{interaction.guild.name}", colour=nextcord.Colour.blurple()
        )
        for reminder in reminders:
            embed.add_field(
                name=reminder.name, value=f"{str(reminder.nextDate)} - {reminder.repeat}"
            )
        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="add_reminder", guild_ids=[848117137397907466])
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
        notify: Optional[bool] = False,
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
            offset = 7 - startDate.weekday()
            startDate += relativedelta.relativedelta(days=offset)
        nextDate = startDate
        if repeat:
            if repeat == "Day":
                nextDate += relativedelta.relativedelta(days=1)
            if repeat == "Week":
                nextDate += relativedelta.relativedelta(days=7)
            if repeat == "2Week":
                nextDate += relativedelta.relativedelta(days=14)
            if repeat == "Month":
                nextDate += relativedelta.relativedelta(months=1)
            if repeat == "Year":
                nextDate += relativedelta.relativedelta(years=1)
        db = get_local_db()
        reminder = ReminderDb()
        reminder._guildId = interaction.guild.id
        reminder._author = interaction.user.id
        reminder.name = name
        reminder.message = message
        reminder.prompt = prompt
        reminder.repeat = repeat
        reminder.startDate = startDate
        reminder.nextDate = nextDate
        reminder.notify = notify
        db.session.add(reminder)
        db.session.commit()
        await interaction.response.send_message(
            embed=embed_success(title="", description=f"✅ reminder {name} saved")
        )
        return

    @nextcord.slash_command(name="rm_reminder", guild_ids=[848117137397907466])
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
