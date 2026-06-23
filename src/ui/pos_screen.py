import logging

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QBrush
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView,
    QPushButton, QLabel, QComboBox, QSpinBox,
    QGroupBox, QFormLayout, QStackedWidget, QTextEdit,
    QMessageBox, QDoubleSpinBox,
)

from src.services.pos_service import PosService
from src.services.auth_service import AuthService
from src.services.mpesa_service import MpesaService
from src.services.receipt_service import ReceiptService
from src.utils.helpers import format_currency
from src.utils.validators import sanitize_phone
from src.utils.exceptions import (
    InsufficientStockError,
    PaymentError,
    ValidationError,
    MpesaError,
)

logger = logging.getLogger(__name__)

CLR_GREEN_DARK = "#27AE60"
CLR_GREEN_BRIGHT = "#2ECC71"
CLR_MUTED = "#95A5A6"
CLR_RED = "#E74C3C"
CLR_LIGHT_GRAY = "#F8F9FA"


class _Obj:
    pass


def _sale_dict_to_obj(sale_dict):
    s = _Obj()
    s.id = sale_dict["id"]
    s.receipt_number = sale_dict.get("receipt_number")
    s.created_at = sale_dict.get("created_at")
    s.subtotal = sale_dict.get("subtotal", 0)
    s.discount = sale_dict.get("discount", 0)
    s.tax = sale_dict.get("tax", 0)
    s.grand_total = sale_dict.get("grand_total", 0)
    s.payment_method = sale_dict.get("payment_method", "CASH")
    s.status = sale_dict.get("status", "COMPLETED")
    s.voided = sale_dict.get("voided", 0)
    s.void_reason = sale_dict.get("void_reason")

    user = _Obj()
    user.full_name = sale_dict.get("cashier_name", "")
    s.user = user

    s.items = []
    for item_dict in sale_dict.get("items", []):
        item = _Obj()
        item.id = item_dict.get("id")
        item.product_id = item_dict.get("product_id")
        item.quantity = item_dict.get("quantity", 0)
        item.unit_price = item_dict.get("unit_price", 0)
        item.subtotal = item_dict.get("subtotal", 0)
        prod = _Obj()
        prod.name = item_dict.get("product_name", "")
        item.product = prod
        s.items.append(item)

    s.payments = []
    for pmt_dict in sale_dict.get("payments", []):
        pmt = _Obj()
        pmt.method = pmt_dict.get("method", "CASH")
        pmt.amount = pmt_dict.get("amount", 0)
        pmt.reference = pmt_dict.get("reference")
        pmt.mpesa_code = pmt_dict.get("mpesa_code")
        s.payments.append(pmt)

    s.etims_invoice = None
    return s


