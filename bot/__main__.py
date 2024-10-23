import os
import logging
import threading

from . import config
import nextcord
from nextcord.ext import commands
from nextcord.ext import help_commands
from .db.models import get_local_db, Config
from .app import run_flask, app


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

    # logger
    logger = logging.getLogger("nextcord")
    logger.setLevel(logging.ERROR)
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
    )
    logger.addHandler(handler)

    # Init database
    get_local_db().create_all()

    # Get the modules of all cogs whose directory structure is ./cogs/<module_name>
    for folder in os.listdir("bot/cogs"):
        if not folder.startswith("__"):
            bot.load_extension(f".{folder}", package=f"bot.cogs")

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

    # Set up Flask app
    flask_app = app
    flask_app.config["bot"] = bot
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Run Discord bot
    bot.run(config.DISCORD_TOKEN)


if __name__ == "__main__":
    main()
