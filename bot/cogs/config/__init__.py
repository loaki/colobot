import nextcord
from db.models import Config as ConfigDb, get_local_db
from utils import embed_success, embed_error
from nextcord.ext import commands
from utils.check import check_adminrole


class Config(commands.Cog, name="Config"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="config", guild_ids=[848117137397907466])
    async def config_slash(
        self,
        interaction: nextcord.Interaction,
        option: str = nextcord.SlashOption(
            choices=[i for i in ConfigDb.__dict__.keys() if i[0] != "_"]
        ),
        role: nextcord.Role = None,
        channel: nextcord.TextChannel = None,
    ):
        """A command which setup config.
        Usage:
        ```
        /config option role/channel
        ```
        """
        # check permissions
        print(check_adminrole(interaction.guild, interaction.user))
        if any(
            [
                interaction.user.top_role.permissions.administrator,
                check_adminrole(interaction.guild, interaction.user),
            ]
        ):
            set_opt = None
            if role and "Role" in option:
                set_opt = role
            if channel and "Chan" in option:
                set_opt = channel
            if set_opt:
                db = get_local_db()
                config = (
                    db.session.query(ConfigDb)
                    .filter(ConfigDb._guildId == interaction.guild.id)
                    .first()
                )
                if config is None:
                    config = ConfigDb()
                    config._guildId = interaction.guild.id
                    db.session.add(config)
                if hasattr(config, option):
                    setattr(config, option, set_opt.id)
                    await interaction.response.send_message(
                        embed=embed_success(title="", description=f"✅ {option} set to {set_opt}")
                    )
                db.session.commit()
                return
        await interaction.response.send_message(
            embed=embed_error(title="", description="❌ Invalid arguments")
        )


# This function will be called when this extension is loaded.
# It is necessary to add these functions to the bot.
def setup(bot: commands.Bot):
    bot.add_cog(Config(bot))
