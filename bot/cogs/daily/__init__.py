import json
import requests
import nextcord
import asyncio
import pytz

from nextcord.utils import get
from dateutil import relativedelta
from nextcord.ext import commands, tasks
from datetime import datetime, time, date

from ... import config
from ...utils import build_embed
from ...utils.llm import llm_call
from ...db.models import Config, get_local_db


class Daily(commands.Cog, name="Daily"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.daily.start()

    def cog_unload(self):
        self.daily.cancel()

    async def send_tempo_notif(self, guild, config):
        chan = get(guild.text_channels, id=config.notifChan)
        if not chan:
            return
        prompt = "ecris un court message drole pour annoncer a la colocation que demain est un jour rouge et qu'il faudra economiser l'electricite"
        loop = asyncio.get_running_loop()
        generated_response = await loop.run_in_executor(None, llm_call, prompt)
        embed = build_embed(
            title=f"🔴 Tempo",
            description=generated_response,
            colour=nextcord.Colour.purple(),
        )
        await chan.send(embed=embed)

    def get_tempo_colors(self):
        colors = {"RED": "🔴", "BLUE": "🔵", "WHITE": "⚪"}
        auth_url = "https://digital.iservices.rte-france.com/token/oauth"
        tempo_url = "https://digital.iservices.rte-france.com/open_api/tempo_like_supply_contract/v1/tempo_like_calendars"
        headers = {"Authorization": f"Basic {config.RTE_TOKEN}"}
        response = requests.get(auth_url, headers=headers)
        if response.status_code == requests.codes.ok:
            r_json = json.loads(response.text)
            headers = {"Authorization": f"Bearer {r_json.get('access_token')}"}
            tz = pytz.timezone("Europe/Paris")
            today = datetime.now(tz)
            offset = today.utcoffset()
            offset_hours = str(int(offset.seconds / 3600)).zfill(2)
            tomorrow = today + relativedelta.relativedelta(days=2)
            data = {
                "start_date": today.strftime(f"%Y-%m-%dT00:00:00+{offset_hours}:00"),
                "end_date": tomorrow.strftime(f"%Y-%m-%dT00:00:00+{offset_hours}:00"),
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
        db = get_local_db()
        configs = db.session.query(Config).all()
        for config in configs:
            guild = self.bot.get_guild(config._guildId)
            if not guild:
                continue
            chan = get(guild.text_channels, id=config.dailyChan)
            if not chan:
                continue
            embed = build_embed(title=f"🗞️ Daily", colour=nextcord.Colour.orange())
            embed.set_author(name=guild.name, icon_url=guild.icon)
            today = date.today()
            embed.add_field(
                name="Date",
                value=str(today),
                inline=False,
            )
            today_color, tomorrow_color = self.get_tempo_colors()
            embed.add_field(
                name="Tempo",
                value=f"Today : {today_color}\nTomorrow : {tomorrow_color}",
                inline=False,
            )
            message = None
            if config.dailyMessage:
                try:
                    message = await chan.fetch_message(config.dailyMessage)
                    await message.edit(embed=embed)
                except:
                    pass
            if not message:
                message = await chan.send(embed=embed)
                config.dailyMessage = message.id
                db.session.commit()
            if tomorrow_color == "🔴":
                await self.send_tempo_notif(guild, config)

    @daily.before_loop
    async def before_reminder(self):
        await self.bot.wait_until_ready()


# This function will be called when this extension is loaded.
# It is necessary to add these functions to the bot.
def setup(bot: commands.Bot):
    bot.add_cog(Daily(bot))
