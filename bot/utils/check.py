import nextcord
from db.models import get_local_db, Config


def check_adminrole(guild: nextcord.Guild, member: nextcord.Member):
    db = get_local_db()
    config = db.session.query(Config).filter(Config._guildId == guild.id).first()
    if config and config.adminRole in member.roles:
        return True
    return False
