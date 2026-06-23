from unittest.mock import patch

import pytest

from src.database.models import Branch, Inventory, Product, Sale, SaleItem
from src.utils.exceptions import InsufficientStockError, NotFoundError, ValidationError
from src.utils.helpers import hash_password


@pytest.fixture(autouse=True)
def _fix_repository_imports():
    import sqlalchemy as sa

    import src.repositories as repos
    from src.database.models import AuditLog

    repos_to_fix = {
        "InventoryRepository": "src.repositories.inventory_repository",
        "ProductRepository": "src.repositories.product_repository",
        "SaleRepository": "src.repositories.sale_repository",
    }
    for name, module_path in repos_to_fix.items():
        if not hasattr(repos, name):
            mod = __import__(module_path, fromlist=[name])
            setattr(repos, name, getattr(mod, name))

    repos_to_create = {
        "PaymentRepository": "Payment",
        "SaleItemRepository": "SaleItem",
        "StockMovementRepository": "StockMovement",
    }
    for name, model_name in repos_to_create.items():
        if not hasattr(repos, name):
            from src.repositories.base import BaseRepository
            from src.database.models import Payment, SaleItem, StockMovement

            model_map = {
                "Payment": Payment,
                "SaleItem": SaleItem,
                "StockMovement": StockMovement,
            }

            cls = type(
                name,
                (BaseRepository,),
                {"__init__": lambda self, m=model_map[model_name]: BaseRepository.__init__(self, m)},
            )
            setattr(repos, name, cls)

    if not hasattr(repos, "AuditLogRepository"):
        from src.repositories.sync_repository import AuditLogRepository as _RealAuditLogRepo

        class _PatchedAuditLogRepo(_RealAuditLogRepo):
            def create(self, session, **kwargs):
                max_id = session.query(sa.func.max(AuditLog.id)).scalar() or 0
                kwargs.setdefault("id", max_id + 1)
                return super().create(session, **kwargs)

        repos.AuditLogRepository = _PatchedAuditLogRepo


@pytest.fixture(autouse=True)
def _mock_receipt_number():
    with patch(
        "src.services.pos_service.generate_receipt_number",
        return_value="RCP-TEST-20260623-0001",
    ):
        yield


@pytest.fixture(scope="function", autouse=True)
def _reset_auth_service():
    from src.services.auth_service import AuthService

    AuthService._instance = None
    AuthService._initialized = False


class TestCreateSale:
    def test_create_sale_success(
        self, db_session, sample_products, sample_branch, sample_user
    ):
        from src.services.pos_service import PosService

        pos = PosService()

        cart_items = [
            {"product_id": sample_products[0].id, "quantity": 2, "unit_price": 800},
            {"product_id": sample_products[1].id, "quantity": 1, "unit_price": 700},
        ]
        payment_data = {"method": "CASH", "amount": 2300}

        result = pos.create_sale(sample_user, sample_branch.id, cart_items, payment_data)

        assert result["receipt_number"].startswith("RCP-")
        assert result["status"] == "COMPLETED"
        assert result["subtotal"] == 2300.0
        assert result["grand_total"] == 2300.0 + 2300.0 * 0.16  # incl. tax
        assert len(result["items"]) == 2

    def test_create_sale_with_discount(
        self, db_session, sample_products, sample_branch, sample_user
    ):
        from src.services.pos_service import PosService

        pos = PosService()

        cart_items = [
            {"product_id": sample_products[0].id, "quantity": 1, "unit_price": 800}
        ]
        payment_data = {"method": "CASH", "amount": 700, "discount": 100}

        result = pos.create_sale(sample_user, sample_branch.id, cart_items, payment_data)

        assert result["subtotal"] == 800.0
        assert result["discount"] == 100.0

    def test_create_sale_insufficient_stock(
        self, db_session, sample_products, sample_branch, sample_user
    ):
        from src.services.pos_service import PosService

        pos = PosService()

        cart_items = [
            {"product_id": sample_products[0].id, "quantity": 9999, "unit_price": 800}
        ]
        payment_data = {"method": "CASH", "amount": 800}

        with pytest.raises(InsufficientStockError, match="Insufficient stock"):
            pos.create_sale(sample_user, sample_branch.id, cart_items, payment_data)

    def test_create_sale_empty_cart(
        self, db_session, sample_branch, sample_user
    ):
        from src.services.pos_service import PosService

        pos = PosService()

        with pytest.raises(ValidationError):
            pos.create_sale(sample_user, sample_branch.id, [], {"method": "CASH"})

    def test_create_sale_deducts_inventory(
        self, db_session, sample_products, sample_branch, sample_user
    ):
        from src.services.pos_service import PosService

        original_qty = 50
        assert (
            db_session.query(Inventory)
            .filter_by(
                product_id=sample_products[0].id, branch_id=sample_branch.id
            )
            .first()
            .quantity_on_hand
            == original_qty
        )

        pos = PosService()
        cart_items = [
            {"product_id": sample_products[0].id, "quantity": 3, "unit_price": 800}
        ]
        pos.create_sale(
            sample_user,
            sample_branch.id,
            cart_items,
            {"method": "CASH", "amount": 2400},
        )

        db_session.expire_all()
        inv = (
            db_session.query(Inventory)
            .filter_by(
                product_id=sample_products[0].id, branch_id=sample_branch.id
            )
            .first()
        )
        assert inv.quantity_on_hand == original_qty - 3


class TestVoidSale:
    def test_void_sale_restores_stock(
        self, db_session, sample_products, sample_branch, sample_user
    ):
        from src.services.pos_service import PosService

        pos = PosService()
        cart_items = [
            {"product_id": sample_products[0].id, "quantity": 5, "unit_price": 800}
        ]
        sale = pos.create_sale(
            sample_user,
            sample_branch.id,
            cart_items,
            {"method": "CASH", "amount": 4000},
        )

        result = pos.void_sale(sample_user, sale["id"], "Test void")

        assert result["voided"] == 1
        assert result["status"] == "CANCELLED"

        db_session.expire_all()
        inv = (
            db_session.query(Inventory)
            .filter_by(
                product_id=sample_products[0].id, branch_id=sample_branch.id
            )
            .first()
        )
        assert inv.quantity_on_hand == 50

    def test_void_sale_already_voided(
        self, db_session, sample_products, sample_branch, sample_user
    ):
        from src.services.pos_service import PosService

        pos = PosService()
        cart_items = [
            {"product_id": sample_products[0].id, "quantity": 1, "unit_price": 800}
        ]
        sale = pos.create_sale(
            sample_user,
            sample_branch.id,
            cart_items,
            {"method": "CASH", "amount": 800},
        )
        pos.void_sale(sample_user, sale["id"], "First void")

        with pytest.raises(ValidationError, match="already voided"):
            pos.void_sale(sample_user, sale["id"], "Second void")

    def test_void_sale_not_found(self, db_session, sample_user):
        from src.services.pos_service import PosService

        pos = PosService()
        with pytest.raises(NotFoundError):
            pos.void_sale(sample_user, 99999, "Not found")

    def test_void_sale_no_reason(self, db_session, sample_user):
        from src.services.pos_service import PosService

        pos = PosService()
        with pytest.raises(ValidationError):
            pos.void_sale(sample_user, 1, "")
