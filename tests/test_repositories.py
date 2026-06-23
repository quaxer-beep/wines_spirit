from src.database.models import User
from src.utils.helpers import hash_password


class TestUserRepository:
    def test_create_and_find(self, db_session, sample_role, sample_branch):
        from src.repositories.user_repository import UserRepository

        repo = UserRepository()
        user = repo.create(
            db_session,
            username="newuser",
            password_hash=hash_password("Pass123"),
            full_name="New User",
            role_id=sample_role.id,
            branch_id=sample_branch.id,
            is_active=1,
        )

        assert user.id is not None
        assert user.username == "newuser"

        found = repo.get_by_username("newuser")
        assert found is not None
        assert found.id == user.id

    def test_get_by_username_not_found(self):
        from src.repositories.user_repository import UserRepository

        repo = UserRepository()
        result = repo.get_by_username("nonexistent")
        assert result is None

    def test_get_active_users(self, db_session, sample_role):
        from src.repositories.user_repository import UserRepository

        active = User(
            username="active_user",
            password_hash="pw",
            full_name="Active User",
            role_id=sample_role.id,
            is_active=1,
        )
        inactive = User(
            username="inactive_user2",
            password_hash="pw",
            full_name="Inactive",
            role_id=sample_role.id,
            is_active=0,
        )
        db_session.add_all([active, inactive])
        db_session.commit()

        repo = UserRepository()
        active_users = repo.get_active_users()
        assert all(u.is_active == 1 for u in active_users)
        assert any(u.username == "active_user" for u in active_users)

    def test_search_users(self, db_session, sample_role, sample_branch):
        from src.repositories.user_repository import UserRepository

        extra = User(
            username="jane_doe",
            password_hash="pw",
            full_name="Jane Doe",
            role_id=sample_role.id,
            branch_id=sample_branch.id,
            is_active=1,
        )
        db_session.add(extra)
        db_session.commit()

        repo = UserRepository()
        results = repo.search_users("jane")
        assert len(results) >= 1
        assert results[0].username == "jane_doe"

    def test_get_by_role(self, db_session, sample_role):
        from src.repositories.user_repository import UserRepository

        u1 = User(
            username="role_user1",
            password_hash="pw",
            full_name="User One",
            role_id=sample_role.id,
            is_active=1,
        )
        db_session.add(u1)
        db_session.commit()

        repo = UserRepository()
        users = repo.get_by_role(sample_role.id)
        assert len(users) >= 1


class TestProductRepository:
    def test_search_by_name(self, db_session, sample_products):
        from src.repositories.product_repository import ProductRepository

        repo = ProductRepository()
        results = repo.search_by_name("Red")
        assert len(results) >= 1
        assert "Red Wine" in [p.name for p in results]

    def test_search_by_name_no_results(self):
        from src.repositories.product_repository import ProductRepository

        repo = ProductRepository()
        results = repo.search_by_name("NonexistentXYZ")
        assert len(results) == 0

    def test_get_by_barcode(self, db_session, sample_products):
        from src.repositories.product_repository import ProductRepository

        repo = ProductRepository()
        product = repo.get_by_barcode("1001")
        assert product is not None
        assert product.name == "Red Wine"

    def test_get_by_category(self, db_session, sample_products, sample_categories):
        from src.repositories.product_repository import ProductRepository

        repo = ProductRepository()
        products = repo.get_by_category(sample_categories[0].id)
        assert len(products) == 2

    def test_get_active_products(self, db_session, sample_products):
        from src.repositories.product_repository import ProductRepository

        repo = ProductRepository()
        active = repo.get_active_products()
        assert all(p.is_active == 1 for p in active)


class TestSaleRepository:
    def test_create_sale(self, db_session, sample_branch, sample_user, sample_products):
        from src.repositories.sale_repository import SaleRepository

        repo = SaleRepository()
        items_data = [
            {"product_id": sample_products[0].id, "quantity": 2, "unit_price": 800, "subtotal": 1600},
            {"product_id": sample_products[1].id, "quantity": 1, "unit_price": 700, "subtotal": 700},
        ]
        payment_data = {
            "method": "CASH",
            "amount": 2300,
            "discount": 0,
            "tax": 0,
        }

        sale = repo.create_sale(
            db_session,
            branch_id=sample_branch.id,
            user_id=sample_user.id,
            items_data=items_data,
            payment_data=payment_data,
        )

        assert sale.id is not None
        assert sale.receipt_number is not None
        assert sale.subtotal == 2300.0
        assert sale.grand_total == 2300.0

    def test_get_sale_with_details(self, db_session, sample_branch, sample_user, sample_products):
        from src.repositories.sale_repository import SaleRepository

        repo = SaleRepository()
        items_data = [
            {"product_id": sample_products[0].id, "quantity": 1, "unit_price": 800, "subtotal": 800},
        ]
        payment_data = {"method": "CASH", "amount": 800, "discount": 0, "tax": 0}

        sale = repo.create_sale(
            db_session, branch_id=sample_branch.id, user_id=sample_user.id,
            items_data=items_data, payment_data=payment_data,
        )

        detailed = repo.get_sale_with_details(sale.id)
        assert detailed is not None
        assert len(detailed.items) == 1

    def test_get_by_branch(self, db_session, sample_branch, sample_user, sample_products):
        from src.repositories.sale_repository import SaleRepository

        repo = SaleRepository()
        items_data = [
            {"product_id": sample_products[0].id, "quantity": 1, "unit_price": 800, "subtotal": 800},
        ]
        payment_data = {"method": "CASH", "amount": 800, "discount": 0, "tax": 0}

        repo.create_sale(
            db_session, branch_id=sample_branch.id, user_id=sample_user.id,
            items_data=items_data, payment_data=payment_data,
        )

        sales = repo.get_by_branch(sample_branch.id)
        assert len(sales) >= 1
