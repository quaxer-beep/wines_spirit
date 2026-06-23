from datetime import date, datetime, timedelta

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QLineEdit,
    QDialog, QFormLayout, QDialogButtonBox, QComboBox,
    QDateEdit, QHeaderView, QMessageBox, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QBrush, QFont

from src.services.auth_service import AuthService
from src.utils.helpers import format_currency
from src.utils.exceptions import ValidationError
from src.repositories.expense_repository import ExpenseRepository
from src.database.connection import db_manager

PRIMARY = "#2E86DE"
WHITE = "#FFFFFF"
LIGHT_BG = "#F5F6FA"

EXPENSE_CATEGORIES = [
    "Rent", "Salaries", "Electricity", "Internet",
    "Fuel", "Supplier", "Miscellaneous"
]

CATEGORY_COLORS = {
    "Rent": "#2E86DE",
    "Salaries": "#28A745",
    "Electricity": "#F39C12",
    "Internet": "#6F42C1",
    "Fuel": "#DC3545",
    "Supplier": "#17A2B8",
    "Miscellaneous": "#6C757D",
}


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


class ExpenseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Record Expense")
        self.setMinimumWidth(450)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(8)

        self.dt_date = QDateEdit()
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDate(QDate.currentDate())
        self.dt_date.setStyleSheet(
            "padding: 6px; font-size: 13px; border: 1px solid #CED4DA; border-radius: 4px;"
        )
        form.addRow("Expense Date:", self.dt_date)

        self.cmb_category = QComboBox()
        self.cmb_category.addItems(EXPENSE_CATEGORIES)
        self.cmb_category.setStyleSheet(
            "padding: 6px; font-size: 13px; border: 1px solid #CED4DA; border-radius: 4px;"
        )
        form.addRow("Category:", self.cmb_category)

        self.txt_description = QLineEdit()
        self.txt_description.setPlaceholderText("Description of the expense *")
        self.txt_description.setStyleSheet(
            "padding: 6px; font-size: 13px; border: 1px solid #CED4DA; border-radius: 4px;"
        )
        form.addRow("Description:", self.txt_description)

        self.txt_amount = QLineEdit()
        self.txt_amount.setPlaceholderText("0.00")
        self.txt_amount.setStyleSheet(
            "padding: 6px; font-size: 13px; border: 1px solid #CED4DA; border-radius: 4px;"
        )
        form.addRow("Amount (KES):", self.txt_amount)

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
        if not self.txt_description.text().strip():
            QMessageBox.warning(self, "Validation Error", "Description is required.")
            self.txt_description.setFocus()
            return
        try:
            amount = float(self.txt_amount.text().strip() or "0")
            if amount <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Please enter a valid positive amount.")
            self.txt_amount.setFocus()
            return
        self.accept()

    def get_data(self):
        return {
            "expense_date": self.dt_date.date().toPyDate(),
            "category": self.cmb_category.currentText(),
            "description": self.txt_description.text().strip(),
            "amount": float(self.txt_amount.text().strip() or "0"),
        }


