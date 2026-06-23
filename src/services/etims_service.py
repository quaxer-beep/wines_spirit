import json
from datetime import datetime

import httpx

from src.config.logging_config import setup_logging
from src.config.settings import settings
from src.database.connection import db_manager
from src.database.models import EtimsInvoice
from src.utils.exceptions import EtimsError
from src.utils.helpers import generate_invoice_number

logger = setup_logging(__name__)


class EtimsService:
    def __init__(self):
        self.settings = settings

    def _get_mock_invoice(self, sale) -> EtimsInvoice:
        now = datetime.now()
        inv_number = generate_invoice_number(now.date())
        control_number = f"MOCK-{now.strftime('%Y%m%d%H%M%S')}-{sale.id:06d}"

        qr_data = (
            f"KRA-ETIMS:{inv_number}:{control_number}:"
            f"{sale.grand_total:.2f}:{now.isoformat()}:MOCK"
        )

        with db_manager.get_session() as session:
            existing = (
                session.query(EtimsInvoice)
                .filter_by(sale_id=sale.id)
                .first()
            )
            if existing:
                existing.invoice_number = inv_number
                existing.control_number = control_number
                existing.qr_code = qr_data
                existing.submission_status = "PENDING"
                invoice = existing
            else:
                invoice = EtimsInvoice(
                    sale_id=sale.id,
                    invoice_number=inv_number,
                    control_number=control_number,
                    qr_code=qr_data,
                    submission_status="PENDING",
                )
                session.add(invoice)

        return invoice

    def _submit_to_kra(self, invoice_data: dict) -> dict:
        endpoint = self.settings.ETIMS_ENDPOINT

        if not endpoint:
            logger.info("eTIMS endpoint not configured; using mock submission.")
            return {
                "success": True,
                "mock": True,
                "message": "Mock submission (endpoint not configured).",
                "submitted_at": datetime.now().isoformat(),
            }

        username = self.settings.ETIMS_USERNAME or ""
        password = self.settings.ETIMS_PASSWORD or ""

        headers = {
            "Content-Type": "application/json",
        }

        if username and password:
            import base64
            auth_str = f"{username}:{password}"
            headers["Authorization"] = f"Basic {base64.b64encode(auth_str.encode()).decode()}"

        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(endpoint, json=invoice_data, headers=headers)
                response.raise_for_status()
                data = response.json()

            logger.info("eTIMS submission successful: %s", data.get("invoiceNumber", "N/A"))
            return {
                "success": True,
                "mock": False,
                "response": data,
                "submitted_at": datetime.now().isoformat(),
            }

        except httpx.TimeoutException:
            logger.error("eTIMS submission timed out.")
            raise EtimsError("eTIMS API request timed out.")
        except httpx.HTTPStatusError as e:
            logger.error("eTIMS submission failed: %s %s", e.response.status_code, e.response.text)
            raise EtimsError(f"eTIMS API error: {e.response.status_code} - {e.response.text[:200]}")
        except httpx.RequestError as e:
            logger.error("eTIMS connection error: %s", e)
            raise EtimsError(f"eTIMS connection error: {e}")

    def generate_invoice(self, sale) -> EtimsInvoice:
        invoice_data = {
            "saleId": sale.id,
            "receiptNumber": sale.receipt_number,
            "branchId": sale.branch_id,
            "userId": sale.user_id,
            "date": sale.created_at.isoformat() if sale.created_at else datetime.now().isoformat(),
            "items": [],
            "subtotal": sale.subtotal,
            "discount": sale.discount,
            "tax": sale.tax,
            "grandTotal": sale.grand_total,
            "paymentMethod": sale.payment_method,
        }

        for item in sale.items:
            invoice_data["items"].append({
                "productId": item.product_id,
                "productName": item.product.name if item.product else f"Product #{item.product_id}",
                "quantity": item.quantity,
                "unitPrice": item.unit_price,
                "subtotal": item.subtotal,
            })

        try:
            submission = self._submit_to_kra(invoice_data)
        except EtimsError:
            logger.warning("eTIMS submission failed for sale %s; falling back to mock.", sale.id)
            submission = {
                "success": True,
                "mock": True,
                "message": "Fallback mock after submission failure.",
                "submitted_at": datetime.now().isoformat(),
            }

        now = datetime.now()
        inv_number = generate_invoice_number(now.date())
        control_number = (
            submission.get("response", {}).get("controlNumber")
            if not submission.get("mock")
            else f"MOCK-{now.strftime('%Y%m%d%H%M%S')}-{sale.id:06d}"
        )

        qr_data = (
            f"KRA-ETIMS:{inv_number}:{control_number}:"
            f"{sale.grand_total:.2f}:{now.isoformat()}:"
            f"{'MOCK' if submission.get('mock') else 'LIVE'}"
        )

        with db_manager.get_session() as session:
            existing = (
                session.query(EtimsInvoice)
                .filter_by(sale_id=sale.id)
                .first()
            )
            if existing:
                existing.invoice_number = inv_number
                existing.control_number = control_number
                existing.qr_code = qr_data
                existing.submission_status = "SUBMITTED" if submission.get("success") else "FAILED"
                existing.submission_response = json.dumps(submission.get("response", submission))
                existing.submitted_at = datetime.now()
                invoice = existing
            else:
                invoice = EtimsInvoice(
                    sale_id=sale.id,
                    invoice_number=inv_number,
                    control_number=control_number,
                    qr_code=qr_data,
                    submission_status="SUBMITTED" if submission.get("success") else "FAILED",
                    submission_response=json.dumps(submission.get("response", submission)),
                    submitted_at=datetime.now(),
                )
                session.add(invoice)

        return invoice

    def get_qr_data(self, etims_invoice: EtimsInvoice) -> str:
        if etims_invoice.qr_code:
            return etims_invoice.qr_code

        now = datetime.now()
        qr_data = (
            f"KRA-ETIMS:{etims_invoice.invoice_number}:{etims_invoice.control_number}:"
            f"0.00:{now.isoformat()}:{'MOCK' if 'MOCK' in (etims_invoice.control_number or '') else 'LIVE'}"
        )

        with db_manager.get_session() as session:
            session.query(EtimsInvoice).filter_by(id=etims_invoice.id).update(
                {"qr_code": qr_data}
            )

        return qr_data

    def get_invoice(self, sale_id: int) -> EtimsInvoice | None:
        with db_manager.get_session() as session:
            return (
                session.query(EtimsInvoice)
                .filter_by(sale_id=sale_id)
                .first()
            )
