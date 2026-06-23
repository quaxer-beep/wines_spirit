import sys
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.database.connection import db_manager
from src.database.models import Base, Branch, Category, Inventory, Product, Role, User
from src.utils.helpers import hash_password

sys.modules.setdefault("PyQt6", MagicMock())
sys.modules.setdefault("PyQt6.QtCore", MagicMock())
sys.modules.setdefault("PyQt6.QtWidgets", MagicMock())
sys.modules.setdefault("PyQt6.QtGui", MagicMock())
sys.modules.setdefault("PyQt6.QtPrintSupport", MagicMock())


from sqlalchemy import select





@pytest.fixture(scope="function", autouse=True)
def _setup_test_db():
    engine = create_engine("sqlite:///:memory:", echo=False, future=True)
    db_manager._engine = engine
    db_manager._session_factory = sessionmaker(
        bind=engine, class_=Session, expire_on_commit=False
    )
    Base.metadata.create_all(engine)
    yield
    if db_manager._engine is not None:
        Base.metadata.drop_all(db_manager._engine)
    db_manager._engine = None
    db_manager._session_factory = None


@pytest.fixture
def db_session():
    session = db_manager.session_factory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@pytest.fixture
def sample_role(db_session):
    role = Role(name="Admin", description="Full system access")
    db_session.add(role)
    db_session.commit()
    return role


@pytest.fixture
def sample_branch(db_session):
    branch = Branch(
        name="Main Branch",
        code="MB001",
        location="Nairobi",
        phone="0712345678",
        email="main@example.com",
        is_active=1,
    )
    db_session.add(branch)
    db_session.commit()
    return branch


@pytest.fixture
def sample_user(db_session, sample_branch, sample_role):
    user = User(
        username="testuser",
        password_hash=hash_password("Pass123"),
        full_name="Test User",
        branch_id=sample_branch.id,
        role_id=sample_role.id,
        is_active=1,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_categories(db_session):
    cat1 = Category(name="Wines", description="Red and white wines")
    cat2 = Category(name="Spirits", description="Spirits and liquors")
    db_session.add_all([cat1, cat2])
    db_session.commit()
    return [cat1, cat2]


@pytest.fixture
def sample_products(db_session, sample_categories, sample_branch):
    prod1 = Product(
        name="Red Wine",
        barcode="1001",
        category_id=sample_categories[0].id,
        cost_price=500.0,
        selling_price=800.0,
        unit="btl",
        reorder_level=5,
        is_active=1,
    )
    prod2 = Product(
        name="White Wine",
        barcode="1002",
        category_id=sample_categories[0].id,
        cost_price=400.0,
        selling_price=700.0,
        unit="btl",
        reorder_level=5,
        is_active=1,
    )
    db_session.add_all([prod1, prod2])
    db_session.commit()

    inv1 = Inventory(
        product_id=prod1.id, branch_id=sample_branch.id, quantity_on_hand=50.0
    )
    inv2 = Inventory(
        product_id=prod2.id, branch_id=sample_branch.id, quantity_on_hand=30.0
    )
    db_session.add_all([inv1, inv2])
    db_session.commit()

    return [prod1, prod2]
