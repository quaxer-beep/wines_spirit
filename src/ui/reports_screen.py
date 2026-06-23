from datetime import date, timedelta

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QFrame,
    QDateEdit, QComboBox, QHeaderView, QMessageBox, QGroupBox, QScrollArea
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QBrush, QFont

from src.services.auth_service import AuthService
from src.services.reporting_service import ReportingService
from src.services.sync_service import SyncService
from src.utils.helpers import format_currency

PRIMARY = "#2E86DE"
LIGHT_BG = "#F5F6FA"
WHITE = "#FFFFFF"


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


class DashboardCard(QFrame):
    def __init__(self, title, value, subtitle="", color=PRIMARY, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            f"""
            DashboardCard {{
                background-color: white;
                border: 1px solid #DEE2E6;
                border-radius: 8px;
                border-top: 4px solid {color};
            }}
            """
        )
        self.setMinimumHeight(140)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet(f"font-size: 12px; color: #6C757D; font-weight: bold; border: none;")
        layout.addWidget(self.lbl_title)

        self.lbl_value = QLabel(str(value))
        self.lbl_value.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {color}; border: none;")
        layout.addWidget(self.lbl_value)

        if subtitle:
            self.lbl_sub = QLabel(subtitle)
            self.lbl_sub.setStyleSheet("font-size: 11px; color: #ADB5BD; border: none;")
            layout.addWidget(self.lbl_sub)
        else:
            layout.addStretch()

    def set_value(self, value):
        self.lbl_value.setText(str(value))


