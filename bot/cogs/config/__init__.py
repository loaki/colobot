import nextcord

from nextcord.utils import get
from nextcord.ext import commands

from ...utils.check import check_adminrole
from ...db.models import Config as ConfigDb, get_local_db
from ...utils import embed_success, embed_error, build_embed


class Config(commands.Cog, name="Config"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="config")
    async def config(self, interaction: nextcord.Interaction):
        """A command which show config.
        Usage:
        ```
        /config
        ```
        """
        db = get_local_db()
        config = (
            db.session.query(ConfigDb).filter(ConfigDb._guildId == interaction.guild.id).first()
        )
        if config is None:
            config = ConfigDb()
            config._guildId = interaction.guild.id
            db.session.add(config)
            db.session.commit()
        embed = build_embed(title="⚙️ Config", colour=nextcord.Colour.blurple())
        embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon)
        for i in ConfigDb.__dict__.keys():
            if i[0] != "_" and ("Role" in i or "Chan" in i) and hasattr(config, i):
                value = None
                if "Chan" in i and getattr(config, i):
                    value = get(interaction.guild.channels, id=getattr(config, i))
                if "Role" in i and getattr(config, i):
                    value = get(interaction.guild.roles, id=getattr(config, i))
                if value:
                    value = value.mention
                embed.add_field(name=i, value=value or "-")
        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="set_config")
    async def set_config(
        self,
        interaction: nextcord.Interaction,
        option: str = nextcord.SlashOption(
            choices=[
                i for i in ConfigDb.__dict__.keys() if i[0] != "_" and ("Role" in i or "Chan" in i)
            ]
        ),
        role: nextcord.Role = None,
        channel: nextcord.TextChannel = None,
    ):
        """A command which setup config.
        Usage:
        ```
        /set_config option role/channel
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
        set_opt = None
        if role and "Role" in option:
            set_opt = role
        if channel and "Chan" in option:
            set_opt = channel
        if set_opt:
            db = get_local_db()
            config = (
                db.session.query(ConfigDb).filter(ConfigDb._guildId == interaction.guild.id).first()
            )
            if config is None:
                config = ConfigDb()
                config._guildId = interaction.guild.id
                db.session.add(config)
            if hasattr(config, option):
                setattr(config, option, set_opt.id)
                db.session.commit()
                await interaction.response.send_message(
                    embed=embed_success(title="", description=f"✅ {option} set to {set_opt}")
                )
                return
            db.session.commit()
            return
        await interaction.response.send_message(
            embed=embed_error(title="", description="❌ Invalid arguments")
        )

    @nextcord.slash_command(name="unset_config")
    async def unset_config(
        self,
        interaction: nextcord.Interaction,
        option: str = nextcord.SlashOption(
            choices=[
                i for i in ConfigDb.__dict__.keys() if i[0] != "_" and ("Role" in i or "Chan" in i)
            ]
        ),
    ):
        """A command which setup config.
        Usage:
        ```
        /unset_config option
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
        if option:
            db = get_local_db()
            config = (
                db.session.query(ConfigDb).filter(ConfigDb._guildId == interaction.guild.id).first()
            )
            if config is None:
                config = ConfigDb()
                config._guildId = interaction.guild.id
                db.session.add(config)
            if hasattr(config, option):
                setattr(config, option, None)
                db.session.commit()
                await interaction.response.send_message(
                    embed=embed_success(title="", description=f"✅ {option} unset")
                )
                return
            db.session.commit()
            return
        await interaction.response.send_message(
            embed=embed_error(title="", description="❌ Invalid arguments")
        )


# This function will be called when this extension is loaded.
# It is necessary to add these functions to the bot.
def setup(bot: commands.Bot):
    bot.add_cog(Config(bot))
