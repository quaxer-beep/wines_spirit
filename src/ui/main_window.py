from datetime import datetime

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


class _SidebarButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(48)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #BDC3C7;
                border: none;
                border-radius: 6px;
                padding: 12px 20px;
                font-size: 14px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #34495E;
                color: #FFFFFF;
            }
            QPushButton:checked {
                background-color: #34495E;
                color: #FFFFFF;
                font-weight: bold;
            }
        """)


class MainWindow(QMainWindow):
    def __init__(
        self,
        auth_service,
        pos_service,
        inventory_service,
        reporting_service,
        sync_service,
    ):
        super().__init__()
        self.auth_service = auth_service
        self.pos_service = pos_service
        self.inventory_service = inventory_service
        self.reporting_service = reporting_service
        self.sync_service = sync_service

        self._nav_buttons = []
        self._screen_widgets = []

        self._setup_ui()
        self._connect_signals()
        self.update_user_info()
        self.setup_navigation_permissions()

    def _setup_ui(self):
        branch_name = self.auth_service.current_branch.name if self.auth_service.current_branch else "POS"
        self.setWindowTitle(f"Wines & Spirits POS - {branch_name}")
        self.showMaximized()

        self.setStyleSheet("""
            QMainWindow {
                background-color: #ECF0F1;
            }
            QWidget#sidebar {
                background-color: #2C3E50;
            }
            QWidget#topBar {
                background-color: #FFFFFF;
                border-bottom: 1px solid #D5D8DC;
            }
            QWidget#contentArea {
                background-color: #ECF0F1;
            }
            QLabel#appTitle {
                color: #ECF0F1;
                font-size: 16px;
                font-weight: bold;
            }
            QLabel#userName {
                color: #FFFFFF;
                font-size: 13px;
                font-weight: 600;
            }
            QLabel#branchName {
                color: #BDC3C7;
                font-size: 11px;
            }
            QLabel#topBarTitle {
                color: #2C3E50;
                font-size: 18px;
                font-weight: bold;
            }
            QLabel#topBarDateTime {
                color: #7F8C8D;
                font-size: 12px;
            }
            QLabel#syncStatus {
                color: #27AE60;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton#logoutButton {
                background-color: #E74C3C;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
                min-height: 16px;
            }
            QPushButton#logoutButton:hover {
                background-color: #C0392B;
            }
            QPushButton#logoutButton:pressed {
                background-color: #A93226;
            }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        top_bar = self._build_top_bar()
        main_layout.addWidget(top_bar)

        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        sidebar = self._build_sidebar()
        body_layout.addWidget(sidebar)

        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("contentArea")
        body_layout.addWidget(self.content_stack, 1)

        main_layout.addLayout(body_layout, 1)

    def _build_top_bar(self):
        widget = QWidget()
        widget.setObjectName("topBar")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(20, 8, 20, 8)

        title_label = QLabel("Wines & Spirits POS")
        title_label.setObjectName("topBarTitle")
        layout.addWidget(title_label)

        layout.addStretch()

        self.datetime_label = QLabel()
        self.datetime_label.setObjectName("topBarDateTime")
        layout.addWidget(self.datetime_label)

        layout.addSpacing(16)

        self.sync_label = QLabel("Sync: Idle")
        self.sync_label.setObjectName("syncStatus")
        layout.addWidget(self.sync_label)

        self._datetime_timer = QTimer(self)
        self._datetime_timer.timeout.connect(self._update_datetime)
        self._datetime_timer.start(30000)
        self._update_datetime()

        return widget

    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(200)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(10, 16, 10, 12)
        layout.setSpacing(4)

        logo_label = QLabel("W&S POS")
        logo_label.setObjectName("appTitle")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)
        layout.addSpacing(20)

        self._add_nav_button(layout, "POS", 0)
        self._add_nav_button(layout, "Inventory", 1)
        self._add_nav_button(layout, "Reports", 2)
        self._add_nav_button(layout, "Expenses", 3)
        self._add_nav_button(layout, "Settings / Admin", 4)

        layout.addStretch()

        self.user_name_label = QLabel()
        self.user_name_label.setObjectName("userName")
        self.user_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.user_name_label)

        self.branch_name_label = QLabel()
        self.branch_name_label.setObjectName("branchName")
        self.branch_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.branch_name_label)

        layout.addSpacing(8)

        logout_btn = QPushButton("Logout")
        logout_btn.setObjectName("logoutButton")
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.clicked.connect(self._on_logout)
        layout.addWidget(logout_btn)

        return sidebar

    def _add_nav_button(self, layout, text, index):
        btn = _SidebarButton(text)
        btn.clicked.connect(lambda checked, i=index: self.navigate_to(i))
        layout.addWidget(btn)
        self._nav_buttons.append((btn, index))

    def navigate_to(self, index):
        if index < 0 or index >= len(self._screen_widgets):
            return
        for btn, idx in self._nav_buttons:
            btn.setChecked(idx == index)
        self.content_stack.setCurrentIndex(index)

    def _update_datetime(self):
        now = datetime.now()
        self.datetime_label.setText(now.strftime("%A, %d %B %Y  %I:%M %p"))

    def _connect_signals(self):
        self.sync_service.sync_started.connect(self.on_sync_started)
        self.sync_service.sync_completed.connect(self.on_sync_completed)
        self.sync_service.sync_error.connect(self.on_sync_error)

    def on_sync_started(self):
        self.sync_label.setText("Sync: Running...")
        self.sync_label.setStyleSheet("color: #F39C12; font-size: 12px; font-weight: 600;")

    def on_sync_completed(self, stats):
        self.sync_label.setText("Sync: OK")
        self.sync_label.setStyleSheet("color: #27AE60; font-size: 12px; font-weight: 600;")
        QTimer.singleShot(5000, self._reset_sync_label)

    def on_sync_error(self, message):
        self.sync_label.setText("Sync: Error")
        self.sync_label.setStyleSheet("color: #E74C3C; font-size: 12px; font-weight: 600;")
        QTimer.singleShot(5000, self._reset_sync_label)

    def _reset_sync_label(self):
        self.sync_label.setText("Sync: Idle")
        self.sync_label.setStyleSheet("color: #27AE60; font-size: 12px; font-weight: 600;")

    def register_screen(self, index, widget):
        while len(self._screen_widgets) <= index:
            self._screen_widgets.append(None)
            self.content_stack.addWidget(QWidget())
        existing = self.content_stack.widget(index)
        if existing:
            self.content_stack.removeWidget(existing)
            existing.deleteLater()
        self.content_stack.insertWidget(index, widget)
        self._screen_widgets[index] = widget

    def update_user_info(self):
        user = self.auth_service.current_user
        branch = self.auth_service.current_branch
        if user:
            name = user.full_name or user.username
            self.user_name_label.setText(name)
        if branch:
            self.branch_name_label.setText(branch.name)

    def setup_navigation_permissions(self):
        for btn, index in self._nav_buttons:
            resource_map = {
                0: "pos",
                1: "inventory",
                2: "reports",
                3: "expenses",
                4: "admin",
            }
            resource = resource_map.get(index, "admin")
            has_perm = self.auth_service.has_permission(resource, "read")
            btn.setVisible(has_perm)

    def _on_logout(self):
        self.sync_service.stop()
        self.auth_service.logout()
        self.close()

    def closeEvent(self, event):
        self.sync_service.stop()
        event.accept()
