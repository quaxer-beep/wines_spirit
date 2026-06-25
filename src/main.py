import logging
import sys
import traceback

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication, QMessageBox

from src.config.logging_config import setup_logging
from src.config.settings import Settings
from src.database.connection import db_manager
from src.database.models import (
    Base,
    Branch,
    Category,
    Inventory,
    Permission,
    Product,
    Role,
    User,
)
from src.services.auth_service import AuthService
from src.services.config_service import ConfigService
from src.services.inventory_service import InventoryService
from src.services.pos_service import PosService
from src.services.reporting_service import ReportingService
from src.services.mpesa_service import MpesaService
from src.services.receipt_service import ReceiptService
from src.services.sync_service import SyncService
from src.ui.admin_screen import AdminScreen
from src.ui.expenses_screen import ExpensesScreen
from src.ui.inventory_screen import InventoryScreen
from src.ui.login_dialog import LoginDialog
from src.ui.main_window import MainWindow
from src.ui.pos_screen import PosScreen
from src.ui.reports_screen import ReportsScreen
from src.utils.helpers import hash_password

logger = logging.getLogger(__name__)


def seed_default_data():
    with db_manager.get_session() as session:
        role_count = session.query(Role).count()
        if role_count > 0:
            logger.info("Data already seeded (%d roles found), skipping.", role_count)
            return

        logger.info("Seeding default data...")

        roles = [
            Role(id=1, name="Admin", description="System administrator with full access"),
            Role(id=2, name="Manager", description="Branch manager"),
            Role(id=3, name="Cashier", description="Cashier / sales operator"),
        ]
        session.add_all(roles)
        session.flush()

        resources = [
            "pos", "inventory", "reports", "expenses",
            "admin", "users", "roles", "branches",
            "products", "categories", "sales",
        ]

        manager_resources = ["pos", "inventory", "reports", "expenses", "products", "sales"]
        cashier_resources = ["pos", "products", "sales"]

        permissions = []
        for resource in resources:
            permissions.append(Permission(role_id=1, resource=resource, can_create=1, can_read=1, can_update=1, can_delete=1))
        for resource in manager_resources:
            permissions.append(Permission(role_id=2, resource=resource, can_create=1, can_read=1, can_update=1, can_delete=1))
        for resource in cashier_resources:
            permissions.append(Permission(role_id=3, resource=resource, can_create=1, can_read=1, can_update=0, can_delete=0))
        session.add_all(permissions)

        branches = [
            Branch(code="NBI", name="Nairobi", location="Nairobi CBD", phone="+254700100200"),
            Branch(code="NVH", name="Naivasha", location="Naivasha Town", phone="+254700100201"),
            Branch(code="NKR", name="Nakuru", location="Nakuru Town", phone="+254700100202"),
        ]
        session.add_all(branches)
        session.flush()

        category_names = [
            "Wines", "Spirits", "Beer", "Soft Drinks", "Whisky",
            "Vodka", "Gin", "Rum", "Liqueur", "Cognac", "Water",
        ]
        categories = [Category(name=name) for name in category_names]
        session.add_all(categories)
        session.flush()

        admin_user = User(
            username="admin",
            password_hash=hash_password("admin123"),
            full_name="System Administrator",
            role_id=1,
            branch_id=branches[0].id,
            is_active=1,
        )
        session.add(admin_user)

        sample_products = [
            ("Wines", "Cabernet Sauvignon", "Robert Mondavi", 1200, 1800, 10),
            ("Spirits", "Smirnoff Vodka 1L", "Smirnoff", 800, 1400, 10),
            ("Beer", "Tusker Lager 500ml", "EABL", 150, 250, 20),
            ("Soft Drinks", "Coca Cola 300ml", "Coca-Cola", 50, 100, 30),
            ("Whisky", "Johnnie Walker Black Label", "Johnnie Walker", 2500, 3800, 5),
            ("Vodka", "Absolut Vodka 750ml", "Absolut", 1500, 2200, 8),
            ("Gin", "Beefeater Gin 1L", "Beefeater", 1800, 2600, 8),
            ("Rum", "Captain Morgan Spiced Gold", "Captain Morgan", 1400, 2000, 8),
            ("Liqueur", "Baileys Irish Cream", "Baileys", 1600, 2400, 6),
            ("Cognac", "Hennessy VS", "Hennessy", 3500, 5000, 4),
            ("Water", "Dasani Still Water 500ml", "Dasani", 40, 80, 40),
        ]

        cat_map = {c.name: c for c in categories}
        products = []
        for cat_name, prod_name, brand, cost, sell, reorder in sample_products:
            product = Product(
                name=prod_name,
                brand=brand,
                category_id=cat_map[cat_name].id,
                cost_price=cost,
                selling_price=sell,
                reorder_level=reorder,
                is_active=1,
            )
            products.append(product)
        session.add_all(products)
        session.flush()

        inventories = []
        for product in products:
            for branch in branches:
                inventories.append(
                    Inventory(
                        product_id=product.id,
                        branch_id=branch.id,
                        quantity_on_hand=50,
                    )
                )
        session.add_all(inventories)

        logger.info("Default data seeded successfully.")


