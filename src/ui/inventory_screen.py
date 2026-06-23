from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QLabel,
    QDialog, QFormLayout, QDialogButtonBox, QComboBox, QDoubleSpinBox,
    QSpinBox, QDateEdit, QHeaderView, QMessageBox, QFrame, QGroupBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QBrush, QFont

from src.services.auth_service import AuthService
from src.services.inventory_service import InventoryService
from src.utils.helpers import format_currency
from src.utils.exceptions import ValidationError, NotFoundError, AuthorizationError
from src.database.connection import db_manager
from src.database.models import Category

PRIMARY = "#2E86DE"
PRIMARY_HOVER = "#1A6EC1"
WHITE = "#FFFFFF"
LIGHT_BG = "#F5F6FA"
YELLOW_BG = QColor(255, 255, 200)
RED_BG = QColor(255, 200, 200)
RED_FG = QColor(200, 50, 50)
GREEN_FG = QColor(40, 180, 40)


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
            background-color: {PRIMARY_HOVER};
        }}
        QPushButton:pressed {{
            background-color: #155A9E;
        }}
        QPushButton:disabled {{
            background-color: #BDC3C7;
        }}
        """
    )


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


def _get_categories():
    with db_manager.get_session() as session:
        cats = session.query(Category).order_by(Category.name).all()
        return [(c.id, c.name) for c in cats]


class ProductDialog(QDialog):
    def __init__(self, parent=None, product_data=None):
        super().__init__(parent)
        self.product_data = product_data
        self.setWindowTitle("Add Product" if product_data is None else "Edit Product")
        self.setMinimumWidth(450)
        self.setModal(True)
        self._build_ui()
        if product_data:
            self._populate(product_data)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        form = QFormLayout()
        form.setSpacing(8)

        self.txt_barcode = QLineEdit()
        self.txt_barcode.setPlaceholderText("Optional barcode")
        form.addRow("Barcode:", self.txt_barcode)

        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("Product name *")
        form.addRow("Name:", self.txt_name)

        self.txt_brand = QLineEdit()
        self.txt_brand.setPlaceholderText("Brand name")
        form.addRow("Brand:", self.txt_brand)

        self.cmb_category = QComboBox()
        self.cmb_category.addItem("-- Select Category --", None)
        for cid, cname in _get_categories():
            self.cmb_category.addItem(cname, cid)
        form.addRow("Category:", self.cmb_category)

        self.spn_cost = QDoubleSpinBox()
        self.spn_cost.setRange(0, 9999999)
        self.spn_cost.setDecimals(2)
        self.spn_cost.setPrefix("KES ")
        form.addRow("Cost Price:", self.spn_cost)

        self.spn_selling = QDoubleSpinBox()
        self.spn_selling.setRange(0, 9999999)
        self.spn_selling.setDecimals(2)
        self.spn_selling.setPrefix("KES ")
        form.addRow("Selling Price:", self.spn_selling)

        self.spn_reorder = QDoubleSpinBox()
        self.spn_reorder.setRange(0, 999999)
        self.spn_reorder.setDecimals(0)
        self.spn_reorder.setValue(0)
        form.addRow("Reorder Level:", self.spn_reorder)

        layout.addLayout(form)
        layout.addSpacing(10)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setStyleSheet(
            """
            QDialog { background-color: white; }
            QLabel { font-size: 13px; }
            QLineEdit, QComboBox, QDoubleSpinBox {
                padding: 6px; font-size: 13px; border: 1px solid #CED4DA;
                border-radius: 4px; min-height: 20px;
            }
            QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {
                border-color: """ + PRIMARY + """;
            }
            """
        )

    def _populate(self, data):
        self.txt_barcode.setText(data.get("barcode") or "")
        self.txt_name.setText(data.get("name") or "")
        self.txt_brand.setText(data.get("brand") or "")
        cid = data.get("category_id")
        if cid is not None:
            idx = self.cmb_category.findData(cid)
            if idx >= 0:
                self.cmb_category.setCurrentIndex(idx)
        self.spn_cost.setValue(float(data.get("cost_price", 0)))
        self.spn_selling.setValue(float(data.get("selling_price", 0)))
        self.spn_reorder.setValue(float(data.get("reorder_level", 0)))

    def _validate_and_accept(self):
        if not self.txt_name.text().strip():
            QMessageBox.warning(self, "Validation Error", "Product name is required.")
            self.txt_name.setFocus()
            return
        self.accept()

    def get_data(self):
        return {
            "barcode": self.txt_barcode.text().strip() or None,
            "name": self.txt_name.text().strip(),
            "brand": self.txt_brand.text().strip() or None,
            "category_id": self.cmb_category.currentData(),
            "cost_price": self.spn_cost.value(),
            "selling_price": self.spn_selling.value(),
            "reorder_level": self.spn_reorder.value(),
        }


class StockInDialog(QDialog):
    def __init__(self, inventory_service, auth_service, parent=None):
        super().__init__(parent)
        self.inventory_service = inventory_service
        self.auth_service = auth_service
        self.selected_product = None
        self.setWindowTitle("Stock In")
        self.setMinimumWidth(450)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Search product by name or barcode...")
        self.txt_search.textChanged.connect(self._search_products)
        form.addRow("Product:", self.txt_search)

        self.lbl_selected = QLabel("No product selected")
        self.lbl_selected.setStyleSheet("color: #888; font-weight: bold;")
        form.addRow("", self.lbl_selected)

        self.spn_qty = QDoubleSpinBox()
        self.spn_qty.setRange(1, 999999)
        self.spn_qty.setDecimals(0)
        self.spn_qty.setValue(1)
        form.addRow("Quantity:", self.spn_qty)

        self.spn_unit_cost = QDoubleSpinBox()
        self.spn_unit_cost.setRange(0, 9999999)
        self.spn_unit_cost.setDecimals(2)
        self.spn_unit_cost.setPrefix("KES ")
        form.addRow("Unit Cost (optional):", self.spn_unit_cost)

        self.txt_notes = QLineEdit()
        self.txt_notes.setPlaceholderText("Optional notes")
        form.addRow("Notes:", self.txt_notes)

        layout.addLayout(form)
        layout.addSpacing(10)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setStyleSheet(self._style())

    def _style(self):
        return """
            QDialog { background-color: white; }
            QLabel { font-size: 13px; }
            QLineEdit, QDoubleSpinBox {
                padding: 6px; font-size: 13px; border: 1px solid #CED4DA;
                border-radius: 4px; min-height: 20px;
            }
            QLineEdit:focus, QDoubleSpinBox:focus {
                border-color: """ + PRIMARY + """;
            }
        """

    def _search_products(self, text):
        if len(text.strip()) < 2:
            return
        self.selected_product = None
        self.lbl_selected.setText("No product selected")
        self.lbl_selected.setStyleSheet("color: #888; font-weight: bold;")
        try:
            branch_id = self.auth_service.current_branch.id
            results = self.inventory_service.search_products(text.strip(), branch_id=branch_id)
            if results:
                self.selected_product = results[0]
                self.lbl_selected.setText(f"{results[0]['name']} ({results[0].get('barcode', 'N/A')})")
                self.lbl_selected.setStyleSheet("color: #2E86DE; font-weight: bold;")
        except Exception:
            pass

    def _accept(self):
        if not self.selected_product:
            QMessageBox.warning(self, "Validation Error", "Please search and select a product.")
            return
        if self.spn_qty.value() < 1:
            QMessageBox.warning(self, "Validation Error", "Quantity must be at least 1.")
            return
        self.accept()

    def get_data(self):
        return {
            "product_id": self.selected_product["id"],
            "product_name": self.selected_product["name"],
            "quantity": self.spn_qty.value(),
            "unit_cost": self.spn_unit_cost.value() if self.spn_unit_cost.value() > 0 else None,
            "notes": self.txt_notes.text().strip(),
        }


class StockOutDialog(QDialog):
    def __init__(self, inventory_service, auth_service, parent=None):
        super().__init__(parent)
        self.inventory_service = inventory_service
        self.auth_service = auth_service
        self.selected_product = None
        self.setWindowTitle("Stock Out")
        self.setMinimumWidth(450)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Search product by name or barcode...")
        self.txt_search.textChanged.connect(self._search_products)
        form.addRow("Product:", self.txt_search)

        self.lbl_selected = QLabel("No product selected")
        self.lbl_selected.setStyleSheet("color: #888; font-weight: bold;")
        form.addRow("", self.lbl_selected)

        self.spn_qty = QDoubleSpinBox()
        self.spn_qty.setRange(1, 999999)
        self.spn_qty.setDecimals(0)
        self.spn_qty.setValue(1)
        form.addRow("Quantity:", self.spn_qty)

        self.cmb_reason = QComboBox()
        self.cmb_reason.addItems([
            "-- Select Reason --", "Damaged", "Expired", "Theft", "Return to Supplier",
            "Breakage", "Sample", "Donation", "Other"
        ])
        form.addRow("Reason:", self.cmb_reason)

        self.txt_notes = QLineEdit()
        self.txt_notes.setPlaceholderText("Optional notes")
        form.addRow("Notes:", self.txt_notes)

        layout.addLayout(form)
        layout.addSpacing(10)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setStyleSheet("""
            QDialog { background-color: white; }
            QLabel { font-size: 13px; }
            QLineEdit, QDoubleSpinBox, QComboBox {
                padding: 6px; font-size: 13px; border: 1px solid #CED4DA;
                border-radius: 4px; min-height: 20px;
            }
            QLineEdit:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border-color: """ + PRIMARY + """;
            }
        """)

    def _search_products(self, text):
        if len(text.strip()) < 2:
            return
        self.selected_product = None
        self.lbl_selected.setText("No product selected")
        self.lbl_selected.setStyleSheet("color: #888; font-weight: bold;")
        try:
            branch_id = self.auth_service.current_branch.id
            results = self.inventory_service.search_products(text.strip(), branch_id=branch_id)
            if results:
                self.selected_product = results[0]
                self.lbl_selected.setText(f"{results[0]['name']} ({results[0].get('barcode', 'N/A')})")
                self.lbl_selected.setStyleSheet("color: #2E86DE; font-weight: bold;")
        except Exception:
            pass

    def _accept(self):
        if not self.selected_product:
            QMessageBox.warning(self, "Validation Error", "Please search and select a product.")
            return
        if self.spn_qty.value() < 1:
            QMessageBox.warning(self, "Validation Error", "Quantity must be at least 1.")
            return
        if self.cmb_reason.currentIndex() == 0:
            QMessageBox.warning(self, "Validation Error", "Please select a reason.")
            return
        self.accept()

    def get_data(self):
        return {
            "product_id": self.selected_product["id"],
            "product_name": self.selected_product["name"],
            "quantity": self.spn_qty.value(),
            "reason": self.cmb_reason.currentText(),
            "notes": self.txt_notes.text().strip(),
        }


class AdjustStockDialog(QDialog):
    def __init__(self, inventory_service, auth_service, parent=None):
        super().__init__(parent)
        self.inventory_service = inventory_service
        self.auth_service = auth_service
        self.selected_product = None
        self.setWindowTitle("Adjust Stock")
        self.setMinimumWidth(450)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Search product by name or barcode...")
        self.txt_search.textChanged.connect(self._search_products)
        form.addRow("Product:", self.txt_search)

        self.lbl_selected = QLabel("No product selected")
        self.lbl_selected.setStyleSheet("color: #888; font-weight: bold;")
        form.addRow("", self.lbl_selected)

        self.spn_new_qty = QDoubleSpinBox()
        self.spn_new_qty.setRange(0, 999999)
        self.spn_new_qty.setDecimals(0)
        self.spn_new_qty.setValue(0)
        form.addRow("New Quantity:", self.spn_new_qty)

        self.txt_reason = QLineEdit()
        self.txt_reason.setPlaceholderText("Reason for adjustment *")
        form.addRow("Reason:", self.txt_reason)

        layout.addLayout(form)
        layout.addSpacing(10)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setStyleSheet("""
            QDialog { background-color: white; }
            QLabel { font-size: 13px; }
            QLineEdit, QDoubleSpinBox {
                padding: 6px; font-size: 13px; border: 1px solid #CED4DA;
                border-radius: 4px; min-height: 20px;
            }
            QLineEdit:focus, QDoubleSpinBox:focus {
                border-color: """ + PRIMARY + """;
            }
        """)

    def _search_products(self, text):
        if len(text.strip()) < 2:
            return
        self.selected_product = None
        self.lbl_selected.setText("No product selected")
        self.lbl_selected.setStyleSheet("color: #888; font-weight: bold;")
        try:
            branch_id = self.auth_service.current_branch.id
            results = self.inventory_service.search_products(text.strip(), branch_id=branch_id)
            if results:
                self.selected_product = results[0]
                self.lbl_selected.setText(f"{results[0]['name']} ({results[0].get('barcode', 'N/A')})")
                self.lbl_selected.setStyleSheet("color: #2E86DE; font-weight: bold;")
        except Exception:
            pass

    def _accept(self):
        if not self.selected_product:
            QMessageBox.warning(self, "Validation Error", "Please search and select a product.")
            return
        if not self.txt_reason.text().strip():
            QMessageBox.warning(self, "Validation Error", "Reason is required.")
            return
        self.accept()

    def get_data(self):
        return {
            "product_id": self.selected_product["id"],
            "product_name": self.selected_product["name"],
            "new_quantity": self.spn_new_qty.value(),
            "reason": self.txt_reason.text().strip(),
        }


class ProductsTab(QWidget):
    def __init__(self, inventory_service, auth_service):
        super().__init__()
        self.inv_service = inventory_service
        self.auth_service = auth_service
        self._build_ui()
        self._load_products()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        top = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Search products by name, barcode, or brand...")
        self.txt_search.setStyleSheet(
            "padding: 8px; font-size: 13px; border: 1px solid #CED4DA; border-radius: 4px;"
        )
        self.txt_search.textChanged.connect(self._search)
        top.addWidget(self.txt_search, 1)

        self.btn_add = QPushButton("  + Add Product")
        self.btn_add.setIconSize(self.btn_add.sizeHint())
        _style_button(self.btn_add)
        self.btn_add.clicked.connect(self._add_product)
        self.btn_add.setEnabled(self.auth_service.has_permission("products", "create"))
        top.addWidget(self.btn_add)

        self.btn_edit = QPushButton("  Edit")
        _style_button(self.btn_edit, "#28A745")
        self.btn_edit.clicked.connect(self._edit_product)
        self.btn_edit.setEnabled(False)
        top.addWidget(self.btn_edit)

        layout.addLayout(top)
        layout.addSpacing(8)

        self.table = QTableWidget()
        _style_table(self.table)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID", "Barcode", "Name", "Brand", "Category", "Cost Price", "Selling Price", "Active"])
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 200)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(6, 100)
        self.table.setColumnWidth(7, 60)
        self.table.itemSelectionChanged.connect(lambda: self.btn_edit.setEnabled(len(self.table.selectedItems()) > 0))
        self.table.doubleClicked.connect(self._edit_product)
        layout.addWidget(self.table)

    def _search(self):
        self._load_products(self.txt_search.text().strip())

    def _load_products(self, query=None):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        try:
            if query:
                products = self.inv_service.search_products(query)
            else:
                products = self.inv_service.search_products("")
            for row, p in enumerate(products):
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(p["id"])))
                self.table.setItem(row, 1, QTableWidgetItem(p.get("barcode") or ""))
                self.table.setItem(row, 2, QTableWidgetItem(p["name"]))
                self.table.setItem(row, 3, QTableWidgetItem(p.get("brand") or ""))
                self.table.setItem(row, 4, QTableWidgetItem(p.get("category_name") or ""))
                self.table.setItem(row, 5, QTableWidgetItem(format_currency(p["cost_price"])))
                self.table.setItem(row, 6, QTableWidgetItem(format_currency(p["selling_price"])))
                item = QTableWidgetItem("Yes" if p.get("is_active") else "No")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if not p.get("is_active"):
                    item.setForeground(QBrush(RED_FG))
                else:
                    item.setForeground(QBrush(GREEN_FG))
                self.table.setItem(row, 7, item)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
        self.table.setSortingEnabled(True)

    def _add_product(self):
        dialog = ProductDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                self.inv_service.add_product(self.auth_service.current_user, **data)
                self._load_products()
                QMessageBox.information(self, "Success", f"Product '{data['name']}' created.")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def _edit_product(self):
        selected = self.table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        product_id = int(self.table.item(row, 0).text())
        try:
            product = self.inv_service.get_product(product_id)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return

        dialog = ProductDialog(self, product_data=product)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                self.inv_service.update_product(self.auth_service.current_user, product_id, **data)
                self._load_products()
                QMessageBox.information(self, "Success", f"Product '{data['name']}' updated.")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))


class StockTab(QWidget):
    def __init__(self, inventory_service, auth_service):
        super().__init__()
        self.inv_service = inventory_service
        self.auth_service = auth_service
        self._build_ui()
        self._load_inventory()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        top = QHBoxLayout()
        self.btn_stock_in = QPushButton("  Stock In")
        _style_button(self.btn_stock_in, "#28A745")
        self.btn_stock_in.clicked.connect(self._stock_in)
        top.addWidget(self.btn_stock_in)

        self.btn_stock_out = QPushButton("  Stock Out")
        _style_button(self.btn_stock_out, "#DC3545")
        self.btn_stock_out.clicked.connect(self._stock_out)
        top.addWidget(self.btn_stock_out)

        self.btn_adjust = QPushButton("  Adjust")
        _style_button(self.btn_adjust, "#F39C12")
        self.btn_adjust.clicked.connect(self._adjust_stock)
        top.addWidget(self.btn_adjust)

        top.addStretch()

        self.btn_refresh = QPushButton("  Refresh")
        _style_button(self.btn_refresh, "#6C757D")
        self.btn_refresh.clicked.connect(self._load_inventory)
        top.addWidget(self.btn_refresh)

        layout.addLayout(top)
        layout.addSpacing(8)

        self.table = QTableWidget()
        _style_table(self.table)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Product", "Barcode", "Quantity", "Reorder Level", "Status", "Unit"])
        self.table.setColumnWidth(0, 250)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 80)
        self.table.setColumnWidth(5, 60)
        layout.addWidget(self.table)

    def _load_inventory(self):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        try:
            branch_id = self.auth_service.current_branch.id
            records = self.inv_service.get_branch_inventory(branch_id)
            for row, r in enumerate(records):
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(r["product_name"]))
                self.table.setItem(row, 1, QTableWidgetItem(r.get("barcode") or ""))
                self.table.setItem(row, 2, QTableWidgetItem(str(int(r["quantity_on_hand"]))))
                self.table.setItem(row, 3, QTableWidgetItem(str(int(r["reorder_level"]))))

                qty = r["quantity_on_hand"]
                reorder = r["reorder_level"]
                if qty == 0:
                    status = "Out"
                    status_color = RED_FG
                    bg = RED_BG
                elif reorder > 0 and qty <= reorder:
                    status = "Low"
                    status_color = QColor(200, 150, 0)
                    bg = YELLOW_BG
                else:
                    status = "OK"
                    status_color = GREEN_FG
                    bg = QColor(255, 255, 255)

                status_item = QTableWidgetItem(status)
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                status_item.setForeground(QBrush(status_color))

                self.table.setItem(row, 4, status_item)
                self.table.setItem(row, 5, QTableWidgetItem(r.get("unit") or "pcs"))

                if qty == 0 or (reorder > 0 and qty <= reorder):
                    for col in range(self.table.columnCount()):
                        existing = self.table.item(row, col)
                        if existing:
                            existing.setBackground(bg)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
        self.table.setSortingEnabled(True)

    def _stock_in(self):
        dialog = StockInDialog(self.inv_service, self.auth_service, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                branch_id = self.auth_service.current_branch.id
                self.inv_service.stock_in(
                    self.auth_service.current_user,
                    branch_id,
                    data["product_id"],
                    data["quantity"],
                    unit_cost=data.get("unit_cost"),
                    notes=data.get("notes", ""),
                )
                self._load_inventory()
                QMessageBox.information(self, "Success",
                    f"Added {int(data['quantity'])} units of '{data['product_name']}'.")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def _stock_out(self):
        dialog = StockOutDialog(self.inv_service, self.auth_service, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                branch_id = self.auth_service.current_branch.id
                self.inv_service.stock_out(
                    self.auth_service.current_user,
                    branch_id,
                    data["product_id"],
                    data["quantity"],
                    data["reason"],
                    notes=data.get("notes", ""),
                )
                self._load_inventory()
                QMessageBox.information(self, "Success",
                    f"Removed {int(data['quantity'])} units of '{data['product_name']}'.")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def _adjust_stock(self):
        dialog = AdjustStockDialog(self.inv_service, self.auth_service, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                branch_id = self.auth_service.current_branch.id
                self.inv_service.adjust_stock(
                    self.auth_service.current_user,
                    branch_id,
                    data["product_id"],
                    data["new_quantity"],
                    data["reason"],
                )
                self._load_inventory()
                QMessageBox.information(self, "Success",
                    f"Stock adjusted for '{data['product_name']}' to {int(data['new_quantity'])}.")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))


class MovementsTab(QWidget):
    def __init__(self, inventory_service, auth_service):
        super().__init__()
        self.inv_service = inventory_service
        self.auth_service = auth_service
        self._build_ui()
        self._load_movements()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("From:"))
        self.dt_from = QDateEdit()
        self.dt_from.setCalendarPopup(True)
        self.dt_from.setDate(QDate.currentDate().addDays(-30))
        self.dt_from.setStyleSheet(
            "padding: 6px; font-size: 13px; border: 1px solid #CED4DA; border-radius: 4px;"
        )
        filter_row.addWidget(self.dt_from)

        filter_row.addWidget(QLabel("To:"))
        self.dt_to = QDateEdit()
        self.dt_to.setCalendarPopup(True)
        self.dt_to.setDate(QDate.currentDate())
        self.dt_to.setStyleSheet(
            "padding: 6px; font-size: 13px; border: 1px solid #CED4DA; border-radius: 4px;"
        )
        filter_row.addWidget(self.dt_to)

        self.btn_filter = QPushButton("  Filter")
        _style_button(self.btn_filter)
        self.btn_filter.clicked.connect(self._load_movements)
        filter_row.addWidget(self.btn_filter)

        filter_row.addStretch()
        layout.addLayout(filter_row)
        layout.addSpacing(8)

        self.table = QTableWidget()
        _style_table(self.table)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Date", "Type", "Product", "Qty Change", "Reference", "Notes", "User"])
        self.table.setColumnWidth(0, 150)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 200)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 200)
        self.table.setColumnWidth(6, 120)
        layout.addWidget(self.table)

    def _load_movements(self):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        try:
            branch_id = self.auth_service.current_branch.id
            start = self.dt_from.date().toPyDate()
            end = self.dt_to.date().toPyDate()
            movements = self.inv_service.get_stock_movements(branch_id, start_date=start, end_date=end)
            for row, m in enumerate(movements):
                self.table.insertRow(row)
                created = m.get("created_at", "")
                if created:
                    created = created[:19].replace("T", " ")
                self.table.setItem(row, 0, QTableWidgetItem(created))

                mtype = m["movement_type"]
                type_item = QTableWidgetItem(mtype)
                type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if mtype == "IN":
                    type_item.setForeground(QBrush(GREEN_FG))
                elif mtype == "OUT":
                    type_item.setForeground(QBrush(RED_FG))
                else:
                    type_item.setForeground(QBrush(QColor(200, 150, 0)))
                self.table.setItem(row, 1, type_item)

                self.table.setItem(row, 2, QTableWidgetItem(m.get("product_name", "")))

                qty = abs(int(m["quantity"])) if m["quantity"] else 0
                qty_item = QTableWidgetItem(str(qty))
                qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if m["movement_type"] == "IN":
                    qty_item.setForeground(QBrush(GREEN_FG))
                elif m["movement_type"] == "OUT":
                    qty_item.setForeground(QBrush(RED_FG))
                self.table.setItem(row, 3, qty_item)

                self.table.setItem(row, 4, QTableWidgetItem(m.get("reference_type", "")))
                self.table.setItem(row, 5, QTableWidgetItem(m.get("notes", "")))
                self.table.setItem(row, 6, QTableWidgetItem(m.get("created_by_name", "")))
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
        self.table.setSortingEnabled(True)


class AnalyticsTab(QWidget):
    def __init__(self, inventory_service, auth_service):
        super().__init__()
        self.inv_service = inventory_service
        self.auth_service = auth_service
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        valuation_group = QGroupBox("Inventory Valuation")
        valuation_group.setStyleSheet(
            "QGroupBox { font-weight: bold; font-size: 14px; border: 1px solid #DEE2E6; "
            "border-radius: 6px; margin-top: 10px; padding-top: 20px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }"
        )
        vlayout = QHBoxLayout(valuation_group)

        self.lbl_cost_value = QLabel("Total Cost: --")
        self.lbl_cost_value.setStyleSheet("font-size: 18px; font-weight: bold; color: #DC3545; padding: 10px;")
        vlayout.addWidget(self.lbl_cost_value)

        self.lbl_retail_value = QLabel("Total Retail: --")
        self.lbl_retail_value.setStyleSheet("font-size: 18px; font-weight: bold; color: #28A745; padding: 10px;")
        vlayout.addWidget(self.lbl_retail_value)

        layout.addWidget(valuation_group)
        layout.addSpacing(16)

        fast_group = QGroupBox("Fast-Moving Products (Top 10)")
        fast_group.setStyleSheet(valuation_group.styleSheet())
        fv = QVBoxLayout(fast_group)

        self.fast_table = QTableWidget()
        _style_table(self.fast_table)
        self.fast_table.setColumnCount(4)
        self.fast_table.setHorizontalHeaderLabels(["Product", "Brand", "Units Sold", "Revenue"])
        self.fast_table.setColumnWidth(0, 250)
        self.fast_table.setColumnWidth(1, 150)
        self.fast_table.setColumnWidth(2, 100)
        self.fast_table.setColumnWidth(3, 150)
        fv.addWidget(self.fast_table)
        layout.addWidget(fast_group)
        layout.addSpacing(16)

        slow_group = QGroupBox("Slow-Moving Products (Bottom 10)")
        slow_group.setStyleSheet(valuation_group.styleSheet())
        sv = QVBoxLayout(slow_group)

        self.slow_table = QTableWidget()
        _style_table(self.slow_table)
        self.slow_table.setColumnCount(4)
        self.slow_table.setHorizontalHeaderLabels(["Product", "Brand", "Units Sold", "Revenue"])
        self.slow_table.setColumnWidth(0, 250)
        self.slow_table.setColumnWidth(1, 150)
        self.slow_table.setColumnWidth(2, 100)
        self.slow_table.setColumnWidth(3, 150)
        sv.addWidget(self.slow_table)
        layout.addWidget(slow_group)

    def _load_data(self):
        try:
            branch_id = self.auth_service.current_branch.id

            valuation = self.inv_service.get_inventory_valuation(branch_id)
            self.lbl_cost_value.setText(f"Total Cost: {format_currency(valuation['total_valuation'])}")
            total_retail = sum(
                item["quantity_on_hand"] * item["cost_price"] for item in valuation.get("items", [])
            )
            self.lbl_retail_value.setText(f"Total Retail: {format_currency(total_retail)}")

            self.fast_table.setSortingEnabled(False)
            self.fast_table.setRowCount(0)
            fast = self.inv_service.get_fast_moving(branch_id)
            for row, p in enumerate(fast):
                self.fast_table.insertRow(row)
                self.fast_table.setItem(row, 0, QTableWidgetItem(p["product_name"]))
                self.fast_table.setItem(row, 1, QTableWidgetItem(p.get("brand") or ""))
                self.fast_table.setItem(row, 2, QTableWidgetItem(str(int(p["total_qty"]))))
                self.fast_table.setItem(row, 3, QTableWidgetItem(format_currency(p["total_revenue"])))
            self.fast_table.setSortingEnabled(True)

            self.slow_table.setSortingEnabled(False)
            self.slow_table.setRowCount(0)
            slow = self.inv_service.get_slow_moving(branch_id)
            for row, p in enumerate(slow):
                self.slow_table.insertRow(row)
                self.slow_table.setItem(row, 0, QTableWidgetItem(p["product_name"]))
                self.slow_table.setItem(row, 1, QTableWidgetItem(p.get("brand") or ""))
                self.slow_table.setItem(row, 2, QTableWidgetItem(str(int(p["total_qty"]))))
                self.slow_table.setItem(row, 3, QTableWidgetItem(format_currency(p["total_revenue"])))
            self.slow_table.setSortingEnabled(True)

        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))


class InventoryScreen(QWidget):
    def __init__(self, inventory_service=None, auth_service=None, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service or AuthService()
        self.inv_service = inventory_service or InventoryService()
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

        self.tabs.addTab(ProductsTab(self.inv_service, self.auth_service), "Products")
        self.tabs.addTab(StockTab(self.inv_service, self.auth_service), "Stock")
        self.tabs.addTab(MovementsTab(self.inv_service, self.auth_service), "Movements")
        self.tabs.addTab(AnalyticsTab(self.inv_service, self.auth_service), "Analytics")

        layout.addWidget(self.tabs)

    def refresh(self):
        idx = self.tabs.currentIndex()
        widget = self.tabs.widget(idx)
        if hasattr(widget, "_load_inventory"):
            widget._load_inventory()
        elif hasattr(widget, "_load_products"):
            widget._load_products()
        elif hasattr(widget, "_load_movements"):
            widget._load_movements()
        elif hasattr(widget, "_load_data"):
            widget._load_data()
