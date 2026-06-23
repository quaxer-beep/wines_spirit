from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QLineEdit,
    QDialog, QFormLayout, QDialogButtonBox, QComboBox,
    QDateEdit, QHeaderView, QMessageBox, QFrame, QGroupBox,
    QTextEdit, QScrollArea, QCheckBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QBrush, QFont

from src.services.auth_service import AuthService
from src.services.sync_service import SyncService
from src.config.settings import settings
from src.utils.exceptions import ValidationError, NotFoundError, AuthorizationError
from src.database.connection import db_manager
from src.database.models import Branch, Role, SyncQueue

PRIMARY = "#2E86DE"
WHITE = "#FFFFFF"
LIGHT_BG = "#F5F6FA"


def _style_table(table):
    table.setAlternatingRowColors(True)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.verticalHeader().setVisible(False)
    table.horizontalHeader().setStretchLastSection(True)
    table.setSortingEnabled(True)
    table.setStyleSheet(
        """
        QTableWidget {
            border: 1px solid #DEE2E6;
            gridline-color: #E9ECEF;
            background-color: white;
            alternate-background-color: #F8F9FA;
        }
        QHeaderView::section {
            background-color: #E9ECEF;
            padding: 6px;
            border: none;
            font-weight: bold;
            font-size: 12px;
        }
        """
    )


def _style_button(btn, color=PRIMARY):
    btn.setStyleSheet(
        f"""
        QPushButton {{
            background-color: {color};
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 13px;
            font-weight: bold;
            min-height: 20px;
        }}
        QPushButton:hover {{
            background-color: #1A6EC1;
        }}
        QPushButton:pressed {{
            background-color: #155A9E;
        }}
        QPushButton:disabled {{
            background-color: #BDC3C7;
        }}
        """
    )


def _style_input():
    return """
        padding: 6px; font-size: 13px; border: 1px solid #CED4DA;
        border-radius: 4px; min-height: 20px;
    """


class ConfigField(QFrame):
    def __init__(self, label, value, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("background-color: white; border: 1px solid #DEE2E6; border-radius: 4px;")
        self.setMinimumHeight(50)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        lbl = QLabel(label)
        lbl.setStyleSheet("font-size: 12px; color: #6C757D; font-weight: bold; border: none; min-width: 140px;")
        layout.addWidget(lbl)

        self.val = QLabel(str(value))
        self.val.setStyleSheet("font-size: 13px; color: #2C3E50; border: none;")
        self.val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.val, 1)

    def set_value(self, value):
        self.val.setText(str(value))


class AddUserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add User")
        self.setMinimumWidth(450)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(8)

        self.txt_username = QLineEdit()
        self.txt_username.setPlaceholderText("Username *")
        self.txt_username.setStyleSheet(_style_input())
        form.addRow("Username:", self.txt_username)

        self.txt_password = QLineEdit()
        self.txt_password.setPlaceholderText("Password * (min 6 chars)")
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password.setStyleSheet(_style_input())
        form.addRow("Password:", self.txt_password)

        self.txt_full_name = QLineEdit()
        self.txt_full_name.setPlaceholderText("Full name *")
        self.txt_full_name.setStyleSheet(_style_input())
        form.addRow("Full Name:", self.txt_full_name)

        self.cmb_role = QComboBox()
        self.cmb_role.setStyleSheet(_style_input())
        self._load_roles()
        form.addRow("Role:", self.cmb_role)

        self.cmb_branch = QComboBox()
        self.cmb_branch.setStyleSheet(_style_input())
        self._load_branches()
        form.addRow("Branch:", self.cmb_branch)

        layout.addLayout(form)
        layout.addSpacing(12)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setStyleSheet(
            """
            QDialog { background-color: white; }
            QLabel { font-size: 13px; }
            QLineEdit:focus, QComboBox:focus {
                border-color: """ + PRIMARY + """ !important;
            }
            """
        )

    def _load_roles(self):
        with db_manager.get_session() as session:
            roles = session.query(Role).order_by(Role.name).all()
            for r in roles:
                self.cmb_role.addItem(r.name, r.id)

    def _load_branches(self):
        self.cmb_branch.addItem("-- None --", None)
        with db_manager.get_session() as session:
            branches = session.query(Branch).filter_by(is_active=1).order_by(Branch.name).all()
            for b in branches:
                self.cmb_branch.addItem(f"{b.name} ({b.code})", b.id)

    def _validate_and_accept(self):
        if not self.txt_username.text().strip():
            QMessageBox.warning(self, "Validation Error", "Username is required.")
            return
        if not self.txt_password.text().strip():
            QMessageBox.warning(self, "Validation Error", "Password is required.")
            return
        if len(self.txt_password.text().strip()) < 6:
            QMessageBox.warning(self, "Validation Error", "Password must be at least 6 characters.")
            return
        if not self.txt_full_name.text().strip():
            QMessageBox.warning(self, "Validation Error", "Full name is required.")
            return
        if self.cmb_role.currentData() is None:
            QMessageBox.warning(self, "Validation Error", "Please select a role.")
            return
        self.accept()

    def get_data(self):
        return {
            "username": self.txt_username.text().strip(),
            "password": self.txt_password.text().strip(),
            "full_name": self.txt_full_name.text().strip(),
            "role_id": self.cmb_role.currentData(),
            "branch_id": self.cmb_branch.currentData(),
        }