class DashboardTab(QWidget):
    CARD_COLORS = [
        ("#2E86DE", "Today's Sales"),
        ("#28A745", "Today's Transactions"),
        ("#DC3545", "Today's Expenses"),
        ("#F39C12", "Low Stock Items"),
        ("#6F42C1", "Pending Syncs"),
    ]

    def __init__(self, report_service, auth_service):
        super().__init__()
        self.report_service = report_service
        self.auth_service = auth_service
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QLabel("Dashboard Summary")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #2C3E50;")
        layout.addWidget(header)

        layout.addSpacing(16)

        grid = QGridLayout()
        grid.setSpacing(16)
        self.cards = []
        colors = [
            ("#2E86DE", "Today's Sales", "KES 0.00", "0 transactions"),
            ("#28A745", "Today's Transactions", "0", "Sales count"),
            ("#DC3545", "Today's Expenses", "KES 0.00", ""),
            ("#F39C12", "Low Stock Items", "0", "Products below reorder level"),
            ("#6F42C1", "Pending Syncs", "0", "Records waiting to sync"),
        ]
        for i, (color, title, val, sub) in enumerate(colors):
            card = DashboardCard(title, val, sub, color)
            self.cards.append(card)
            grid.addWidget(card, i // 3, i % 3)

        layout.addLayout(grid)
        layout.addStretch()

    def refresh(self):
        try:
            branch_id = self.auth_service.current_branch.id
            data = self.report_service.get_summary_dashboard(branch_id)
            self.cards[0].set_value(format_currency(data.get("today_sales", 0)))
            self.cards[1].set_value(str(data.get("today_transactions", 0)))
            self.cards[2].set_value(format_currency(data.get("today_expenses", 0)))
            self.cards[3].set_value(str(data.get("low_stock_count", 0)))
            self.cards[4].set_value(str(data.get("pending_syncs", 0)))
        except Exception as e:
            pass


class SalesReportsTab(QWidget):
    def __init__(self, report_service, auth_service):
        super().__init__()
        self.report_service = report_service
        self.auth_service = auth_service
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        top = QHBoxLayout()
        top.addWidget(QLabel("From:"))
        self.dt_from = QDateEdit()
        self.dt_from.setCalendarPopup(True)
        self.dt_from.setDate(QDate.currentDate().addDays(-30))
        self.dt_from.setStyleSheet(
            "padding: 6px; font-size: 13px; border: 1px solid #CED4DA; border-radius: 4px;"
        )
        top.addWidget(self.dt_from)

        top.addWidget(QLabel("To:"))
        self.dt_to = QDateEdit()
        self.dt_to.setCalendarPopup(True)
        self.dt_to.setDate(QDate.currentDate())
        self.dt_to.setStyleSheet(
            "padding: 6px; font-size: 13px; border: 1px solid #CED4DA; border-radius: 4px;"
        )
        top.addWidget(self.dt_to)

        self.cmb_view = QComboBox()
        self.cmb_view.addItems(["Daily", "Weekly", "Monthly", "By Cashier", "By Brand"])
        self.cmb_view.setStyleSheet(
            "padding: 6px; font-size: 13px; border: 1px solid #CED4DA; border-radius: 4px; min-width: 120px;"
        )
        top.addWidget(self.cmb_view)

        self.btn_generate = QPushButton("  Generate")
        _style_button(self.btn_generate)
        self.btn_generate.clicked.connect(self._generate)
        top.addWidget(self.btn_generate)

        top.addStretch()
        layout.addLayout(top)
        layout.addSpacing(8)

        self.table = QTableWidget()
        _style_table(self.table)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Date / Period", "Transactions", "Total Sales", "Cash", "M-Pesa"])
        self.table.setColumnWidth(0, 180)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 150)
        self.table.setColumnWidth(4, 150)
        layout.addWidget(self.table)

        layout.addSpacing(8)

        summary = QHBoxLayout()
        self.lbl_total = QLabel("Total: KES 0.00")
        self.lbl_total.setStyleSheet("font-size: 14px; font-weight: bold; color: #2C3E50; padding: 6px;")
        summary.addWidget(self.lbl_total)

        self.lbl_avg = QLabel("Average: KES 0.00")
        self.lbl_avg.setStyleSheet("font-size: 14px; font-weight: bold; color: #6C757D; padding: 6px;")
        summary.addWidget(self.lbl_avg)

        summary.addStretch()
        layout.addLayout(summary)

    def _generate(self):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        try:
            branch_id = self.auth_service.current_branch.id
            start = self.dt_from.date().toPyDate()
            end = self.dt_to.date().toPyDate()
            view = self.cmb_view.currentText()

            if view == "Daily":
                self._load_daily(branch_id, start, end)
            elif view == "Weekly":
                self._load_weekly(branch_id, start, end)
            elif view == "Monthly":
                self._load_monthly(branch_id, start, end)
            elif view == "By Cashier":
                self._load_by_cashier(branch_id, start, end)
            elif view == "By Brand":
                self._load_by_brand(branch_id, start, end)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

        self.table.setSortingEnabled(True)

    def _load_daily(self, branch_id, start, end):
        total_sales = 0
        total_count = 0
        row = 0
        current = start
        while current <= end:
            try:
                report = self.report_service.get_daily_sales_report(branch_id, current)
            except Exception:
                current += timedelta(days=1)
                continue

            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(current.isoformat()))
            self.table.setItem(row, 1, QTableWidgetItem(str(report["sale_count"])))
            self.table.setItem(row, 2, QTableWidgetItem(format_currency(report["total_sales"])))
            cash = report.get("payment_breakdown", {}).get("CASH", {}).get("total", 0)
            mpesa = report.get("payment_breakdown", {}).get("MPESA", {}).get("total", 0)
            self.table.setItem(row, 3, QTableWidgetItem(format_currency(cash)))
            self.table.setItem(row, 4, QTableWidgetItem(format_currency(mpesa)))
            total_sales += report["total_sales"]
            total_count += report["sale_count"]
            row += 1
            current += timedelta(days=1)

        self.lbl_total.setText(f"Total: {format_currency(total_sales)} ({total_count} transactions)")
        self.lbl_avg.setText(f"Average: {format_currency(total_sales / max(total_count, 1))}")

    def _load_weekly(self, branch_id, start, end):
        self.table.setHorizontalHeaderLabels(["Week", "Transactions", "Total Sales", "", ""])
        self.table.setColumnHidden(3, True)
        self.table.setColumnHidden(4, True)
        total_sales = 0
        total_count = 0
        row = 0
        current = start
        while current <= end:
            iso_year, iso_week, _ = current.isocalendar()
            try:
                report = self.report_service.get_weekly_sales_report(branch_id, iso_year, iso_week)
            except Exception:
                current += timedelta(weeks=1)
                continue

            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(f"W{iso_week:02d} {iso_year}"))
            self.table.setItem(row, 1, QTableWidgetItem(str(report["sale_count"])))
            self.table.setItem(row, 2, QTableWidgetItem(format_currency(report["total_sales"])))
            total_sales += report["total_sales"]
            total_count += report["sale_count"]
            row += 1
            current += timedelta(weeks=1)

        self.lbl_total.setText(f"Total: {format_currency(total_sales)} ({total_count} transactions)")
        self.lbl_avg.setText(f"Average: {format_currency(total_sales / max(total_count, 1))}")

    def _load_monthly(self, branch_id, start, end):
        self.table.setHorizontalHeaderLabels(["Month", "Transactions", "Total Sales", "", ""])
        self.table.setColumnHidden(3, True)
        self.table.setColumnHidden(4, True)
        total_sales = 0
        total_count = 0
        row = 0
        current = start.replace(day=1)
        while current <= end:
            try:
                report = self.report_service.get_monthly_sales_report(branch_id, current.year, current.month)
            except Exception:
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)
                continue

            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(current.strftime("%B %Y")))
            self.table.setItem(row, 1, QTableWidgetItem(str(report["sale_count"])))
            self.table.setItem(row, 2, QTableWidgetItem(format_currency(report["total_sales"])))
            total_sales += report["total_sales"]
            total_count += report["sale_count"]
            row += 1
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

        self.lbl_total.setText(f"Total: {format_currency(total_sales)} ({total_count} transactions)")
        self.lbl_avg.setText(f"Average: {format_currency(total_sales / max(total_count, 1))}")

    def _load_by_cashier(self, branch_id, start, end):
        self.table.setHorizontalHeaderLabels(["Cashier", "Transactions", "Total Sales", "", ""])
        self.table.setColumnHidden(3, True)
        self.table.setColumnHidden(4, True)
        try:
            rows = self.report_service.get_sales_by_cashier(branch_id, start, end)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return

        total_sales = 0
        total_count = 0
        for row_idx, r in enumerate(rows):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(r["cashier_name"]))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(r["sale_count"])))
            self.table.setItem(row_idx, 2, QTableWidgetItem(format_currency(r["total_sales"])))
            total_sales += r["total_sales"]
            total_count += r["sale_count"]

        self.lbl_total.setText(f"Total: {format_currency(total_sales)} ({total_count} transactions)")

    def _load_by_brand(self, branch_id, start, end):
        self.table.setHorizontalHeaderLabels(["Brand", "Units", "Revenue", "", ""])
        self.table.setColumnHidden(3, True)
        self.table.setColumnHidden(4, True)
        try:
            rows = self.report_service.get_brand_profit_report(branch_id, start, end)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return

        total_rev = 0
        total_units = 0
        for row_idx, r in enumerate(rows):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(r["brand_name"]))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(r["units_sold"])))
            self.table.setItem(row_idx, 2, QTableWidgetItem(format_currency(r["total_revenue"])))
            total_rev += r["total_revenue"]
            total_units += r["units_sold"]

        self.lbl_total.setText(f"Total Revenue: {format_currency(total_rev)} ({total_units} units)")


