from datetime import datetime

import pytest
from sqlalchemy import inspect

from src.database.models import (
    Branch,
    Category,
    Expense,
    Inventory,
    Permission,
    Product,
    Role,
    Sale,
    SaleItem,
    StockMovement,
    User,
)


class TestBranch:
    def test_create_branch(self, db_session):
        branch = Branch(
            name="Test Branch",
            code="TB001",
            location="Mombasa",
            phone="0712345678",
            is_active=1,
        )
        db_session.add(branch)
        db_session.flush()

        assert branch.id is not None
        assert branch.name == "Test Branch"
        assert branch.code == "TB001"
        assert branch.is_active == 1

    def test_branch_unique_code(self, db_session):
        b1 = Branch(name="Branch A", code="BA", is_active=1)
        db_session.add(b1)
        db_session.flush()

        b2 = Branch(name="Branch B", code="BA", is_active=1)
        db_session.add(b2)
        with pytest.raises(Exception):
            db_session.flush()
        db_session.rollback()

    def test_branch_null_name(self, db_session):
        branch = Branch(code="NULLNAME")
        db_session.add(branch)
        with pytest.raises(Exception):
            db_session.flush()
        db_session.rollback()

    def test_branch_relationships(self, db_session, sample_branch):
        assert hasattr(sample_branch, "users")
        assert hasattr(sample_branch, "inventory")
        assert hasattr(sample_branch, "sales")


class TestRole:
    def test_create_role(self, db_session):
        role = Role(name="Manager", description="Branch manager")
        db_session.add(role)
        db_session.flush()

        assert role.id is not None
        assert role.name == "Manager"

    def test_role_unique_name(self, db_session):
        r1 = Role(name="Supervisor")
        db_session.add(r1)
        db_session.flush()

        r2 = Role(name="Supervisor")
        db_session.add(r2)
        with pytest.raises(Exception):
            db_session.flush()
        db_session.rollback()


class TestPermission:
    def test_create_permission(self, db_session, sample_role):
        perm = Permission(
            role_id=sample_role.id,
            resource="products",
            can_create=1,
            can_read=1,
            can_update=0,
            can_delete=0,
        )
        db_session.add(perm)
        db_session.flush()

        assert perm.id is not None
        assert perm.resource == "products"
        assert perm.can_create == 1
        assert perm.can_read == 1

    def test_unique_role_resource(self, db_session, sample_role):
        p1 = Permission(role_id=sample_role.id, resource="inventory")
        db_session.add(p1)
        db_session.flush()

        p2 = Permission(role_id=sample_role.id, resource="inventory")
        db_session.add(p2)
        with pytest.raises(Exception):
            db_session.flush()
        db_session.rollback()


class TestUser:
    def test_create_user(self, db_session, sample_role):
        user = User(
            username="john",
            password_hash="hashed_pw",
            full_name="John Doe",
            role_id=sample_role.id,
            is_active=1,
        )
        db_session.add(user)
        db_session.flush()

        assert user.id is not None
        assert user.username == "john"
        assert user.is_active == 1

    def test_user_unique_username(self, db_session, sample_role):
        u1 = User(username="uniquetest", password_hash="pw", full_name="A", role_id=sample_role.id)
        db_session.add(u1)
        db_session.flush()

        u2 = User(username="uniquetest", password_hash="pw", full_name="B", role_id=sample_role.id)
        db_session.add(u2)
        with pytest.raises(Exception):
            db_session.flush()
        db_session.rollback()

    def test_user_null_fields(self, db_session, sample_role):
        user = User(
            username="required_test",
            password_hash="pw",
            full_name="Required",
            role_id=sample_role.id,
        )
        db_session.add(user)
        db_session.flush()

        assert user.email is None
        assert user.phone is None

    def test_user_branch_relationship(self, db_session, sample_user, sample_branch):
        assert sample_user.branch is not None
        assert sample_user.branch.id == sample_branch.id

    def test_user_role_relationship(self, db_session, sample_user, sample_role):
        assert sample_user.role is not None
        assert sample_user.role.id == sample_role.id


