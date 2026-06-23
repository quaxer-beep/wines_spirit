import os
from datetime import datetime
from pathlib import Path

from src.config.logging_config import setup_logging
from src.config.settings import settings
from src.utils.helpers import format_currency

logger = setup_logging(__name__)


class ReceiptService:
    def __init__(self):
        self.settings = settings

    def _get_width(self) -> int:
        printer = self.settings.PRINTER_DEFAULT or "58mm"
        if printer == "80mm":
            return self.settings.PRINTER_WIDTH_80MM or 48
        return self.settings.PRINTER_WIDTH_58MM or 32

    def _center(self, text: str, width: int) -> str:
        return text.center(width)

    def _left_right(self, left: str, right: str, width: int) -> str:
        left = str(left)
        right = str(right)
        dots = width - len(left) - len(right)
        if dots < 1:
            return left[:width]
        return f"{left}{'.' * dots}{right}"

    def _line(self, char: str = "-", width: int | None = None) -> str:
        w = width or self._get_width()
        return char * w

    def generate_receipt_text(self, sale, branch, company_name: str | None = None) -> str:
        width = self._get_width()
        lines = []

        lines.append(self._line("=", width))
        lines.append("")
        lines.append(self._center(company_name or self.settings.COMPANY_NAME or "Wines & Spirits", width))
        tagline = self.settings.COMPANY_TAGLINE
        if tagline:
            lines.append(self._center(tagline, width))
        lines.append("")
        lines.append(self._line("-", width))

        lines.append(branch.name or "Branch")
        if branch.phone:
            lines.append(f"Tel: {branch.phone}")
        lines.append(self._line("-", width))

        lines.append(f"Receipt: {sale.receipt_number or 'N/A'}")
        created = sale.created_at
        if created:
            if isinstance(created, str):
                from datetime import datetime as dt
                try:
                    created = dt.fromisoformat(created)
                except (ValueError, TypeError):
                    created = datetime.now()
            lines.append(f"Date: {created.strftime('%d/%m/%Y')}  Time: {created.strftime('%H:%M:%S')}")
        else:
            now = datetime.now()
            lines.append(f"Date: {now.strftime('%d/%m/%Y')}  Time: {now.strftime('%H:%M:%S')}")
        if sale.user and sale.user.full_name:
            lines.append(f"Cashier: {sale.user.full_name}")
        lines.append(self._line("-", width))

        lines.append(f"{'Item':<{width - 14}}{'Qty':>4}{'Price':>10}")
        lines.append(self._line("-", width))

        for item in sale.items:
            name = (item.product.name if item.product else f"Item #{item.product_id}")[:width - 20]
            qty = f"{item.quantity:.1f}" if item.quantity != int(item.quantity) else str(int(item.quantity))
            price = format_currency(item.subtotal)
            lines.append(f"{name:<{width - 14}}{qty:>4}{price:>10}")

        lines.append(self._line("-", width))
        lines.append(self._left_right("Subtotal:", format_currency(sale.subtotal), width))
        if sale.discount > 0:
            lines.append(self._left_right("Discount:", format_currency(sale.discount), width))
        lines.append(self._left_right("VAT (16%):", format_currency(sale.tax), width))
        lines.append(self._left_right("Total:", format_currency(sale.grand_total), width))
        lines.append(self._line("-", width))

        method = sale.payment_method or "N/A"
        lines.append(f"Payment: {method}")
        for payment in sale.payments:
            if payment.mpesa_code:
                lines.append(f"M-PESA: {payment.mpesa_code}")

        lines.append(self._line("-", width))

        if sale.etims_invoice and sale.etims_invoice.qr_code:
            qr = sale.etims_invoice.qr_code
            max_qr_len = width - 4
            if len(qr) > max_qr_len:
                qr = qr[:max_qr_len]
            lines.append(f"  {qr}")

        footer = self.settings.RECEIPT_FOOTER or "Thank you for your purchase!"
        for f_line in footer.split("\n"):
            lines.append(self._center(f_line.strip(), width))

        lines.append(self._line("=", width))
        lines.append("")

        return "\n".join(lines)

    def print_receipt(self, receipt_text: str, printer_name: str | None = None) -> bool:
        receipts_dir = Path(self.settings.BASE_DIR) / "resources" / "receipts"
        receipts_dir.mkdir(parents=True, exist_ok=True)

        try:
            if os.name == "nt":
                import tempfile
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".txt", delete=False, dir=str(receipts_dir)
                ) as f:
                    f.write(receipt_text)
                    temp_path = f.name

                if printer_name:
                    result = os.system(f'print /D:"{printer_name}" "{temp_path}"')
                else:
                    result = os.system(f'print "{temp_path}"')

                try:
                    os.unlink(temp_path)
                except OSError:
                    pass

                if result == 0:
                    logger.info("Receipt sent to printer.")
                    return True
            else:
                cmd = f"lpr" if not printer_name else f'lpr -P "{printer_name}"'
                import subprocess
                proc = subprocess.Popen(
                    cmd.split(),
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                stdout, stderr = proc.communicate(input=receipt_text.encode())
                if proc.returncode == 0:
                    logger.info("Receipt sent to printer.")
                    return True
                else:
                    logger.warning("Printer command failed: %s", stderr.decode())
        except Exception as e:
            logger.warning("Printing failed: %s", e)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = receipts_dir / f"receipt_{timestamp}.txt"
        try:
            filepath.write_text(receipt_text, encoding="utf-8")
            logger.info("Receipt saved to file: %s", filepath)
        except Exception as e:
            logger.error("Failed to save receipt to file: %s", e)
            raise

        return False

    def save_receipt_html(self, sale, branch) -> str:
        width = self._get_width()
        created = sale.created_at
        if created and not isinstance(created, str):
            date_str = created.strftime("%d/%m/%Y")
            time_str = created.strftime("%H:%M:%S")
        else:
            now = datetime.now()
            date_str = now.strftime("%d/%m/%Y")
            time_str = now.strftime("%H:%M:%S")

        cashier = sale.user.full_name if sale.user else "N/A"
        items_html = ""
        for item in sale.items:
            name = item.product.name if item.product else f"Item #{item.product_id}"
            qty = f"{item.quantity:.1f}" if item.quantity != int(item.quantity) else str(int(item.quantity))
            price = format_currency(item.subtotal)
            items_html += f"<tr><td>{name}</td><td style='text-align:center'>{qty}</td><td style='text-align:right'>{price}</td></tr>\n"

        payments_html = ""
        for payment in sale.payments:
            ref = f" ({payment.mpesa_code})" if payment.mpesa_code else ""
            payments_html += f"<p>{payment.method}{ref}: {format_currency(payment.amount)}</p>\n"

        qr_html = ""
        if sale.etims_invoice and sale.etims_invoice.qr_code:
            qr_html = f"<p style='font-family:monospace;font-size:10px'>{sale.etims_invoice.qr_code}</p>"

        company = self.settings.COMPANY_NAME or "Wines & Spirits"
        tagline = self.settings.COMPANY_TAGLINE or ""
        footer = self.settings.RECEIPT_FOOTER or "Thank you for your purchase!"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Receipt - {sale.receipt_number}</title>
<style>
  body {{ font-family: 'Courier New', monospace; font-size: 12px; width: {width * 8}px; margin: 0 auto; }}
  table {{ width: 100%; border-collapse: collapse; }}
  td, th {{ padding: 2px 4px; }}
  .center {{ text-align: center; }}
  .right {{ text-align: right; }}
  .line {{ border-top: 1px dashed #000; }}
</style>
</head>
<body>
<div class="center">
  <h2 style="margin:0">{company}</h2>
  {f'<p style="margin:0">{tagline}</p>' if tagline else ''}
</div>
<hr>
<p>{branch.name}</p>
{f'<p>Tel: {branch.phone}</p>' if branch.phone else ''}
<hr>
<p>Receipt: {sale.receipt_number}</p>
<p>Date: {date_str} | Time: {time_str}</p>
<p>Cashier: {cashier}</p>
<hr>
<table>
  <tr><th>Item</th><th style='text-align:center'>Qty</th><th style='text-align:right'>Price</th></tr>
  {items_html}
</table>
<hr>
<table>
  <tr><td>Subtotal:</td><td class="right">{format_currency(sale.subtotal)}</td></tr>
  {f'<tr><td>Discount:</td><td class="right">{format_currency(sale.discount)}</td></tr>' if sale.discount > 0 else ''}
  <tr><td>VAT (16%):</td><td class="right">{format_currency(sale.tax)}</td></tr>
  <tr><td><strong>Total:</strong></td><td class="right"><strong>{format_currency(sale.grand_total)}</strong></td></tr>
</table>
<hr>
<div>{payments_html}</div>
<hr>
{qr_html}
<div class="center">
  {''.join(f'<p>{fl.strip()}</p>' for fl in footer.split('\\n'))}
</div>
</body>
</html>"""

        return html

    def generate_receipt_preview(self, sale, branch) -> dict:
        created = sale.created_at
        if created and not isinstance(created, str):
            date_str = created.strftime("%d/%m/%Y")
            time_str = created.strftime("%H:%M:%S")
        else:
            now = datetime.now()
            date_str = now.strftime("%d/%m/%Y")
            time_str = now.strftime("%H:%M:%S")

        items = []
        for item in sale.items:
            items.append({
                "product_name": item.product.name if item.product else f"Item #{item.product_id}",
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "subtotal": item.subtotal,
            })

        payments = []
        for payment in sale.payments:
            payments.append({
                "method": payment.method,
                "amount": payment.amount,
                "reference": payment.reference,
                "mpesa_code": payment.mpesa_code,
            })

        return {
            "company_name": self.settings.COMPANY_NAME or "Wines & Spirits",
            "company_tagline": self.settings.COMPANY_TAGLINE or "",
            "branch_name": branch.name,
            "branch_phone": branch.phone,
            "receipt_number": sale.receipt_number,
            "date": date_str,
            "time": time_str,
            "cashier": sale.user.full_name if sale.user else "N/A",
            "items": items,
            "subtotal": sale.subtotal,
            "discount": sale.discount,
            "tax": sale.tax,
            "grand_total": sale.grand_total,
            "payment_method": sale.payment_method or "N/A",
            "payments": payments,
            "qr_code": sale.etims_invoice.qr_code if sale.etims_invoice else None,
            "footer": self.settings.RECEIPT_FOOTER or "Thank you for your purchase!",
        }