class FinancialReportsTab(QWidget):
    def __init__(self, report_service, auth_service):
        super().__init__()
        self.report_service = report_service
        self.auth_service = auth_service
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        top = QHBoxLayout()
        top.addWidget(QLabel("From:"))
        self.dt_from = QDateEdit()
        self.dt_from.setCalendarPopup(True)
        self.dt_from.setDate(QDate.currentDate().addDays(-30))
        self.dt_from.setStyleSheet(
            "padding: 6px; font-size: 13px; border: 1px solid #CED4DA; border-radius: 4px;"
        )
        top.addWidget(self.dt_from)

        top.addWidget(QLabel("To:"))
        self.dt_to = QDateEdit()
        self.dt_to.setCalendarPopup(True)
        self.dt_to.setDate(QDate.currentDate())
        self.dt_to.setStyleSheet(
            "padding: 6px; font-size: 13px; border: 1px solid #CED4DA; border-radius: 4px;"
        )
        top.addWidget(self.dt_to)

        self.btn_generate = QPushButton("  Generate")
        _style_button(self.btn_generate)
        self.btn_generate.clicked.connect(self._generate)
        top.addWidget(self.btn_generate)

        top.addStretch()
        layout.addLayout(top)
        layout.addSpacing(12)

        cards_grid = QGridLayout()
        cards_grid.setSpacing(12)

        self.cards = {}
        card_configs = [
            ("total_revenue", "Total Revenue", "KES 0.00", "#2E86DE"),
            ("cogs", "Cost of Goods Sold", "KES 0.00", "#DC3545"),
            ("gross_profit", "Gross Profit", "KES 0.00", "#28A745"),
            ("expenses", "Expenses", "KES 0.00", "#F39C12"),
            ("net_profit", "Net Profit", "KES 0.00", "#6F42C1"),
            ("profit_margin", "Profit Margin", "0%", "#17A2B8"),
        ]
        for i, (key, title, default, color) in enumerate(card_configs):
            card = DashboardCard(title, default, "", color)
            self.cards[key] = card
            cards_grid.addWidget(card, i // 3, i % 3)

        layout.addLayout(cards_grid)
        layout.addSpacing(16)

        brand_group = QGroupBox("Brand Profit Breakdown")
        brand_group.setStyleSheet(
            "QGroupBox { font-weight: bold; font-size: 14px; border: 1px solid #DEE2E6; "
            "border-radius: 6px; margin-top: 10px; padding-top: 20px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; background: white; }"
        )
        bv = QVBoxLayout(brand_group)

        self.brand_table = QTableWidget()
        _style_table(self.brand_table)
        self.brand_table.setColumnCount(6)
        self.brand_table.setHorizontalHeaderLabels(["Brand", "Units", "Cost", "Revenue", "Profit", "Margin %"])
        self.brand_table.setColumnWidth(0, 180)
        self.brand_table.setColumnWidth(1, 80)
        self.brand_table.setColumnWidth(2, 120)
        self.brand_table.setColumnWidth(3, 120)
        self.brand_table.setColumnWidth(4, 120)
        self.brand_table.setColumnWidth(5, 100)
        bv.addWidget(self.brand_table)

        layout.addWidget(brand_group)

    def _generate(self):
        try:
            branch_id = self.auth_service.current_branch.id
            start = self.dt_from.date().toPyDate()
            end = self.dt_to.date().toPyDate()

            report = self.report_service.get_profit_report(branch_id, start, end)
            self.cards["total_revenue"].set_value(format_currency(report["total_revenue"]))
            self.cards["cogs"].set_value(format_currency(report["total_cost_of_goods"]))
            self.cards["gross_profit"].set_value(format_currency(report["gross_profit"]))
            self.cards["expenses"].set_value(format_currency(report["total_expenses"]))
            self.cards["net_profit"].set_value(format_currency(report["net_profit"]))
            self.cards["profit_margin"].set_value(f"{report['profit_margin_percent']}%")

            brands = self.report_service.get_brand_profit_report(branch_id, start, end)
            self.brand_table.setSortingEnabled(False)
            self.brand_table.setRowCount(0)
            for row, b in enumerate(brands):
                self.brand_table.insertRow(row)
                self.brand_table.setItem(row, 0, QTableWidgetItem(b["brand_name"]))
                self.brand_table.setItem(row, 1, QTableWidgetItem(str(b["units_sold"])))
                self.brand_table.setItem(row, 2, QTableWidgetItem(format_currency(b["total_cost"])))
                self.brand_table.setItem(row, 3, QTableWidgetItem(format_currency(b["total_revenue"])))
                self.brand_table.setItem(row, 4, QTableWidgetItem(format_currency(b["gross_profit"])))
                self.brand_table.setItem(row, 5, QTableWidgetItem(f"{b['margin_percent']}%"))
            self.brand_table.setSortingEnabled(True)

        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))