PREMIUM_BG = "#F5F0EB"
PREMIUM_SIDEBAR = "#1B1B2F"
PREMIUM_GOLD = "#C8A45C"
PREMIUM_GOLD_HOVER = "#B8923E"
PREMIUM_GOLD_PRESSED = "#A07E2E"
PREMIUM_DARK = "#2C3E50"
PREMIUM_TEXT = "#3D3D3D"
PREMIUM_MUTED = "#8E8E93"
PREMIUM_BORDER = "#E0D8CF"
PREMIUM_DANGER = "#C0392B"
PREMIUM_WHITE = "#FFFFFF"

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {PREMIUM_BG};
}}
QPushButton {{
    background-color: {PREMIUM_GOLD};
    color: {PREMIUM_WHITE};
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 700;
    min-height: 20px;
}}
QPushButton:hover {{
    background-color: {PREMIUM_GOLD_HOVER};
}}
QPushButton:pressed {{
    background-color: {PREMIUM_GOLD_PRESSED};
}}
QPushButton:disabled {{
    background-color: #D5CBBE;
    color: #F5F0EB;
}}
QLineEdit, QComboBox, QSpinBox, QDateEdit {{
    border: 1.5px solid {PREMIUM_BORDER};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    background-color: {PREMIUM_WHITE};
    color: {PREMIUM_TEXT};
    min-height: 22px;
}}
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDateEdit:disabled {{
    background-color: #F8F6F2;
    color: {PREMIUM_MUTED};
    border: 1.5px solid #EBE5DE;
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus {{
    border-color: {PREMIUM_GOLD};
}}
QLineEdit::placeholder {{
    color: {PREMIUM_MUTED};
}}
QTableWidget {{
    gridline-color: {PREMIUM_BORDER};
    border: 1.5px solid {PREMIUM_BORDER};
    border-radius: 6px;
    background-color: {PREMIUM_WHITE};
    alternate-background-color: #FAF8F5;
}}
QTableWidget::item {{
    padding: 6px 10px;
}}
QHeaderView::section {{
    background-color: {PREMIUM_SIDEBAR};
    color: {PREMIUM_WHITE};
    font-weight: 700;
    padding: 10px 8px;
    border: none;
    font-size: 12px;
    text-transform: uppercase;
}}
QTabWidget::pane {{
    border: 1.5px solid {PREMIUM_BORDER};
    border-radius: 6px;
    background-color: {PREMIUM_WHITE};
}}
QTabBar::tab {{
    background-color: #EDE8E2;
    color: {PREMIUM_TEXT};
    padding: 10px 20px;
    border: 1.5px solid {PREMIUM_BORDER};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
    font-weight: 600;
}}
QTabBar::tab:selected {{
    background-color: {PREMIUM_WHITE};
    color: {PREMIUM_GOLD};
    font-weight: 700;
}}
QTabBar::tab:hover:!selected {{
    background-color: #E0D8CF;
}}
QGroupBox {{
    border: 1.5px solid {PREMIUM_BORDER};
    border-radius: 8px;
    margin-top: 14px;
    padding: 20px 16px 14px 16px;
    font-weight: 700;
    color: {PREMIUM_DARK};
    background-color: {PREMIUM_WHITE};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 8px;
}}
QScrollBar:vertical {{
    background-color: #F5F0EB;
    width: 10px;
    border: none;
    border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background-color: #D5CBBE;
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {PREMIUM_MUTED};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
"""


def _global_excepthook(exc_type, exc_value, exc_tb):
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    crash_path = Settings.BASE_DIR / "crash.log"
    with open(str(crash_path), "w", encoding="utf-8") as f:
        f.write(msg)
    # Also try the Qt message box
    try:
        app = QApplication.instance()
        if app:
            QMessageBox.critical(None, "Crash", f"An error occurred:\n\n{exc_value}\n\nSee crash.log for details.")
    except Exception:
        pass
    sys.__excepthook__(exc_type, exc_value, exc_tb)

sys.excepthook = _global_excepthook


def main():
    try:
        setup_logging()
        logger.info("=" * 60)
        logger.info("%s v%s starting...", Settings.APP_NAME, Settings.APP_VERSION)
        logger.info("=" * 60)

        db_path = Settings.get_db_path()
        db_manager.initialize(db_path)
        Base.metadata.create_all(db_manager.engine)
        logger.info("Database initialized and tables created.")

        seed_default_data()

        ConfigService().load_all_into_settings()

        app = QApplication(sys.argv)
        app.setApplicationName(Settings.APP_NAME)
        app.setApplicationVersion(Settings.APP_VERSION)

        font = QFont("Segoe UI", 10)
        app.setFont(font)

        app.setStyleSheet(STYLESHEET)

        auth_service = AuthService()
        pos_service = PosService()
        inventory_service = InventoryService()
        reporting_service = ReportingService()
        sync_service = SyncService()

        login = LoginDialog()
        if login.exec() == LoginDialog.DialogCode.Accepted:
            main_window = MainWindow(
                auth_service=auth_service,
                pos_service=pos_service,
                inventory_service=inventory_service,
                reporting_service=reporting_service,
                sync_service=sync_service,
            )

            try:
                pos_screen = PosScreen(
                    pos_service=pos_service,
                    auth_service=auth_service,
                    receipt_service=ReceiptService(),
                    mpesa_service=MpesaService(),
                )
                main_window.register_screen(0, pos_screen)
                logger.info("POS screen registered.")

                inventory_screen = InventoryScreen(
                    inventory_service=inventory_service,
                    auth_service=auth_service,
                )
                main_window.register_screen(1, inventory_screen)
                logger.info("Inventory screen registered.")

                reports_screen = ReportsScreen(
                    reporting_service=reporting_service,
                )
                main_window.register_screen(2, reports_screen)
                logger.info("Reports screen registered.")

                expenses_screen = ExpensesScreen(
                    auth_service=auth_service,
                )
                main_window.register_screen(3, expenses_screen)
                logger.info("Expenses screen registered.")

                admin_screen = AdminScreen(
                    auth_service=auth_service,
                )
                main_window.register_screen(4, admin_screen)
                logger.info("Admin screen registered.")
            except Exception as e:
                logger.critical("Failed to register screens: %s", e, exc_info=True)
                QMessageBox.critical(
                    None,
                    "Initialization Error",
                    f"Failed to initialize application screens:\n\n{e}",
                )
                sys.exit(1)

            main_window.show()
            sync_service.start()

            exit_code = app.exec()
            sync_service.stop()
            sys.exit(exit_code)
        else:
            logger.info("Login cancelled by user.")
            sys.exit(0)

    except Exception as e:
        logger.critical("Failed to start application: %s", e, exc_info=True)
        error_app = QApplication(sys.argv)
        QMessageBox.critical(
            None,
            "Application Error",
            f"Failed to start application:\n\n{e}\n\nCheck the logs for details.",
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