class PosScreen(QWidget):
    def __init__(self, pos_service=None, auth_service=None,
                 mpesa_service=None, receipt_service=None, parent=None):
        super().__init__(parent)
        self.pos_service = pos_service or PosService()
        self.auth_service = auth_service or AuthService()
        self.mpesa_service = mpesa_service or MpesaService()
        self.receipt_service = receipt_service or ReceiptService()

        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._execute_search)

        self._mpesa_poll_timer = QTimer(self)
        self._mpesa_poll_timer.timeout.connect(self._poll_mpesa_status)
        self._checkout_request_id = None
        self._mpesa_verified = False
        self._mpesa_amount = 0.0

        self.cart_items = []
        self._current_sale = None
        self._receipt_text = None
        self._receipt_raw = None

        self._build_ui()
        self._apply_styles()
        self._connect_signals()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._stack = QStackedWidget()
        main_layout.addWidget(self._stack)

        self._pos_page = self._build_pos_page()
        self._stack.addWidget(self._pos_page)

        self._receipt_page = self._build_receipt_page()
        self._stack.addWidget(self._receipt_page)

        self._stack.setCurrentIndex(0)

    def _build_pos_page(self):
        page = QWidget()
        page.setObjectName("posPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        hsplit = QSplitter(Qt.Orientation.Horizontal)
        hsplit.setHandleWidth(1)
        layout.addWidget(hsplit)

        left = QWidget()
        left.setObjectName("leftPanel")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(10)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search product by name or scan barcode...")
        self._search_input.setClearButtonEnabled(True)
        font_large = QFont()
        font_large.setPointSize(14)
        self._search_input.setFont(font_large)
        self._search_input.setMinimumHeight(44)
        left_layout.addWidget(self._search_input)

        self._results_table = QTableWidget()
        self._results_table.setColumnCount(3)
        self._results_table.setHorizontalHeaderLabels(["Product", "Price", "Stock"])
        self._results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._results_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._results_table.verticalHeader().setVisible(False)
        self._results_table.setAlternatingRowColors(True)
        hdr = self._results_table.horizontalHeader()
        hdr.setStretchLastSection(False)
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._results_table.setMaximumHeight(320)
        left_layout.addWidget(self._results_table)

        cart_label = QLabel("<b>Cart</b>")
        cart_label.setStyleSheet("font-size: 14px;")
        left_layout.addWidget(cart_label)

        self._cart_table = QTableWidget()
        self._cart_table.setColumnCount(5)
        self._cart_table.setHorizontalHeaderLabels(["Product", "Qty", "Price", "Subtotal", ""])
        self._cart_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._cart_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._cart_table.verticalHeader().setVisible(False)
        self._cart_table.setAlternatingRowColors(True)
        chdr = self._cart_table.horizontalHeader()
        chdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        chdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        chdr.resizeSection(1, 72)
        chdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        chdr.resizeSection(2, 100)
        chdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        chdr.resizeSection(3, 110)
        chdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        chdr.resizeSection(4, 44)
        left_layout.addWidget(self._cart_table, stretch=1)

        right = QWidget()
        right.setObjectName("rightPanel")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(12)

        self._build_totals_section(right_layout)
        self._build_payment_section(right_layout)
        self._build_action_buttons(right_layout)
        right_layout.addStretch()

        hsplit.addWidget(left)
        hsplit.addWidget(right)
        hsplit.setSizes([600, 400])

        return page

    def _build_totals_section(self, parent_layout):
        group = QGroupBox("Totals")
        group.setObjectName("totalsGroup")
        gl = QVBoxLayout(group)
        gl.setSpacing(6)

        self._lbl_subtotal = QLabel("KES 0.00")
        self._lbl_subtotal.setStyleSheet("font-size: 16px;")
        self._lbl_vat = QLabel("KES 0.00")
        self._lbl_vat.setStyleSheet("font-size: 16px;")
        self._lbl_grand_total = QLabel("KES 0.00")
        self._lbl_grand_total.setStyleSheet(
            f"font-size: 28px; font-weight: bold; color: {CLR_GREEN_DARK};"
        )

        gl.addWidget(QLabel("Subtotal:"))
        gl.addWidget(self._lbl_subtotal)
        gl.addWidget(QLabel("VAT (16%):"))
        gl.addWidget(self._lbl_vat)
        gl.addSpacing(8)
        gl.addWidget(QLabel("<b>Grand Total:</b>"))
        gl.addWidget(self._lbl_grand_total)

        parent_layout.addWidget(group)

    def _build_payment_section(self, parent_layout):
        group = QGroupBox("Payment")
        group.setObjectName("paymentGroup")
        gl = QVBoxLayout(group)
        gl.setSpacing(8)

        method_row = QHBoxLayout()
        method_row.addWidget(QLabel("Method:"))
        self._cmb_payment_method = QComboBox()
        self._cmb_payment_method.addItems(["Cash", "M-Pesa", "Mixed"])
        self._cmb_payment_method.setMinimumHeight(36)
        method_row.addWidget(self._cmb_payment_method, stretch=1)
        gl.addLayout(method_row)

        self._payment_stack = QStackedWidget()
        self._payment_stack.addWidget(self._build_cash_form())
        self._payment_stack.addWidget(self._build_mpesa_form())
        self._payment_stack.addWidget(self._build_mixed_form())
        gl.addWidget(self._payment_stack)

        parent_layout.addWidget(group)

    def _build_cash_form(self):
        w = QWidget()
        layout = QFormLayout(w)
        layout.setSpacing(8)

        self._cash_received = QDoubleSpinBox()
        self._cash_received.setPrefix("KES ")
        self._cash_received.setMaximum(9999999.99)
        self._cash_received.setDecimals(2)
        self._cash_received.setMinimumHeight(36)
        self._cash_received.setStyleSheet("font-size: 14px;")
        layout.addRow("Amount Received:", self._cash_received)

        self._lbl_change = QLabel("Change: KES 0.00")
        self._lbl_change.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {CLR_GREEN_DARK};"
        )
        layout.addRow(self._lbl_change)
        return w

    def _build_mpesa_form(self):
        w = QWidget()
        layout = QFormLayout(w)
        layout.setSpacing(8)

        self._mpesa_phone = QLineEdit()
        self._mpesa_phone.setPlaceholderText("e.g. 0712345678")
        self._mpesa_phone.setMinimumHeight(36)
        self._mpesa_phone.setStyleSheet("font-size: 14px;")
        layout.addRow("Phone Number:", self._mpesa_phone)

        btn_row = QHBoxLayout()
        self._btn_stk_push = QPushButton("Send STK Push")
        self._btn_stk_push.setMinimumHeight(40)
        self._btn_stk_push.setStyleSheet(
            f"background-color: {CLR_GREEN_BRIGHT}; color: white; "
            f"font-weight: bold; font-size: 14px; border-radius: 6px;"
        )
        btn_row.addWidget(self._btn_stk_push)

        self._lbl_mpesa_status = QLabel("")
        self._lbl_mpesa_status.setWordWrap(True)
        self._lbl_mpesa_status.setStyleSheet("font-size: 13px; padding: 4px;")
        btn_row.addWidget(self._lbl_mpesa_status, stretch=1)
        layout.addRow(btn_row)

        return w

    def _build_mixed_form(self):
        w = QWidget()
        layout = QFormLayout(w)
        layout.setSpacing(8)

        self._mixed_cash = QDoubleSpinBox()
        self._mixed_cash.setPrefix("KES ")
        self._mixed_cash.setMaximum(9999999.99)
        self._mixed_cash.setDecimals(2)
        self._mixed_cash.setMinimumHeight(36)
        layout.addRow("Cash Amount:", self._mixed_cash)

        self._mixed_mpesa = QDoubleSpinBox()
        self._mixed_mpesa.setPrefix("KES ")
        self._mixed_mpesa.setMaximum(9999999.99)
        self._mixed_mpesa.setDecimals(2)
        self._mixed_mpesa.setMinimumHeight(36)
        self._mixed_mpesa.setReadOnly(True)
        layout.addRow("M-Pesa Amount:", self._mixed_mpesa)

        self._mixed_phone = QLineEdit()
        self._mixed_phone.setPlaceholderText("e.g. 0712345678")
        self._mixed_phone.setMinimumHeight(36)
        layout.addRow("M-Pesa Phone:", self._mixed_phone)

        btn_row = QHBoxLayout()
        self._btn_mixed_stk = QPushButton("Send STK Push")
        self._btn_mixed_stk.setMinimumHeight(36)
        self._btn_mixed_stk.setStyleSheet(
            f"background-color: {CLR_GREEN_BRIGHT}; color: white; "
            f"font-weight: bold; border-radius: 6px;"
        )
        btn_row.addWidget(self._btn_mixed_stk)

        self._lbl_mixed_status = QLabel("")
        self._lbl_mixed_status.setWordWrap(True)
        btn_row.addWidget(self._lbl_mixed_status, stretch=1)
        layout.addRow(btn_row)

        return w

    def _build_action_buttons(self, parent_layout):
        self._btn_complete = QPushButton("Complete Sale")
        self._btn_complete.setMinimumHeight(52)
        self._btn_complete.setEnabled(False)
        self._btn_complete.setStyleSheet(
            f"background-color: {CLR_GREEN_BRIGHT}; color: white; "
            f"font-size: 18px; font-weight: bold; border-radius: 8px;"
        )
        parent_layout.addWidget(self._btn_complete)

        self._btn_clear = QPushButton("Clear Cart")
        self._btn_clear.setMinimumHeight(40)
        self._btn_clear.setStyleSheet(
            f"background-color: {CLR_MUTED}; color: white; "
            f"font-size: 14px; font-weight: bold; border-radius: 6px;"
        )
        parent_layout.addWidget(self._btn_clear)

    def _build_receipt_page(self):
        page = QWidget()
        page.setObjectName("receiptPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        heading = QLabel("<h2>Sale Complete</h2>")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(heading)

        self._receipt_view = QTextEdit()
        self._receipt_view.setReadOnly(True)
        font_mono = QFont("Courier New", 10)
        self._receipt_view.setFont(font_mono)
        self._receipt_view.setStyleSheet(
            "background-color: white; border: 1px solid #ddd; padding: 12px;"
        )
        layout.addWidget(self._receipt_view, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(16)

        self._btn_print = QPushButton("Print Receipt")
        self._btn_print.setMinimumHeight(48)
        self._btn_print.setStyleSheet(
            f"background-color: {CLR_GREEN_BRIGHT}; color: white; "
            f"font-size: 16px; font-weight: bold; border-radius: 8px;"
        )
        btn_row.addWidget(self._btn_print, stretch=1)

        self._btn_new_sale = QPushButton("New Sale")
        self._btn_new_sale.setMinimumHeight(48)
        self._btn_new_sale.setStyleSheet(
            "background-color: #3498DB; color: white; "
            "font-size: 16px; font-weight: bold; border-radius: 8px;"
        )
        btn_row.addWidget(self._btn_new_sale, stretch=1)

        layout.addLayout(btn_row)
        return page

    def _apply_styles(self):
        self.setStyleSheet("""
            #posPage { background-color: white; }
            #leftPanel { background-color: white; }
            #rightPanel { background-color: #F8F9FA; }
            #receiptPage { background-color: #F8F9FA; }
            #totalsGroup, #paymentGroup {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 16px;
                font-size: 14px;
            }
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                gridline-color: #eee;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 6px;
                border: none;
                border-bottom: 2px solid #ddd;
                font-weight: bold;
                font-size: 13px;
            }
            QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox {
                border: 1px solid #ccc;
                border-radius: 6px;
                padding: 6px 10px;
            }
            QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {
                border-color: #2ECC71;
            }
        """)

    # ------------------------------------------------------------------
    # Signal Connections
    # ------------------------------------------------------------------

    def _connect_signals(self):
        self._search_input.textChanged.connect(self._on_search_text_changed)
        self._results_table.cellClicked.connect(self._on_result_clicked)
        self._cmb_payment_method.currentIndexChanged.connect(self._on_payment_method_changed)
        self._cash_received.valueChanged.connect(self._on_cash_received_changed)
        self._mixed_cash.valueChanged.connect(self._on_mixed_amounts_changed)
        self._btn_stk_push.clicked.connect(self._on_send_stk_push)
        self._btn_mixed_stk.clicked.connect(self._on_send_mixed_stk_push)
        self._btn_complete.clicked.connect(self._on_complete_sale)
        self._btn_clear.clicked.connect(self._on_clear_cart)
        self._btn_print.clicked.connect(self._on_print_receipt)
        self._btn_new_sale.clicked.connect(self._on_new_sale)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def _on_search_text_changed(self, text):
        self._debounce_timer.stop()
        if text.strip():
            self._debounce_timer.start(300)
        else:
            self._results_table.setRowCount(0)

    def _execute_search(self):
        query = self._search_input.text().strip()
        if not query:
            self._results_table.setRowCount(0)
            return
        branch = self.auth_service.current_branch
        if not branch:
            return
        try:
            results = self.pos_service.search_products_for_pos(query, branch.id, limit=20)
            self._display_results(results)
        except Exception as e:
            logger.warning("Product search failed: %s", e)

    def _display_results(self, products):
        self._results_table.setRowCount(0)
        for product in products:
            row = self._results_table.rowCount()
            self._results_table.insertRow(row)

            name_item = QTableWidgetItem(product["name"])
            name_item.setData(Qt.ItemDataRole.UserRole, product)
            if product["quantity_on_hand"] <= 0:
                name_item.setForeground(QBrush(QColor(CLR_MUTED)))
            self._results_table.setItem(row, 0, name_item)

            price_item = QTableWidgetItem(format_currency(product["selling_price"]))
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if product["quantity_on_hand"] <= 0:
                price_item.setForeground(QBrush(QColor(CLR_MUTED)))
            self._results_table.setItem(row, 1, price_item)

            stock = product["quantity_on_hand"]
            stock_text = f"{stock:.0f}" if stock == int(stock) else f"{stock:.1f}"
            stock_item = QTableWidgetItem(stock_text)
            stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if stock <= 0:
                stock_item.setForeground(QBrush(QColor(CLR_RED)))
                stock_item.setText("Out of Stock")
            elif stock <= 5:
                stock_item.setForeground(QBrush(QColor("#E67E22")))
            self._results_table.setItem(row, 2, stock_item)

    def _on_result_clicked(self, row, _col):
        item = self._results_table.item(row, 0)
        if not item:
            return
        product = item.data(Qt.ItemDataRole.UserRole)
        if product and product["quantity_on_hand"] > 0:
            self._add_to_cart(product)

    # ------------------------------------------------------------------
    # Cart Operations
    # ------------------------------------------------------------------

    def _add_to_cart(self, product):
        existing = next(
            (c for c in self.cart_items if c["product_id"] == product["id"]),
            None,
        )
        if existing:
            max_stock = int(product["quantity_on_hand"])
            if existing["quantity"] < max_stock:
                existing["quantity"] += 1
            else:
                QMessageBox.information(
                    self, "Stock Limit",
                    f"Cannot add more '{product['name']}'. Only {max_stock} available.",
                )
        else:
            self.cart_items.append({
                "product_id": product["id"],
                "name": product["name"],
                "unit_price": product["selling_price"],
                "quantity": 1,
                "max_qty": int(product["quantity_on_hand"]),
            })
        self._refresh_cart()
        self._search_input.clear()
        self._results_table.setRowCount(0)

    def _refresh_cart(self):
        self._cart_table.setRowCount(0)
        for idx, item in enumerate(self.cart_items):
            row = self._cart_table.rowCount()
            self._cart_table.insertRow(row)
            self._cart_table.setRowHeight(row, 36)

            name_item = QTableWidgetItem(item["name"])
            name_item.setData(Qt.ItemDataRole.UserRole, item["product_id"])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._cart_table.setItem(row, 0, name_item)

            spin = QSpinBox()
            spin.setMinimum(1)
            spin.setMaximum(max(item["max_qty"], 1))
            spin.setValue(item["quantity"])
            spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
            spin.valueChanged.connect(
                lambda val, idx=i: self._on_qty_changed(idx, val)
            )
            self._cart_table.setCellWidget(row, 1, spin)

            price_item = QTableWidgetItem(format_currency(item["unit_price"]))
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            price_item.setFlags(price_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._cart_table.setItem(row, 2, price_item)

            sub = item["quantity"] * item["unit_price"]
            sub_item = QTableWidgetItem(format_currency(sub))
            sub_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            sub_item.setFlags(sub_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._cart_table.setItem(row, 3, sub_item)

            btn_remove = QPushButton("✕")
            btn_remove.setFixedSize(32, 32)
            btn_remove.setStyleSheet(
                f"background-color: {CLR_RED}; color: white; "
                f"font-weight: bold; border-radius: 16px; border: none;"
            )
            btn_remove.clicked.connect(
                lambda checked, idx=i: self._remove_cart_item(idx)
            )
            self._cart_table.setCellWidget(row, 4, btn_remove)

        self._update_totals()
        self._btn_complete.setEnabled(len(self.cart_items) > 0)

    def _on_qty_changed(self, index, value):
        if 0 <= index < len(self.cart_items):
            self.cart_items[index]["quantity"] = value
            self._update_totals()

    def _remove_cart_item(self, index):
        if 0 <= index < len(self.cart_items):
            del self.cart_items[index]
            self._refresh_cart()

    # ------------------------------------------------------------------
    # Totals
    # ------------------------------------------------------------------

    def _update_totals(self):
        subtotal = sum(item["quantity"] * item["unit_price"] for item in self.cart_items)
        subtotal = round(subtotal, 2)
        vat = round(subtotal * 0.16, 2)
        grand_total = round(subtotal + vat, 2)

        self._lbl_subtotal.setText(format_currency(subtotal))
        self._lbl_vat.setText(format_currency(vat))
        self._lbl_grand_total.setText(format_currency(grand_total))

        self._on_cash_received_changed()
        self._on_mixed_amounts_changed()

    def _grand_total(self) -> float:
        subtotal = sum(item["quantity"] * item["unit_price"] for item in self.cart_items)
        return round(subtotal * 1.16, 2)

    # ------------------------------------------------------------------
    # Payment Handlers
    # ------------------------------------------------------------------

    def _on_payment_method_changed(self, index):
        self._payment_stack.setCurrentIndex(index)
        self._reset_mpesa_state()

    def _on_cash_received_changed(self):
        total = self._grand_total()
        received = self._cash_received.value()
        change = max(0.0, received - total)
        self._lbl_change.setText(f"Change: {format_currency(change)}")

    def _on_mixed_amounts_changed(self):
        total = self._grand_total()
        cash_val = self._mixed_cash.value()
        remaining = max(0.0, total - cash_val)
        self._mixed_mpesa.setValue(remaining)

    # ------------------------------------------------------------------
    # M-Pesa STK Push
    # ------------------------------------------------------------------

    def _reset_mpesa_state(self):
        self._mpesa_poll_timer.stop()
        self._checkout_request_id = None
        self._mpesa_verified = False
        self._mpesa_amount = 0.0
        self._lbl_mpesa_status.setText("")
        self._lbl_mixed_status.setText("")
        self._btn_stk_push.setEnabled(True)
        self._btn_mixed_stk.setEnabled(True)

    def _on_send_stk_push(self):
        phone = self._mpesa_phone.text().strip()
        amount = self._grand_total()
        if amount <= 0:
            QMessageBox.warning(self, "Invalid Amount", "Cart total must be greater than 0.")
            return
        self._initiate_stk_push(phone, amount, self._lbl_mpesa_status, self._btn_stk_push)

    def _on_send_mixed_stk_push(self):
        phone = self._mixed_phone.text().strip()
        amount = self._mixed_mpesa.value()
        if amount <= 0:
            QMessageBox.warning(self, "Invalid Amount", "M-Pesa amount must be greater than 0.")
            return
        self._initiate_stk_push(phone, amount, self._lbl_mixed_status, self._btn_mixed_stk)

    def _initiate_stk_push(self, phone, amount, status_label, button):
        try:
            sanitize_phone(phone)
        except ValidationError as e:
            QMessageBox.warning(self, "Invalid Phone", str(e))
            return

        status_label.setText("Sending STK Push...")
        status_label.setStyleSheet("color: #555; font-size: 13px; padding: 4px;")
        button.setEnabled(False)

        try:
            result = self.mpesa_service.stk_push(
                phone=phone,
                amount=amount,
                account_reference="POS-SALE",
                transaction_desc="Wines & Spirits POS",
            )
            self._checkout_request_id = result["checkout_request_id"]
            self._mpesa_amount = amount
            self._mpesa_verified = False
            status_label.setText("STK Push sent! Enter PIN on your phone...")
            status_label.setStyleSheet(
                "color: #E67E22; font-weight: bold; font-size: 13px; padding: 4px;"
            )
            self._mpesa_poll_timer.start(3000)
        except MpesaError as e:
            status_label.setText(f"STK Push failed: {e}")
            status_label.setStyleSheet(f"color: {CLR_RED}; font-size: 13px; padding: 4px;")
            button.setEnabled(True)
        except Exception as e:
            logger.exception("STK Push error")
            status_label.setText(f"Error: {e}")
            status_label.setStyleSheet(f"color: {CLR_RED}; font-size: 13px; padding: 4px;")
            button.setEnabled(True)

    def _poll_mpesa_status(self):
        if not self._checkout_request_id or self._mpesa_verified:
            return
        try:
            verified = self.mpesa_service.verify_payment(
                self._checkout_request_id, self._mpesa_amount,
            )
            if verified:
                self._mpesa_verified = True
                self._mpesa_poll_timer.stop()
                msg = "Payment Verified \u2713"
                style = (
                    f"color: {CLR_GREEN_DARK}; font-weight: bold; "
                    f"font-size: 13px; padding: 4px;"
                )
                self._lbl_mpesa_status.setText(msg)
                self._lbl_mpesa_status.setStyleSheet(style)
                self._lbl_mixed_status.setText(msg)
                self._lbl_mixed_status.setStyleSheet(style)
        except Exception as e:
            logger.debug("M-Pesa poll check: %s", e)

    # ------------------------------------------------------------------
    # Complete Sale
    # ------------------------------------------------------------------

    def _on_complete_sale(self):
        if not self.cart_items:
            QMessageBox.warning(self, "Empty Cart", "Add items to the cart before completing sale.")
            return

        method_idx = self._cmb_payment_method.currentIndex()
        method_map = {0: "CASH", 1: "MPESA", 2: "MIXED"}
        method = method_map[method_idx]
        grand_total = self._grand_total()

        if method == "MPESA" and not self._mpesa_verified:
            QMessageBox.warning(
                self, "M-Pesa Not Verified",
                "Please send STK Push and verify payment before completing the sale.",
            )
            return

        if method == "MIXED":
            cash_amt = self._mixed_cash.value()
            mpesa_amt = self._mixed_mpesa.value()
            if mpesa_amt > 0 and not self._mpesa_verified:
                QMessageBox.warning(
                    self, "M-Pesa Not Verified",
                    "Please send STK Push and verify the M-Pesa portion before completing.",
                )
                return
            if abs(cash_amt + mpesa_amt - grand_total) > 0.01:
                QMessageBox.warning(
                    self, "Amount Mismatch",
                    f"Payment amounts ({format_currency(cash_amt + mpesa_amt)}) "
                    f"do not match grand total ({format_currency(grand_total)}).",
                )
                return

        self._set_processing(True)

        try:
            user = self.auth_service.current_user
            branch = self.auth_service.current_branch
            if not user or not branch:
                QMessageBox.critical(self, "Not Logged In", "Please log in first.")
                self._set_processing(False)
                return

            payment_data = self._build_payment_data(method, grand_total)
            cart_items_data = [
                {
                    "product_id": item["product_id"],
                    "quantity": item["quantity"],
                    "unit_price": item["unit_price"],
                }
                for item in self.cart_items
            ]

            sale = self.pos_service.create_sale(
                user=user,
                branch_id=branch.id,
                cart_items=cart_items_data,
                payment_data=payment_data,
            )

            self._current_sale = sale
            self._show_receipt(sale, branch)
        except InsufficientStockError as e:
            QMessageBox.warning(self, "Insufficient Stock", str(e))
        except ValidationError as e:
            QMessageBox.warning(self, "Validation Error", str(e))
        except PaymentError as e:
            QMessageBox.warning(self, "Payment Error", str(e))
        except Exception as e:
            logger.exception("Sale creation failed")
            QMessageBox.critical(self, "Error", f"An unexpected error occurred:\n{e}")
        finally:
            self._set_processing(False)

    def _build_payment_data(self, method, grand_total):
        if method == "CASH":
            return {
                "method": "CASH",
                "amount": self._cash_received.value(),
            }
        elif method == "MPESA":
            return {
                "method": "MPESA",
                "amount": grand_total,
                "reference": self._mpesa_phone.text().strip(),
                "mpesa_code": self._checkout_request_id,
            }
        elif method == "MIXED":
            cash_amt = self._mixed_cash.value()
            mpesa_amt = self._mixed_mpesa.value()
            payments = []
            if cash_amt > 0:
                payments.append({"method": "CASH", "amount": cash_amt})
            if mpesa_amt > 0:
                payments.append({
                    "method": "MPESA",
                    "amount": mpesa_amt,
                    "reference": self._mixed_phone.text().strip(),
                    "mpesa_code": self._checkout_request_id,
                })
            return {"method": "MIXED", "payments": payments}

    def _set_processing(self, busy):
        self._btn_complete.setEnabled(not busy and len(self.cart_items) > 0)
        self._btn_clear.setEnabled(not busy)
        self._search_input.setEnabled(not busy)
        self._btn_stk_push.setEnabled(not busy)
        self._btn_mixed_stk.setEnabled(not busy)
        self._cmb_payment_method.setEnabled(not busy)
        self._cash_received.setEnabled(not busy)
        self._mpesa_phone.setEnabled(not busy)
        self._mixed_cash.setEnabled(not busy)
        self._mixed_phone.setEnabled(not busy)
        self._results_table.setEnabled(not busy)
        if busy:
            self._btn_complete.setText("Processing...")
        else:
            self._btn_complete.setText("Complete Sale")

    # ------------------------------------------------------------------
    # Receipt
    # ------------------------------------------------------------------

    def _show_receipt(self, sale_dict, branch):
        try:
            sale_obj = _sale_dict_to_obj(sale_dict)
            self._receipt_raw = self.receipt_service.generate_receipt_text(
                sale_obj, branch, company_name=None,
            )
            preview = self.receipt_service.generate_receipt_preview(sale_obj, branch)

            lines = [
                f"{'=' * 42}",
                f"  {preview['company_name']}",
            ]
            if preview.get("company_tagline"):
                lines.append(f"  {preview['company_tagline']}")
            lines.append(f"{'-' * 42}")
            lines.append(f"  {preview['branch_name']}")
            if preview.get("branch_phone"):
                lines.append(f"  Tel: {preview['branch_phone']}")
            lines.append(f"{'-' * 42}")
            lines.append(f"  Receipt: {preview['receipt_number']}")
            lines.append(f"  Date: {preview['date']}  Time: {preview['time']}")
            lines.append(f"  Cashier: {preview['cashier']}")
            lines.append(f"{'-' * 42}")
            lines.append(f"  {'Item':<22}{'Qty':>4}{'Price':>10}")
            lines.append(f"{'-' * 42}")
            for item in preview["items"]:
                name = item["product_name"][:22]
                qty = (
                    f"{item['quantity']:.0f}"
                    if item["quantity"] == int(item["quantity"])
                    else f"{item['quantity']:.1f}"
                )
                price = format_currency(item["subtotal"])
                lines.append(f"  {name:<22}{qty:>4}{price:>10}")
            lines.append(f"{'-' * 42}")
            lines.append(
                f"  {'Subtotal:':<20}{format_currency(preview['subtotal']):>16}"
            )
            if preview.get("discount", 0) > 0:
                lines.append(
                    f"  {'Discount:':<20}{format_currency(preview['discount']):>16}"
                )
            lines.append(
                f"  {'VAT (16%):':<20}{format_currency(preview['tax']):>16}"
            )
            lines.append(
                f"  {'Total:':<20}{format_currency(preview['grand_total']):>16}"
            )
            lines.append(f"{'-' * 42}")
            lines.append(f"  Payment: {preview['payment_method']}")
            for pmt in preview.get("payments", []):
                if pmt.get("mpesa_code"):
                    lines.append(f"  M-PESA: {pmt['mpesa_code']}")
            lines.append(f"{'-' * 42}")
            if preview.get("footer"):
                for fl in preview["footer"].split("\n"):
                    lines.append(f"  {fl.strip()}")
            lines.append(f"{'=' * 42}")

            self._receipt_view.setPlainText("\n".join(lines))
            self._stack.setCurrentIndex(1)

            self._auto_print_receipt()
        except Exception as e:
            logger.exception("Failed to generate receipt preview")
            self._receipt_view.setPlainText(
                f"Sale completed successfully.\n"
                f"Receipt #{sale_dict.get('receipt_number', 'N/A')}\n"
                f"Total: {format_currency(sale_dict.get('grand_total', 0))}"
            )
            self._stack.setCurrentIndex(1)

    def _auto_print_receipt(self):
        if not self._receipt_raw:
            return
        try:
            self.receipt_service.print_receipt(self._receipt_raw)
        except Exception as e:
            logger.warning("Auto-print failed: %s", e)

    def _on_print_receipt(self):
        if not self._receipt_raw:
            return
        try:
            self.receipt_service.print_receipt(self._receipt_raw)
            QMessageBox.information(self, "Print", "Receipt sent to printer.")
        except Exception as e:
            QMessageBox.warning(self, "Print Error", f"Printing failed:\n{e}")

    def _on_new_sale(self):
        self.cart_items.clear()
        self._current_sale = None
        self._receipt_text = None
        self._receipt_raw = None
        self._receipt_view.clear()
        self._reset_mpesa_state()
        self._cash_received.setValue(0.0)
        self._mixed_cash.setValue(0.0)
        self._mpesa_phone.clear()
        self._mixed_phone.clear()
        self._search_input.clear()
        self._results_table.setRowCount(0)
        self._refresh_cart()
        self._cmb_payment_method.setCurrentIndex(0)
        self._stack.setCurrentIndex(0)

    def _on_clear_cart(self):
        if not self.cart_items:
            return
        reply = QMessageBox.question(
            self, "Clear Cart",
            "Remove all items from the cart?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.cart_items.clear()
            self._refresh_cart()
            self._reset_mpesa_state()
