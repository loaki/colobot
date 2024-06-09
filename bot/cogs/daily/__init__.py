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
        today_color = None
        tomorrow_color = None
        colors = {1:"🔵", 2:"⚪", 3:"🔴"}
        response = requests.get("https://www.api-couleur-tempo.fr/api/jourTempo/today")
        if response.status_code == requests.codes.ok:
            today_color = response.json().get("codeJour")
        response = requests.get("https://www.api-couleur-tempo.fr/api/jourTempo/tomorrow")
        if response.status_code == requests.codes.ok:
            tomorrow_color = response.json().get("codeJour")
        return colors.get(today_color), colors.get(tomorrow_color)

    @tasks.loop(time=[time(hour=9)])
    async def daily(self):
        db = get_local_db()
        configs = db.session.query(Config).all()
        for config in configs:
            guild = self.bot.get_guild(config._guildId)
            if not guild:
                print("no guild found : ", config._guildId)
                continue
            chan = get(guild.text_channels, id=config.dailyChan)
            if not chan:
                print("no chan found : ", config.dailyChan)
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
