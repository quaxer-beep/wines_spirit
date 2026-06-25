from src.database.connection import db_manager
from src.database.models import Config
from src.repositories.base import BaseRepository


class ConfigRepository(BaseRepository):
    def __init__(self):
        super().__init__(Config)

    def get_by_key(self, key, session=None):
        return self.first(session=session, key=key)

    def set_value(self, session, key, value):
        existing = self.get_by_key(key, session=session)
        if existing:
            existing.value = value
            session.flush()
            return existing
        return self.create(session, key=key, value=value)

    def get_value(self, key, session=None, default=None):
        if session is None:
            with db_manager.get_session() as session:
                entry = self.get_by_key(key, session=session)
                return entry.value if entry else default
        else:
            entry = self.get_by_key(key, session=session)
            return entry.value if entry else default