class ResetPasswordDialog(QDialog):
    def __init__(self, users, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Reset Password")
        self.setMinimumWidth(400)
        self.setModal(True)
        self.users = users
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(8)

        self.cmb_user = QComboBox()
        self.cmb_user.setStyleSheet(_style_input())
        for u in self.users:
            self.cmb_user.addItem(f"{u['full_name']} (@{u['username']})", u["id"])
        form.addRow("User:", self.cmb_user)

        self.txt_password = QLineEdit()
        self.txt_password.setPlaceholderText("New password * (min 6 chars)")
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password.setStyleSheet(_style_input())
        form.addRow("New Password:", self.txt_password)

        self.txt_confirm = QLineEdit()
        self.txt_confirm.setPlaceholderText("Confirm new password")
        self.txt_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_confirm.setStyleSheet(_style_input())
        form.addRow("Confirm:", self.txt_confirm)

        layout.addLayout(form)
        layout.addSpacing(12)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setStyleSheet(
            """
            QDialog { background-color: white; }
            QLabel { font-size: 13px; }
            QLineEdit:focus, QComboBox:focus {
                border-color: """ + PRIMARY + """ !important;
            }
            """
        )

    def _validate_and_accept(self):
        pwd = self.txt_password.text().strip()
        if not pwd:
            QMessageBox.warning(self, "Validation Error", "Password is required.")
            return
        if len(pwd) < 6:
            QMessageBox.warning(self, "Validation Error", "Password must be at least 6 characters.")
            return
        if pwd != self.txt_confirm.text().strip():
            QMessageBox.warning(self, "Validation Error", "Passwords do not match.")
            return
        self.accept()

    def get_data(self):
        return {
            "user_id": self.cmb_user.currentData(),
            "new_password": self.txt_password.text().strip(),
        }


class AddBranchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Branch")
        self.setMinimumWidth(400)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(8)

        self.txt_code = QLineEdit()
        self.txt_code.setPlaceholderText("Branch code * (e.g. NRB-01)")
        self.txt_code.setStyleSheet(_style_input())
        form.addRow("Code:", self.txt_code)

        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("Branch name *")
        self.txt_name.setStyleSheet(_style_input())
        form.addRow("Name:", self.txt_name)

        self.txt_location = QLineEdit()
        self.txt_location.setPlaceholderText("Location / address")
        self.txt_location.setStyleSheet(_style_input())
        form.addRow("Location:", self.txt_location)

        self.txt_phone = QLineEdit()
        self.txt_phone.setPlaceholderText("Phone number")
        self.txt_phone.setStyleSheet(_style_input())
        form.addRow("Phone:", self.txt_phone)

        layout.addLayout(form)
        layout.addSpacing(12)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setStyleSheet(
            """
            QDialog { background-color: white; }
            QLabel { font-size: 13px; }
            QLineEdit:focus {
                border-color: """ + PRIMARY + """ !important;
            }
            """
        )

    def _validate_and_accept(self):
        if not self.txt_code.text().strip():
            QMessageBox.warning(self, "Validation Error", "Branch code is required.")
            return
        if not self.txt_name.text().strip():
            QMessageBox.warning(self, "Validation Error", "Branch name is required.")
            return
        self.accept()

    def get_data(self):
        return {
            "code": self.txt_code.text().strip().upper(),
            "name": self.txt_name.text().strip(),
            "location": self.txt_location.text().strip(),
            "phone": self.txt_phone.text().strip(),
        }


class MpesaConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure M-Pesa")
        self.setMinimumWidth(500)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(8)

        self.txt_consumer_key = QLineEdit(settings.MPESA_CONSUMER_KEY)
        self.txt_consumer_key.setStyleSheet(_style_input())
        form.addRow("Consumer Key:", self.txt_consumer_key)

        self.txt_consumer_secret = QLineEdit(settings.MPESA_CONSUMER_SECRET)
        self.txt_consumer_secret.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_consumer_secret.setStyleSheet(_style_input())
        form.addRow("Consumer Secret:", self.txt_consumer_secret)

        self.txt_passkey = QLineEdit(settings.MPESA_PASSKEY)
        self.txt_passkey.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_passkey.setStyleSheet(_style_input())
        form.addRow("Passkey:", self.txt_passkey)

        self.txt_shortcode = QLineEdit(settings.MPESA_SHORTCODE)
        self.txt_shortcode.setStyleSheet(_style_input())
        form.addRow("Shortcode:", self.txt_shortcode)

        self.cmb_env = QComboBox()
        self.cmb_env.addItems(["sandbox", "production"])
        self.cmb_env.setCurrentText(settings.MPESA_ENVIRONMENT)
        self.cmb_env.setStyleSheet(_style_input())
        form.addRow("Environment:", self.cmb_env)

        layout.addLayout(form)
        layout.addSpacing(12)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setStyleSheet(
            """
            QDialog { background-color: white; }
            QLabel { font-size: 13px; }
            QLineEdit:focus, QComboBox:focus {
                border-color: """ + PRIMARY + """ !important;
            }
            """
        )

    def get_data(self):
        return {
            "consumer_key": self.txt_consumer_key.text().strip(),
            "consumer_secret": self.txt_consumer_secret.text().strip(),
            "passkey": self.txt_passkey.text().strip(),
            "shortcode": self.txt_shortcode.text().strip(),
            "environment": self.cmb_env.currentText(),
        }


class EtimsConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure eTIMS")
        self.setMinimumWidth(500)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(8)

        self.txt_endpoint = QLineEdit(settings.ETIMS_ENDPOINT)
        self.txt_endpoint.setStyleSheet(_style_input())
        form.addRow("API Endpoint:", self.txt_endpoint)

        self.txt_username = QLineEdit(settings.ETIMS_USERNAME)
        self.txt_username.setStyleSheet(_style_input())
        form.addRow("Username:", self.txt_username)

        self.txt_password = QLineEdit(settings.ETIMS_PASSWORD)
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password.setStyleSheet(_style_input())
        form.addRow("Password:", self.txt_password)

        layout.addLayout(form)
        layout.addSpacing(12)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setStyleSheet(
            """
            QDialog { background-color: white; }
            QLabel { font-size: 13px; }
            QLineEdit:focus {
                border-color: """ + PRIMARY + """ !important;
            }
            """
        )

    def get_data(self):
        return {
            "endpoint": self.txt_endpoint.text().strip(),
            "username": self.txt_username.text().strip(),
            "password": self.txt_password.text().strip(),
        }


class UsersTab(QWidget):
    def __init__(self, auth_service):
        super().__init__()
        self.auth_service = auth_service
        self._build_ui()
        self._load_users()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        top = QHBoxLayout()
        self.btn_add_user = QPushButton("  + Add User")
        _style_button(self.btn_add_user, "#28A745")
        self.btn_add_user.clicked.connect(self._add_user)
        self.btn_add_user.setEnabled(self.auth_service.has_permission("users", "create"))
        top.addWidget(self.btn_add_user)

        self.btn_reset_pwd = QPushButton("  Reset Password")
        _style_button(self.btn_reset_pwd, "#F39C12")
        self.btn_reset_pwd.clicked.connect(self._reset_password)
        self.btn_reset_pwd.setEnabled(self.auth_service.has_permission("users", "update"))
        top.addWidget(self.btn_reset_pwd)

        self.btn_refresh = QPushButton("  Refresh")
        _style_button(self.btn_refresh, "#6C757D")
        self.btn_refresh.clicked.connect(self._load_users)
        top.addWidget(self.btn_refresh)

        top.addStretch()
        layout.addLayout(top)
        layout.addSpacing(8)

        self.table = QTableWidget()
        _style_table(self.table)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Username", "Full Name", "Role", "Branch", "Active"])
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 180)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 150)
        self.table.setColumnWidth(5, 60)
        layout.addWidget(self.table)

    def _load_users(self):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        try:
            users = self.auth_service.get_users()
            current_uid = self.auth_service.current_user.id
            for row, u in enumerate(users):
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(u["id"])))
                self.table.setItem(row, 1, QTableWidgetItem(u["username"]))
                self.table.setItem(row, 2, QTableWidgetItem(u["full_name"]))
                self.table.setItem(row, 3, QTableWidgetItem(u.get("role_name") or ""))
                self.table.setItem(row, 4, QTableWidgetItem(u.get("branch_name") or ""))
                active_item = QTableWidgetItem("Yes" if u.get("is_active") else "No")
                active_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 5, active_item)

                if u["id"] == current_uid:
                    font = QFont()
                    font.setBold(True)
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        if item:
                            item.setFont(font)
                            item.setBackground(QColor(220, 235, 255))
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
        self.table.setSortingEnabled(True)

    def _add_user(self):
        dialog = AddUserDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                self.auth_service.create_user(
                    self.auth_service.current_user,
                    data["username"],
                    data["password"],
                    data["role_id"],
                    data["branch_id"],
                    data["full_name"],
                )
                self._load_users()
                QMessageBox.information(self, "Success", f"User '{data['username']}' created.")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def _reset_password(self):
        try:
            users = self.auth_service.get_users()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return

        dialog = ResetPasswordDialog(users, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                self.auth_service.reset_password(
                    self.auth_service.current_user,
                    data["user_id"],
                    data["new_password"],
                )
                QMessageBox.information(self, "Success", "Password reset successfully.")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))


