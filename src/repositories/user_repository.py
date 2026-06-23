from sqlalchemy import select, or_
from sqlalchemy.orm import joinedload, selectinload

from src.database.connection import db_manager
from src.database.models import Permission, Role, User
from src.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__(User)

    def get_by_username(self, username, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = select(User).where(User.username == username)
                return session.execute(stmt).scalar_one_or_none()
        else:
            stmt = select(User).where(User.username == username)
            return session.execute(stmt).scalar_one_or_none()

    def get_by_role(self, role_id, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = (
                    select(User)
                    .where(User.role_id == role_id)
                    .order_by(User.full_name)
                )
                return session.execute(stmt).scalars().all()
        else:
            stmt = (
                select(User)
                .where(User.role_id == role_id)
                .order_by(User.full_name)
            )
            return session.execute(stmt).scalars().all()

    def get_active_users(self, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = (
                    select(User)
                    .where(User.is_active == 1)
                    .order_by(User.full_name)
                )
                return session.execute(stmt).scalars().all()
        else:
            stmt = (
                select(User)
                .where(User.is_active == 1)
                .order_by(User.full_name)
            )
            return session.execute(stmt).scalars().all()

    def authenticate(self, username, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = (
                    select(User)
                    .options(
                        joinedload(User.role).selectinload(Role.permissions),
                    )
                    .where(User.username == username)
                )
                return session.execute(stmt).scalar_one_or_none()
        else:
            stmt = (
                select(User)
                .options(
                    joinedload(User.role).selectinload(Role.permissions),
                )
                .where(User.username == username)
            )
            return session.execute(stmt).scalar_one_or_none()

    def search_users(self, query, session=None):
        if session is None:
            with db_manager.get_session() as session:
                pattern = f"%{query}%"
                stmt = (
                    select(User)
                    .where(
                        or_(
                            User.username.like(pattern),
                            User.full_name.like(pattern),
                            User.email.like(pattern),
                        )
                    )
                    .order_by(User.full_name)
                )
                return session.execute(stmt).scalars().all()
        else:
            pattern = f"%{query}%"
            stmt = (
                select(User)
                .where(
                    or_(
                        User.username.like(pattern),
                        User.full_name.like(pattern),
                        User.email.like(pattern),
                    )
                )
                .order_by(User.full_name)
            )
            return session.execute(stmt).scalars().all()
