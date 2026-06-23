from sqlalchemy import select, func

from src.database.connection import db_manager


class BaseRepository:
    def __init__(self, model_class):
        self.model_class = model_class

    def get_by_id(self, entity_id, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = select(self.model_class).where(
                    self.model_class.id == entity_id
                )
                return session.execute(stmt).scalar_one_or_none()
        else:
            stmt = select(self.model_class).where(
                self.model_class.id == entity_id
            )
            return session.execute(stmt).scalar_one_or_none()

    def list_all(self, order_by=None, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = select(self.model_class)
                if order_by is not None:
                    stmt = stmt.order_by(order_by)
                return session.execute(stmt).scalars().all()
        else:
            stmt = select(self.model_class)
            if order_by is not None:
                stmt = stmt.order_by(order_by)
            return session.execute(stmt).scalars().all()

    def find(self, session=None, **filters):
        if session is None:
            with db_manager.get_session() as session:
                stmt = select(self.model_class).filter_by(**filters)
                return session.execute(stmt).scalars().all()
        else:
            stmt = select(self.model_class).filter_by(**filters)
            return session.execute(stmt).scalars().all()

    def first(self, session=None, **filters):
        if session is None:
            with db_manager.get_session() as session:
                stmt = select(self.model_class).filter_by(**filters)
                return session.execute(stmt).scalar_one_or_none()
        else:
            stmt = select(self.model_class).filter_by(**filters)
            return session.execute(stmt).scalar_one_or_none()

    def count(self, session=None, **filters):
        if session is None:
            with db_manager.get_session() as session:
                stmt = (
                    select(func.count())
                    .select_from(self.model_class)
                    .filter_by(**filters)
                )
                return session.execute(stmt).scalar()
        else:
            stmt = (
                select(func.count())
                .select_from(self.model_class)
                .filter_by(**filters)
            )
            return session.execute(stmt).scalar()

    def exists(self, session=None, **filters):
        if session is None:
            with db_manager.get_session() as session:
                stmt = (
                    select(self.model_class)
                    .filter_by(**filters)
                    .limit(1)
                )
                return session.execute(stmt).scalar_one_or_none() is not None
        else:
            stmt = (
                select(self.model_class)
                .filter_by(**filters)
                .limit(1)
            )
            return session.execute(stmt).scalar_one_or_none() is not None

    def create(self, session, **kwargs):
        instance = self.model_class(**kwargs)
        session.add(instance)
        session.flush()
        return instance

    def update(self, session, entity_id, **kwargs):
        stmt = select(self.model_class).where(
            self.model_class.id == entity_id
        )
        instance = session.execute(stmt).scalar_one_or_none()
        if instance is None:
            return None
        for key, value in kwargs.items():
            setattr(instance, key, value)
        session.flush()
        return instance

    def delete(self, session, entity_id):
        stmt = select(self.model_class).where(
            self.model_class.id == entity_id
        )
        instance = session.execute(stmt).scalar_one_or_none()
        if instance is None:
            return False
        session.delete(instance)
        session.flush()
        return True

    def bulk_create(self, session, items):
        instances = [self.model_class(**item) for item in items]
        session.add_all(instances)
        session.flush()
        return instances