class BranchesTab(QWidget):
    def __init__(self, auth_service):
        super().__init__()
        self.auth_service = auth_service
        self._build_ui()
        self._load_branches()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        top = QHBoxLayout()
        self.btn_add = QPushButton("  + Add Branch")
        _style_button(self.btn_add, "#28A745")
        self.btn_add.clicked.connect(self._add_branch)
        is_admin = self.auth_service.current_user and self.auth_service.current_user.role and self.auth_service.current_user.role.name == "Admin"
        self.btn_add.setEnabled(is_admin and self.auth_service.has_permission("branches", "create"))
        top.addWidget(self.btn_add)

        self.btn_refresh = QPushButton("  Refresh")
        _style_button(self.btn_refresh, "#6C757D")
        self.btn_refresh.clicked.connect(self._load_branches)
        top.addWidget(self.btn_refresh)

        top.addStretch()
        layout.addLayout(top)
        layout.addSpacing(8)

        self.table = QTableWidget()
        _style_table(self.table)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Code", "Name", "Location", "Phone", "Active"])
        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 200)
        self.table.setColumnWidth(3, 150)
        self.table.setColumnWidth(4, 60)
        layout.addWidget(self.table)

        if not is_admin:
            lbl = QLabel("Branch management is restricted to Admin users.")
            lbl.setStyleSheet("color: #6C757D; font-style: italic; padding: 8px;")
            layout.addWidget(lbl)

    def _load_branches(self):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        try:
            with db_manager.get_session() as session:
                branches = session.query(Branch).order_by(Branch.name).all()
                for row, b in enumerate(branches):
                    self.table.insertRow(row)
                    self.table.setItem(row, 0, QTableWidgetItem(b.code))
                    self.table.setItem(row, 1, QTableWidgetItem(b.name))
                    self.table.setItem(row, 2, QTableWidgetItem(b.location or ""))
                    self.table.setItem(row, 3, QTableWidgetItem(b.phone or ""))
                    item = QTableWidgetItem("Yes" if b.is_active else "No")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table.setItem(row, 4, item)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
        self.table.setSortingEnabled(True)

    def _add_branch(self):
        dialog = AddBranchDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                with db_manager.get_session() as session:
                    branch = Branch(
                        code=data["code"],
                        name=data["name"],
                        location=data["location"],
                        phone=data["phone"],
                        is_active=1,
                    )
                    session.add(branch)
                self._load_branches()
                QMessageBox.information(self, "Success", f"Branch '{data['name']}' created.")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))


