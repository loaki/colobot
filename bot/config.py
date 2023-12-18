import os

from dotenv.main import load_dotenv

load_dotenv()

# Discord config
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
RTE_TOKEN = os.getenv("RTE_TOKEN", "")
BOT_PREFIX = "?"
LLM_HOST = "http://localhost:8086/completion"