class InventoryReportsTab(QWidget):
    def __init__(self, report_service, auth_service):
        super().__init__()
        self.report_service = report_service
        self.auth_service = auth_service
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        top = QHBoxLayout()
        self.btn_generate = QPushButton("  Generate Reports")
        _style_button(self.btn_generate)
        self.btn_generate.clicked.connect(self._generate)
        top.addWidget(self.btn_generate)

        self.btn_export = QPushButton("  Export (Console)")
        _style_button(self.btn_export, "#6C757D")
        self.btn_export.clicked.connect(self._export)
        top.addWidget(self.btn_export)

        top.addStretch()
        layout.addLayout(top)
        layout.addSpacing(16)

        valuation_group = QGroupBox("Inventory Valuation")
        valuation_group.setStyleSheet(
            "QGroupBox { font-weight: bold; font-size: 14px; border: 1px solid #DEE2E6; "
            "border-radius: 6px; margin-top: 10px; padding-top: 20px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; background: white; }"
        )
        vv = QHBoxLayout(valuation_group)

        self.lbl_cost = QLabel("Cost Value: --")
        self.lbl_cost.setStyleSheet("font-size: 18px; font-weight: bold; color: #DC3545; padding: 10px;")
        vv.addWidget(self.lbl_cost)

        self.lbl_retail = QLabel("Retail Value: --")
        self.lbl_retail.setStyleSheet("font-size: 18px; font-weight: bold; color: #28A745; padding: 10px;")
        vv.addWidget(self.lbl_retail)

        self.lbl_markup = QLabel("Potential Markup: --")
        self.lbl_markup.setStyleSheet("font-size: 18px; font-weight: bold; color: #2E86DE; padding: 10px;")
        vv.addWidget(self.lbl_markup)

        layout.addWidget(valuation_group)
        layout.addSpacing(16)

        low_stock_group = QGroupBox("Low Stock Report")
        low_stock_group.setStyleSheet(valuation_group.styleSheet())
        lv = QVBoxLayout(low_stock_group)

        self.low_table = QTableWidget()
        _style_table(self.low_table)
        self.low_table.setColumnCount(6)
        self.low_table.setHorizontalHeaderLabels(["Product", "Brand", "Barcode", "Qty On Hand", "Reorder Level", "Shortage"])
        self.low_table.setColumnWidth(0, 200)
        self.low_table.setColumnWidth(1, 120)
        self.low_table.setColumnWidth(2, 120)
        self.low_table.setColumnWidth(3, 100)
        self.low_table.setColumnWidth(4, 100)
        self.low_table.setColumnWidth(5, 100)
        lv.addWidget(self.low_table)

        layout.addWidget(low_stock_group)

    def _generate(self):
        try:
            branch_id = self.auth_service.current_branch.id

            valuation = self.report_service.get_inventory_valuation_report(branch_id)
            self.lbl_cost.setText(f"Cost Value: {format_currency(valuation['cost_value'])}")
            self.lbl_retail.setText(f"Retail Value: {format_currency(valuation['retail_value'])}")
            self.lbl_markup.setText(f"Potential Markup: {format_currency(valuation['potential_markup'])}")

            low_stock = self.report_service.get_low_stock_report(branch_id)
            self.low_table.setSortingEnabled(False)
            self.low_table.setRowCount(0)
            for row, item in enumerate(low_stock):
                self.low_table.insertRow(row)
                self.low_table.setItem(row, 0, QTableWidgetItem(item["product_name"]))
                self.low_table.setItem(row, 1, QTableWidgetItem(item.get("brand") or ""))
                self.low_table.setItem(row, 2, QTableWidgetItem(item.get("barcode") or ""))
                self.low_table.setItem(row, 3, QTableWidgetItem(str(int(item["quantity_on_hand"]))))
                self.low_table.setItem(row, 4, QTableWidgetItem(str(int(item["reorder_level"]))))
                self.low_table.setItem(row, 5, QTableWidgetItem(str(int(item["shortage"]))))
            self.low_table.setSortingEnabled(True)

        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _export(self):
        try:
            branch_id = self.auth_service.current_branch.id
            valuation = self.report_service.get_inventory_valuation_report(branch_id)
            low_stock = self.report_service.get_low_stock_report(branch_id)

            print("=" * 60)
            print("INVENTORY VALUATION REPORT")
            print("=" * 60)
            print(f"Cost Value: {format_currency(valuation['cost_value'])}")
            print(f"Retail Value: {format_currency(valuation['retail_value'])}")
            print(f"Potential Markup: {format_currency(valuation['potential_markup'])}")
            print()
            print("LOW STOCK ITEMS:")
            print("-" * 60)
            for item in low_stock:
                print(f"  {item['product_name']}: {int(item['quantity_on_hand'])} / {int(item['reorder_level'])}")
            print("=" * 60)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))


class ReportsScreen(QWidget):
    def __init__(self, reporting_service=None, auth_service=None, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service or AuthService()
        self.report_service = reporting_service or ReportingService()
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

        self.dash_tab = DashboardTab(self.report_service, self.auth_service)
        self.tabs.addTab(self.dash_tab, "Dashboard")

        self.sales_tab = SalesReportsTab(self.report_service, self.auth_service)
        self.tabs.addTab(self.sales_tab, "Sales Reports")

        self.financial_tab = FinancialReportsTab(self.report_service, self.auth_service)
        self.tabs.addTab(self.financial_tab, "Financial Reports")

        self.inv_report_tab = InventoryReportsTab(self.report_service, self.auth_service)
        self.tabs.addTab(self.inv_report_tab, "Inventory Reports")

        layout.addWidget(self.tabs)

    def refresh(self):
        self.dash_tab.refresh()