class CategoryBar(QFrame):
    def __init__(self, category, amount, total, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("background-color: white; border: 1px solid #DEE2E6; border-radius: 6px;")
        self.setMinimumHeight(50)

        color = CATEGORY_COLORS.get(category, "#6C757D")
        pct = (amount / total * 100) if total > 0 else 0

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        lbl_cat = QLabel(category)
        lbl_cat.setStyleSheet("font-size: 13px; font-weight: bold; color: #2C3E50; border: none; min-width: 100px;")
        layout.addWidget(lbl_cat)

        bar_container = QFrame()
        bar_container.setStyleSheet("background-color: #E9ECEF; border-radius: 4px; border: none;")
        bar_container.setFixedHeight(20)

        bar_fill = QFrame(bar_container)
        bar_fill.setStyleSheet(f"background-color: {color}; border-radius: 4px; border: none;")
        bar_fill.setFixedWidth(int(pct * 3))
        bar_fill.setFixedHeight(20)

        bar_layout = QHBoxLayout(bar_container)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.addWidget(bar_fill)
        bar_layout.addStretch()

        layout.addWidget(bar_container, 1)

        lbl_val = QLabel(format_currency(amount))
        lbl_val.setStyleSheet("font-size: 13px; font-weight: bold; color: #2C3E50; border: none; min-width: 100px;")
        lbl_val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(lbl_val)

        lbl_pct = QLabel(f"{pct:.1f}%")
        lbl_pct.setStyleSheet("font-size: 12px; color: #6C757D; border: none; min-width: 50px;")
        lbl_pct.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(lbl_pct)


class ExpensesScreen(QWidget):
    def __init__(self, auth_service=None, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service or AuthService()
        self.expense_repo = ExpenseRepository()
        self._build_ui()
        self._load_expenses()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QHBoxLayout()
        title = QLabel("Expenses Management")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2C3E50;")
        header.addWidget(title)
        header.addStretch()

        self.btn_record = QPushButton("  + Record Expense")
        _style_button(self.btn_record)
        self.btn_record.clicked.connect(self._record_expense)
        header.addWidget(self.btn_record)

        layout.addLayout(header)
        layout.addSpacing(16)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("From:"))
        self.dt_from = QDateEdit()
        self.dt_from.setCalendarPopup(True)
        self.dt_from.setDate(QDate.currentDate().addDays(-30))
        self.dt_from.setStyleSheet(
            "padding: 6px; font-size: 13px; border: 1px solid #CED4DA; border-radius: 4px;"
        )
        self.dt_from.dateChanged.connect(self._load_expenses)
        filter_row.addWidget(self.dt_from)

        filter_row.addWidget(QLabel("To:"))
        self.dt_to = QDateEdit()
        self.dt_to.setCalendarPopup(True)
        self.dt_to.setDate(QDate.currentDate())
        self.dt_to.setStyleSheet(
            "padding: 6px; font-size: 13px; border: 1px solid #CED4DA; border-radius: 4px;"
        )
        self.dt_to.dateChanged.connect(self._load_expenses)
        filter_row.addWidget(self.dt_to)

        self.btn_refresh = QPushButton("  Refresh")
        _style_button(self.btn_refresh, "#6C757D")
        self.btn_refresh.clicked.connect(self._load_expenses)
        filter_row.addWidget(self.btn_refresh)

        filter_row.addStretch()
        layout.addLayout(filter_row)
        layout.addSpacing(12)

        summary_bar = QHBoxLayout()
        self.lbl_total_expenses = QLabel("Total: KES 0.00")
        self.lbl_total_expenses.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #DC3545; padding: 8px;"
            "background-color: #FFF5F5; border: 1px solid #FECACA; border-radius: 4px;"
        )
        summary_bar.addWidget(self.lbl_total_expenses)

        self.lbl_count = QLabel("0 expenses")
        self.lbl_count.setStyleSheet(
            "font-size: 14px; color: #6C757D; padding: 8px;"
        )
        summary_bar.addWidget(self.lbl_count)

        summary_bar.addStretch()
        layout.addLayout(summary_bar)
        layout.addSpacing(8)

        self.table = QTableWidget()
        _style_table(self.table)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Date", "Category", "Description", "Amount", "Recorded By"])
        self.table.setColumnWidth(0, 130)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 250)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 150)
        layout.addWidget(self.table, 2)

        layout.addSpacing(16)

        breakdown_group = QLabel("Category Breakdown")
        breakdown_group.setStyleSheet("font-size: 16px; font-weight: bold; color: #2C3E50; padding: 4px 0;")
        layout.addWidget(breakdown_group)
        layout.addSpacing(8)

        self.breakdown_container = QVBoxLayout()
        self.breakdown_container.setSpacing(6)
        layout.addLayout(self.breakdown_container)
        layout.addStretch()

    def _load_expenses(self):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        try:
            branch_id = self.auth_service.current_branch.id
            start = self.dt_from.date().toPyDate()
            end = self.dt_to.date().toPyDate()

            start_dt = datetime.combine(start, datetime.min.time())
            end_dt = datetime.combine(end, datetime.max.time())

            with db_manager.get_session() as session:
                expenses = self.expense_repo.get_by_branch(branch_id, start_date=start_dt, end_date=end_dt, session=session)

            total = 0
            for row, exp in enumerate(expenses):
                self.table.insertRow(row)
                exp_date = exp.expense_date
                if hasattr(exp_date, "strftime"):
                    date_str = exp_date.strftime("%Y-%m-%d")
                else:
                    date_str = str(exp_date)[:10]
                self.table.setItem(row, 0, QTableWidgetItem(date_str))
                self.table.setItem(row, 1, QTableWidgetItem(exp.category))
                self.table.setItem(row, 2, QTableWidgetItem(exp.description or ""))
                amt_item = QTableWidgetItem(format_currency(exp.amount))
                amt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 3, amt_item)
                self.table.setItem(row, 4, QTableWidgetItem(
                    exp.recorded_by_user.full_name if exp.recorded_by_user else ""
                ))
                total += exp.amount

            self.lbl_total_expenses.setText(f"Total: {format_currency(total)}")
            self.lbl_count.setText(f"{len(expenses)} expenses")

            self._load_category_breakdown(branch_id, start_dt, end_dt)

        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

        self.table.setSortingEnabled(True)

    def _load_category_breakdown(self, branch_id, start_dt, end_dt):
        for i in reversed(range(self.breakdown_container.count())):
            widget = self.breakdown_container.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        try:
            with db_manager.get_session() as session:
                breakdown = self.expense_repo.get_category_breakdown(branch_id, start_dt, end_dt, session=session)
            total = sum(float(row.total_amount) for row in breakdown)

            for row in breakdown:
                cat_bar = CategoryBar(row.category, float(row.total_amount), total)
                self.breakdown_container.addWidget(cat_bar)

            if not breakdown:
                lbl = QLabel("No expenses recorded for this period.")
                lbl.setStyleSheet("color: #ADB5BD; font-style: italic; padding: 12px;")
                self.breakdown_container.addWidget(lbl)

        except Exception as e:
            lbl = QLabel(f"Could not load breakdown: {e}")
            lbl.setStyleSheet("color: #DC3545; padding: 12px;")
            self.breakdown_container.addWidget(lbl)

    def _record_expense(self):
        dialog = ExpenseDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                with db_manager.get_session() as session:
                    self.expense_repo.create(
                        session,
                        branch_id=self.auth_service.current_branch.id,
                        category=data["category"],
                        description=data["description"],
                        amount=data["amount"],
                        expense_date=datetime.combine(data["expense_date"], datetime.min.time()),
                        recorded_by=self.auth_service.current_user.id,
                    )
                self._load_expenses()
                QMessageBox.information(self, "Success",
                    f"Expense of {format_currency(data['amount'])} recorded under '{data['category']}'.")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))
