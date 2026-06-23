from sqlalchemy import select

from src.database.connection import db_manager
from src.database.models import Branch
from src.repositories.base import BaseRepository


class BranchRepository(BaseRepository):
    def __init__(self):
        super().__init__(Branch)

    def get_by_code(self, code, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = select(Branch).where(Branch.code == code)
                return session.execute(stmt).scalar_one_or_none()
        else:
            stmt = select(Branch).where(Branch.code == code)
            return session.execute(stmt).scalar_one_or_none()

    def get_active(self, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = select(Branch).where(Branch.is_active == 1).order_by(Branch.name)
                return session.execute(stmt).scalars().all()
        else:
            stmt = select(Branch).where(Branch.is_active == 1).order_by(Branch.name)
            return session.execute(stmt).scalars().all()
