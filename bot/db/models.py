import sqlalchemy
from sqlalchemy.orm import relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass


class Config(Base):
    __tablename__ = "config"
    _id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    _guildId = sqlalchemy.Column(sqlalchemy.Integer)
    adminRole = sqlalchemy.Column(sqlalchemy.Integer)
    notifChan = sqlalchemy.Column(sqlalchemy.Integer)


class LocalDatabase:
    def __init__(self):
        self.db_name = "discord.db"
        self._engine = sqlalchemy.create_engine(
            f"sqlite:///{self.db_name}?check_same_thread=false", echo=True, future=True
        )
        self._session = sqlalchemy.orm.sessionmaker(bind=self._engine)()

    @property
    def session(self):
        return self._session

    def create_all(self):
        Base.metadata.create_all(self._engine)


g_local_db = LocalDatabase()


def get_local_db():
    return g_local_db