class TestCategory:
    def test_create_category(self, db_session):
        cat = Category(name="Whisky", description="Scotch whisky")
        db_session.add(cat)
        db_session.flush()

        assert cat.id is not None
        assert cat.name == "Whisky"

    def test_category_unique_name(self, db_session):
        cat = Category(name="UniqueCat")
        db_session.add(cat)
        db_session.flush()
        cat2 = Category(name="UniqueCat")
        db_session.add(cat2)
        with pytest.raises(Exception):
            db_session.flush()
        db_session.rollback()


class TestProduct:
    def test_create_product(self, db_session, sample_categories):
        product = Product(
            name="Johnnie Walker Black",
            barcode="JW001",
            category_id=sample_categories[0].id,
            cost_price=1500.0,
            selling_price=2500.0,
            unit="btl",
            reorder_level=10,
            is_active=1,
        )
        db_session.add(product)
        db_session.flush()

        assert product.id is not None
        assert product.name == "Johnnie Walker Black"
        assert product.selling_price == 2500.0

    def test_product_unique_barcode(self, db_session):
        p1 = Product(name="Prod A", barcode="UNIQUE001")
        db_session.add(p1)
        db_session.flush()
        p2 = Product(name="Prod B", barcode="UNIQUE001")
        db_session.add(p2)
        with pytest.raises(Exception):
            db_session.flush()
        db_session.rollback()

    def test_product_category_relationship(self, db_session, sample_products, sample_categories):
        assert sample_products[0].category is not None
        assert sample_products[0].category.id == sample_categories[0].id

    def test_product_negative_price_validation(self, db_session):
        with pytest.raises(ValueError, match="non-negative"):
            product = Product(name="Bad", cost_price=-10, selling_price=10)
            db_session.add(product)
            db_session.flush()


class TestInventory:
    def test_create_inventory(self, db_session, sample_branch):
        product = Product(
            name="Test Vodka", barcode="INV001", cost_price=300, selling_price=500,
            unit="btl", is_active=1,
        )
        db_session.add(product)
        db_session.flush()

        inv = Inventory(
            product_id=product.id,
            branch_id=sample_branch.id,
            quantity_on_hand=100.0,
        )
        db_session.add(inv)
        db_session.flush()

        assert inv.id is not None
        assert inv.quantity_on_hand == 100.0

    def test_unique_product_branch(self, db_session, sample_branch):
        product = Product(
            name="Test Gin", barcode="INV002", cost_price=400, selling_price=600,
            unit="btl", is_active=1,
        )
        db_session.add(product)
        db_session.flush()

        i1 = Inventory(
            product_id=product.id,
            branch_id=sample_branch.id,
            quantity_on_hand=10,
        )
        db_session.add(i1)
        db_session.flush()

        i2 = Inventory(
            product_id=product.id,
            branch_id=sample_branch.id,
            quantity_on_hand=20,
        )
        db_session.add(i2)
        with pytest.raises(Exception):
            db_session.flush()
        db_session.rollback()

    def test_inventory_branch_product_relationships(
        self, db_session, sample_branch
    ):
        product = Product(
            name="Test Rum", barcode="INV003", cost_price=500, selling_price=800,
            unit="btl", is_active=1,
        )
        db_session.add(product)
        db_session.flush()

        inv = Inventory(
            product_id=product.id,
            branch_id=sample_branch.id,
            quantity_on_hand=10,
        )
        db_session.add(inv)
        db_session.flush()

        assert inv.product is not None
        assert inv.product.id == product.id
        assert inv.branch is not None
        assert inv.branch.id == sample_branch.id


class TestTimestampMixin:
    def test_created_at_and_updated_at_set(self, db_session):
        branch = Branch(name="TS Test", code="TST", is_active=1)
        db_session.add(branch)
        db_session.flush()

        assert branch.created_at is not None
        assert branch.updated_at is not None
        assert isinstance(branch.created_at, datetime)
        assert isinstance(branch.updated_at, datetime)
