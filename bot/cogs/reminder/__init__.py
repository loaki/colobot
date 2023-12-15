import nextcord
from db.models import Reminder as ReminderDb, get_local_db
from utils import embed_success, embed_error
from nextcord.ext import commands
from utils.check import check_adminrole
from datetime import datetime
from dateutil import relativedelta
from typing import Optional


class Reminder(commands.Cog, name="Reminder"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="add_reminder", guild_ids=[848117137397907466])
    async def add_reminder(
        self,
        interaction: nextcord.Interaction,
        name: str,
        start_hour: Optional[int] = 10,
        start_day: Optional[int] = int(datetime.now().day),
        start_week_day: Optional[int] = nextcord.SlashOption(
            choices={"Monday":0,"Tuesday":1,"Wednesday":2,"Thursday":3,"Friday":4,"Saturday":5,"Sunday":6},
            required=False
        ),
        start_month: Optional[int] = int(datetime.now().month),
        start_year: Optional[int] = int(datetime.now().year),
        repeat: Optional[str] = nextcord.SlashOption(
            choices=["Day","Week","2Week","Month","Year"],
            required=False
        ),
        message: Optional[str] = None,
        prompt: Optional[str] = None,
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
            startDate = datetime.strptime(f"{start_hour}-{start_day}-{start_month}-{start_year}", "%H-%d-%m-%Y")
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
        reminder.name = name
        reminder.message = message
        reminder.prompt = prompt
        reminder.repeat = repeat
        reminder.startDate = startDate
        reminder.nextDate = nextDate
        db.session.add(reminder)
        db.session.commit()
        await interaction.response.send_message(
            embed=embed_success(title="", description=f"✅ reminder {name} saved")
                )
        return


# This function will be called when this extension is loaded.
# It is necessary to add these functions to the bot.
def setup(bot: commands.Bot):
    bot.add_cog(Reminder(bot))
