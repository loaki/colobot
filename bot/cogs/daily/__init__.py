import nextcord
from db.models import Config, get_local_db
from utils import build_embed
from nextcord.ext import commands, tasks
from nextcord.utils import get
from datetime import datetime, time, date


class Daily(commands.Cog, name="Daily"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.daily.start()

    def cog_unload(self):
        self.daily.cancel()

    @tasks.loop(time=[time(hour=9)])
    async def daily(self):
        print(datetime.now())
        db = get_local_db()
        configs = db.session.query(Config).all()
        for config in configs:
            guild = self.bot.get_guild(config._guildId)
            chan = get(guild.text_channels, id=config.notifChan)
            if not chan:
                continue
            embed = build_embed(title=f"🗞️ Daily", colour=nextcord.Colour.orange())
            embed.set_author(name=guild.name, icon_url=guild.icon)
            today = date.today()
            embed.add_field(
                name="Date", value=f"{str(today)} - Week {today.isocalendar()[1] % 5}", inline=False
            )
            embed.add_field(name="Tempo", value=f"Today : ⚪\nTomorrow : 🔴", inline=False)
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
