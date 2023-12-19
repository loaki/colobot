import json
import requests
import nextcord

from nextcord.utils import get
from dateutil import relativedelta
from nextcord.ext import commands, tasks
from datetime import datetime, time, date

from ... import config
from ...utils import build_embed
from ...db.models import Config, get_local_db


class Daily(commands.Cog, name="Daily"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.daily.start()

    def cog_unload(self):
        self.daily.cancel()

    def get_tempo_colors(self):
        colors = {"RED": "🔴", "BLUE": "🔵", "WHITE": "⚪"}
        auth_url = "https://digital.iservices.rte-france.com/token/oauth"
        tempo_url = "https://digital.iservices.rte-france.com/open_api/tempo_like_supply_contract/v1/tempo_like_calendars"
        headers = {"Authorization": f"Basic {config.RTE_TOKEN}"}
        response = requests.get(auth_url, headers=headers)
        if response.status_code == requests.codes.ok:
            r_json = json.loads(response.text)
            headers = {"Authorization": f"Bearer {r_json.get('access_token')}"}
            today = date.today()
            tomorrow = today + relativedelta.relativedelta(days=2)
            data = {
                "start_date": today.strftime("%Y-%m-%dT00:00:00+01:00"),
                "end_date": tomorrow.strftime("%Y-%m-%dT00:00:00+01:00"),
            }
            response = requests.get(tempo_url, headers=headers, params=data)
            if response.status_code == requests.codes.ok:
                r_json = json.loads(response.text)
                today_color = r_json["tempo_like_calendars"]["values"][1]["value"]
                tomorrow_color = r_json["tempo_like_calendars"]["values"][0]["value"]
                return colors[today_color], colors[tomorrow_color]
        return None, None

    @tasks.loop(time=[time(hour=9)])
    async def daily(self):
        print(datetime.now())
        db = get_local_db()
        configs = db.session.query(Config).all()
        for config in configs:
            guild = self.bot.get_guild(config._guildId)
            chan = get(guild.text_channels, id=config.dailyChan)
            if not chan:
                continue
            embed = build_embed(title=f"🗞️ Daily", colour=nextcord.Colour.orange())
            embed.set_author(name=guild.name, icon_url=guild.icon)
            today = date.today()
            embed.add_field(
                name="Date", value=f"{str(today)} - Week {today.isocalendar()[1] % 5}", inline=False
            )
            today_color, tomorrow_color = self.get_tempo_colors()
            embed.add_field(
                name="Tempo",
                value=f"Today : {today_color}\nTomorrow : {tomorrow_color}",
                inline=False,
            )
            if config.dailyMessage:
                try:
                    message = await chan.fetch_message(config.dailyMessage)
                    await message.edit(embed=embed)
                    return
                except:
                    pass
            message = await chan.send(embed=embed)
            config.dailyMessage = message.id
            db.session.commit()

    @daily.before_loop
    async def before_reminder(self):
        await self.bot.wait_until_ready()


# This function will be called when this extension is loaded.
# It is necessary to add these functions to the bot.
def setup(bot: commands.Bot):
    bot.add_cog(Daily(bot))
