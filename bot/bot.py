import os

import config
import nextcord
from nextcord.ext import commands
from nextcord.ext import help_commands
from utils.embedder import embed_error
from db.models import get_local_db, Config


def main():
    # Allows privledged intents for monitoring members joining, roles editing, and role assignments
    # These need to be enabled in the developer portal as well
    intents = nextcord.Intents.default()

    # Required in order to read messages (eg. prefix commands)
    intents.message_content = True

    # To enable the guilds priveleged intent:
    intents.guilds = True

    # To enable the members priveleged intent:
    intents.members = True

    # Set custom status to "Listening to ?help"
    activity = nextcord.Activity(
        type=nextcord.ActivityType.listening, name=f"{config.BOT_PREFIX}help"
    )

    bot = commands.Bot(
        commands.when_mentioned_or(config.BOT_PREFIX),
        intents=intents,
        activity=activity,
        help_command=help_commands.PaginatedHelpCommand(),
    )

    # Init database
    get_local_db().create_all()

    # Get the modules of all cogs whose directory structure is ./cogs/<module_name>
    for folder in os.listdir("cogs"):
        bot.load_extension(f"cogs.{folder}")

    @bot.listen()
    async def on_ready():
        """When Discord is connected"""
        assert bot.user is not None
        print(f"{bot.user.name} has connected to Discord!")

    @bot.event
    async def on_guild_join(guild):
        db = get_local_db()
        config = db.session.query(Config).filter(Config._guildId == guild.id).first()
        if config is None:
            config = Config()
            config._guildId = guild.id
            db.session.add(config)
            db.session.commit()

    @bot.event
    async def on_command_error(ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandNotFound):
            return
        try:
            await ctx.reply(
                embed=embed_error(
                    title=" ", description=f"❌ {error}\n``` ?help {ctx.command.name}```"
                ),
                mention_author=False,
            )
        except:
            pass

    # Run Discord bot
    bot.run(config.DISCORD_TOKEN)


if __name__ == "__main__":
    main()