class SystemTab(QWidget):
    def __init__(self, auth_service):
        super().__init__()
        self.auth_service = auth_service
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: white;")
        cl = QVBoxLayout(container)
        cl.setSpacing(12)

        general_group = QGroupBox("General")
        general_group.setStyleSheet(
            "QGroupBox { font-weight: bold; font-size: 14px; border: 1px solid #DEE2E6; "
            "border-radius: 6px; margin-top: 10px; padding-top: 20px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; background: white; }"
        )
        gv = QVBoxLayout(general_group)
        gv.setSpacing(4)

        self.app_version = ConfigField("App Version:", settings.APP_VERSION)
        gv.addWidget(self.app_version)

        self.db_location = ConfigField("Database Location:", settings.get_db_path())
        gv.addWidget(self.db_location)

        self.sync_interval = ConfigField("Sync Interval:", f"{settings.SYNC_INTERVAL_SECONDS}s")
        gv.addWidget(self.sync_interval)

        cl.addWidget(general_group)

        mpesa_group = QGroupBox("M-Pesa Configuration")
        mpesa_group.setStyleSheet(general_group.styleSheet())
        mv = QVBoxLayout(mpesa_group)
        mv.setSpacing(4)

        mpesa_status = "Configured" if (settings.MPESA_CONSUMER_KEY and settings.MPESA_CONSUMER_SECRET) else "Not Configured"
        mpesa_color = "#28A745" if mpesa_status == "Configured" else "#DC3545"
        self.mpesa_status = ConfigField("M-Pesa Status:", mpesa_status)
        self.mpesa_status.val.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {mpesa_color}; border: none;")
        mv.addWidget(self.mpesa_status)

        self.mpesa_env = ConfigField("Environment:", settings.MPESA_ENVIRONMENT)
        mv.addWidget(self.mpesa_env)

        self.mpesa_shortcode = ConfigField("Shortcode:", settings.MPESA_SHORTCODE or "--")
        mv.addWidget(self.mpesa_shortcode)

        self.btn_config_mpesa = QPushButton("  Configure M-Pesa")
        _style_button(self.btn_config_mpesa)
        self.btn_config_mpesa.clicked.connect(self._config_mpesa)
        mv.addWidget(self.btn_config_mpesa)

        cl.addWidget(mpesa_group)

        etims_group = QGroupBox("eTIMS Configuration")
        etims_group.setStyleSheet(general_group.styleSheet())
        ev = QVBoxLayout(etims_group)
        ev.setSpacing(4)

        etims_status = "Configured" if settings.ETIMS_ENDPOINT else "Not Configured"
        etims_color = "#28A745" if etims_status == "Configured" else "#DC3545"
        self.etims_status = ConfigField("eTIMS Status:", etims_status)
        self.etims_status.val.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {etims_color}; border: none;")
        ev.addWidget(self.etims_status)

        self.etims_endpoint = ConfigField("Endpoint:", settings.ETIMS_ENDPOINT or "--")
        ev.addWidget(self.etims_endpoint)

        self.btn_config_etims = QPushButton("  Configure eTIMS")
        _style_button(self.btn_config_etims)
        self.btn_config_etims.clicked.connect(self._config_etims)
        ev.addWidget(self.btn_config_etims)

        cl.addWidget(etims_group)
        cl.addStretch()

        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _config_mpesa(self):
        dialog = MpesaConfigDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            settings.MPESA_CONSUMER_KEY = data["consumer_key"]
            settings.MPESA_CONSUMER_SECRET = data["consumer_secret"]
            settings.MPESA_PASSKEY = data["passkey"]
            settings.MPESA_SHORTCODE = data["shortcode"]
            settings.MPESA_ENVIRONMENT = data["environment"]
            self._refresh_mpesa_status()

    def _config_etims(self):
        dialog = EtimsConfigDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            settings.ETIMS_ENDPOINT = data["endpoint"]
            settings.ETIMS_USERNAME = data["username"]
            settings.ETIMS_PASSWORD = data["password"]
            self._refresh_etims_status()

    def _refresh_mpesa_status(self):
        status = "Configured" if (settings.MPESA_CONSUMER_KEY and settings.MPESA_CONSUMER_SECRET) else "Not Configured"
        color = "#28A745" if status == "Configured" else "#DC3545"
        self.mpesa_status.set_value(status)
        self.mpesa_status.val.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {color}; border: none;")
        self.mpesa_env.set_value(settings.MPESA_ENVIRONMENT)
        self.mpesa_shortcode.set_value(settings.MPESA_SHORTCODE or "--")

    def _refresh_etims_status(self):
        status = "Configured" if settings.ETIMS_ENDPOINT else "Not Configured"
        color = "#28A745" if status == "Configured" else "#DC3545"
        self.etims_status.set_value(status)
        self.etims_status.val.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {color}; border: none;")
        self.etims_endpoint.set_value(settings.ETIMS_ENDPOINT or "--")


