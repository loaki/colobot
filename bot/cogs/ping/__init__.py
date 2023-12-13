import nextcord
from nextcord.ext import commands
from utils import embed_success


class Ping(commands.Cog, name="Ping"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="ping", guild_ids=[848117137397907466])
    async def ping(self, interaction: nextcord.Interaction):
        """A command which simply acknowledges the user's ping.
        Usage:
        ```
        /ping
        ```
        """
        # respond to the message
        await interaction.response.send_message(
            embed=embed_success(title="", description=f"✅ Pong! {int(self.bot.latency * 1000)} ms")
        )


# This function will be called when this extension is loaded.
# It is necessary to add these functions to the bot.
def setup(bot: commands.Bot):
    bot.add_cog(Ping(bot))
