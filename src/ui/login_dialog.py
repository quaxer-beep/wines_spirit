from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from src.database.connection import db_manager
from src.database.models import Branch
from src.services.auth_service import AuthService
from src.utils.exceptions import AuthenticationError


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.auth_service = AuthService()
        self._setup_ui()
        self._load_branches()

    def _setup_ui(self):
        self.setWindowTitle("Wines & Spirits POS - Login")
        self.setMinimumWidth(400)
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
                background-color: #F5F6FA;
            }
            QLabel#titleLabel {
                color: #2C3E50;
                font-size: 22px;
                font-weight: bold;
            }
            QLabel#subtitleLabel {
                color: #7F8C8D;
                font-size: 13px;
            }
            QLabel#fieldLabel {
                color: #2C3E50;
                font-size: 13px;
                font-weight: 600;
            }
            QLabel#statusLabel {
                color: #E74C3C;
                font-size: 12px;
            }
            QComboBox, QLineEdit {
                border: 1px solid #D5D8DC;
                border-radius: 6px;
                padding: 10px 14px;
                font-size: 14px;
                background-color: #FFFFFF;
                color: #2C3E50;
                min-height: 20px;
            }
            QComboBox:focus, QLineEdit:focus {
                border-color: #2E86DE;
                background-color: #FFFFFF;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #7F8C8D;
                margin-right: 8px;
            }
            QComboBox:hover, QLineEdit:hover {
                border-color: #AAB7B8;
            }
            QPushButton#loginButton {
                background-color: #2E86DE;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 15px;
                font-weight: bold;
                min-height: 20px;
            }
            QPushButton#loginButton:hover {
                background-color: #2471A3;
            }
            QPushButton#loginButton:pressed {
                background-color: #1B4F72;
            }
            QPushButton#loginButton:disabled {
                background-color: #AAB7B8;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(0)

        title_label = QLabel("Wines & Spirits POS")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        subtitle_label = QLabel("Sign in to your account")
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)

        layout.addSpacing(30)

        branch_label = QLabel("Branch")
        branch_label.setObjectName("fieldLabel")
        layout.addWidget(branch_label)
        layout.addSpacing(4)

        self.branch_combo = QComboBox()
        self.branch_combo.setObjectName("branchCombo")
        self.branch_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        layout.addWidget(self.branch_combo)

        layout.addSpacing(16)

        username_label = QLabel("Username")
        username_label.setObjectName("fieldLabel")
        layout.addWidget(username_label)
        layout.addSpacing(4)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        layout.addWidget(self.username_input)

        layout.addSpacing(16)

        password_label = QLabel("Password")
        password_label.setObjectName("fieldLabel")
        layout.addWidget(password_label)
        layout.addSpacing(4)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.password_input.returnPressed.connect(self._on_login)
        layout.addWidget(self.password_input)

        layout.addSpacing(24)

        self.login_button = QPushButton("Sign In")
        self.login_button.setObjectName("loginButton")
        self.login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.login_button.clicked.connect(self._on_login)
        layout.addWidget(self.login_button)

        layout.addSpacing(16)

        self.status_label = QLabel()
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        layout.addStretch()

    def _load_branches(self):
        try:
            with db_manager.get_session() as session:
                branches = (
                    session.query(Branch)
                    .filter(Branch.is_active == 1)
                    .order_by(Branch.name)
                    .all()
                )
            self.branch_combo.clear()
            for b in branches:
                self.branch_combo.addItem(f"{b.name} ({b.code})", b.code)
            if self.branch_combo.count() > 0:
                self.branch_combo.setCurrentIndex(0)
        except Exception:
            self.status_label.setText("Could not load branches. Check database connection.")

    def _on_login(self):
        branch_code = self.branch_combo.currentData()
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not branch_code:
            self.status_label.setText("No branch selected.")
            return
        if not username:
            self.status_label.setText("Please enter your username.")
            self.username_input.setFocus()
            return
        if not password:
            self.status_label.setText("Please enter your password.")
            self.password_input.setFocus()
            return

        self.login_button.setEnabled(False)
        self.login_button.setText("Signing in...")
        self.status_label.setText("")

        try:
            self.auth_service.login(username, password, branch_code)
            self.accept()
        except AuthenticationError as e:
            self.status_label.setText(str(e))
        except Exception:
            self.status_label.setText("An unexpected error occurred. Please try again.")
        finally:
            self.login_button.setEnabled(True)
            self.login_button.setText("Sign In")