class SyncStatusTab(QWidget):
    def __init__(self, auth_service):
        super().__init__()
        self.auth_service = auth_service
        self.sync_service = SyncService()
        self._build_ui()
        self._load_sync_status()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        status_group = QGroupBox("Sync Status")
        status_group.setStyleSheet(
            "QGroupBox { font-weight: bold; font-size: 14px; border: 1px solid #DEE2E6; "
            "border-radius: 6px; margin-top: 10px; padding-top: 20px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; background: white; }"
        )
        sv = QHBoxLayout(status_group)
        sv.setSpacing(20)

        self.lbl_pending = QLabel("Pending: --")
        self.lbl_pending.setStyleSheet("font-size: 16px; font-weight: bold; color: #F39C12; padding: 8px;")
        sv.addWidget(self.lbl_pending)

        self.lbl_synced = QLabel("Synced: --")
        self.lbl_synced.setStyleSheet("font-size: 16px; font-weight: bold; color: #28A745; padding: 8px;")
        sv.addWidget(self.lbl_synced)

        self.lbl_failed = QLabel("Failed: --")
        self.lbl_failed.setStyleSheet("font-size: 16px; font-weight: bold; color: #DC3545; padding: 8px;")
        sv.addWidget(self.lbl_failed)

        self.lbl_total = QLabel("Total: --")
        self.lbl_total.setStyleSheet("font-size: 16px; font-weight: bold; color: #2C3E50; padding: 8px;")
        sv.addWidget(self.lbl_total)

        sv.addStretch()

        self.lbl_last_sync = QLabel("Last Sync: N/A")
        self.lbl_last_sync.setStyleSheet("font-size: 13px; color: #6C757D; padding: 8px;")
        sv.addWidget(self.lbl_last_sync)

        layout.addWidget(status_group)
        layout.addSpacing(12)

        actions = QHBoxLayout()
        self.btn_sync_now = QPushButton("  Sync Now")
        _style_button(self.btn_sync_now)
        self.btn_sync_now.clicked.connect(self._sync_now)
        actions.addWidget(self.btn_sync_now)

        self.btn_refresh = QPushButton("  Refresh")
        _style_button(self.btn_refresh, "#6C757D")
        self.btn_refresh.clicked.connect(self._load_sync_status)
        actions.addWidget(self.btn_refresh)

        actions.addStretch()
        layout.addLayout(actions)
        layout.addSpacing(12)

        log_group = QGroupBox("Sync Queue Log")
        log_group.setStyleSheet(status_group.styleSheet())
        lv = QVBoxLayout(log_group)

        self.log_table = QTableWidget()
        _style_table(self.log_table)
        self.log_table.setColumnCount(6)
        self.log_table.setHorizontalHeaderLabels(["ID", "Table", "Record ID", "Action", "Status", "Created At"])
        self.log_table.setColumnWidth(0, 50)
        self.log_table.setColumnWidth(1, 120)
        self.log_table.setColumnWidth(2, 80)
        self.log_table.setColumnWidth(3, 80)
        self.log_table.setColumnWidth(4, 80)
        self.log_table.setColumnWidth(5, 160)
        lv.addWidget(self.log_table)

        layout.addWidget(log_group)

    def _load_sync_status(self):
        try:
            status = self.sync_service.get_sync_status()
            self.lbl_pending.setText(f"Pending: {status.get('pending', 0)}")
            self.lbl_synced.setText(f"Synced: {status.get('synced', 0)}")
            self.lbl_failed.setText(f"Failed: {status.get('failed', 0)}")
            self.lbl_total.setText(f"Total: {status.get('total', 0)}")
        except Exception:
            pass

        try:
            with db_manager.get_session() as session:
                rows = (
                    session.query(SyncQueue)
                    .order_by(SyncQueue.created_at.desc())
                    .limit(100)
                    .all()
                )
                self.log_table.setSortingEnabled(False)
                self.log_table.setRowCount(0)
                for row_idx, r in enumerate(rows):
                    self.log_table.insertRow(row_idx)
                    self.log_table.setItem(row_idx, 0, QTableWidgetItem(str(r.id)))
                    self.log_table.setItem(row_idx, 1, QTableWidgetItem(r.table_name))
                    self.log_table.setItem(row_idx, 2, QTableWidgetItem(str(r.record_id)))
                    self.log_table.setItem(row_idx, 3, QTableWidgetItem(r.action))
                    status_item = QTableWidgetItem(r.status)
                    status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if r.status == "PENDING":
                        status_item.setForeground(QBrush(QColor(243, 156, 18)))
                    elif r.status == "SYNCED":
                        status_item.setForeground(QBrush(QColor(40, 167, 69)))
                    elif r.status == "FAILED":
                        status_item.setForeground(QBrush(QColor(220, 53, 69)))
                    self.log_table.setItem(row_idx, 4, status_item)
                    created = r.created_at
                    if created:
                        created_str = created.strftime("%Y-%m-%d %H:%M:%S") if hasattr(created, "strftime") else str(created)[:19]
                    else:
                        created_str = ""
                    self.log_table.setItem(row_idx, 5, QTableWidgetItem(created_str))
                self.log_table.setSortingEnabled(True)

                if rows:
                    last = rows[0]
                    if last.synced_at:
                        last_str = last.synced_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(last.synced_at, "strftime") else str(last.synced_at)[:19]
                    else:
                        last_str = last.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(last.created_at, "strftime") else str(last.created_at)[:19]
                    self.lbl_last_sync.setText(f"Last Sync: {last_str}")
        except Exception:
            pass

    def _sync_now(self):
        self.btn_sync_now.setEnabled(False)
        self.btn_sync_now.setText("Syncing...")
        try:
            self.sync_service.sync_now()
            QMessageBox.information(self, "Sync", "Sync process triggered.")
        except Exception as e:
            QMessageBox.warning(self, "Sync Error", str(e))
        finally:
            self.btn_sync_now.setText("  Sync Now")
            self.btn_sync_now.setEnabled(True)
        self._load_sync_status()


class AdminScreen(QWidget):
    def __init__(self, auth_service=None, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service or AuthService()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            """
            QTabWidget::pane {
                border: none;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #E9ECEF;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
                border: none;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: """ + PRIMARY + """;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #DEE2E6;
            }
            """
        )

        self.tabs.addTab(UsersTab(self.auth_service), "Users")
        self.tabs.addTab(BranchesTab(self.auth_service), "Branches")
        self.tabs.addTab(SystemTab(self.auth_service), "System")
        self.tabs.addTab(SyncStatusTab(self.auth_service), "Sync Status")

        layout.addWidget(self.tabs)

    def refresh(self):
        idx = self.tabs.currentIndex()
        widget = self.tabs.widget(idx)
        if hasattr(widget, "_load_users"):
            widget._load_users()
        elif hasattr(widget, "_load_branches"):
            widget._load_branches()
        elif hasattr(widget, "_load_sync_status"):
            widget._load_sync_status()
