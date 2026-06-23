import base64
from datetime import datetime

import httpx

from src.config.logging_config import setup_logging
from src.config.settings import settings
from src.database.connection import db_manager
from src.database.models import MpesaTransaction
from src.utils.exceptions import MpesaError, ValidationError
from src.utils.validators import sanitize_phone

logger = setup_logging(__name__)


class MpesaService:
    def __init__(self):
        self.settings = settings
        self._base_url = self._get_base_url()

    def _get_base_url(self) -> str:
        env = self.settings.MPESA_ENVIRONMENT or "sandbox"
        if env.lower() == "production":
            return "https://api.safaricom.co.ke"
        return "https://sandbox.safaricom.co.ke"

    def _get_access_token(self) -> str:
        url = f"{self._base_url}/oauth/v1/generate?grant_type=client_credentials"
        consumer_key = self.settings.MPESA_CONSUMER_KEY
        consumer_secret = self.settings.MPESA_CONSUMER_SECRET

        if not consumer_key or not consumer_secret:
            raise MpesaError("MPESA_CONSUMER_KEY and MPESA_CONSUMER_SECRET must be configured.")

        try:
            with httpx.Client(timeout=30) as client:
                response = client.get(
                    url,
                    auth=(consumer_key, consumer_secret),
                    headers={"Accept": "application/json"},
                )
                response.raise_for_status()
                data = response.json()
                token = data.get("access_token")
                if not token:
                    raise MpesaError("No access_token in response.")
                logger.info("M-Pesa access token obtained successfully.")
                return token
        except httpx.TimeoutException:
            raise MpesaError("Request timed out while obtaining M-Pesa access token.")
        except httpx.HTTPStatusError as e:
            raise MpesaError(f"M-Pesa auth failed with status {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise MpesaError(f"Connection error obtaining M-Pesa token: {e}")

    def _get_timestamp(self) -> str:
        return datetime.now().strftime("%Y%m%d%H%M%S")

    def _get_password(self) -> str:
        timestamp = self._get_timestamp()
        raw = f"{self.settings.MPESA_SHORTCODE}{self.settings.MPESA_PASSKEY}{timestamp}"
        return base64.b64encode(raw.encode()).decode()

    def stk_push(self, phone: str, amount: float, account_reference: str, transaction_desc: str) -> dict:
        if not self.settings.MPESA_SHORTCODE:
            raise MpesaError("MPESA_SHORTCODE is not configured.")

        try:
            sanitized_phone = sanitize_phone(phone)
        except ValidationError as e:
            raise MpesaError(f"Invalid phone number: {e}")

        token = self._get_access_token()
        password = self._get_password()
        timestamp = self._get_timestamp()

        payload = {
            "BusinessShortCode": self.settings.MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(round(amount)),
            "PartyA": sanitized_phone,
            "PartyB": self.settings.MPESA_SHORTCODE,
            "PhoneNumber": sanitized_phone,
            "CallBackURL": self.settings.MPESA_CALLBACK_URL or "",
            "AccountReference": account_reference[:12],
            "TransactionDesc": transaction_desc[:13],
        }

        url = f"{self._base_url}/mpesa/stkpush/v1/processrequest"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()

            checkout_id = data.get("CheckoutRequestID")
            response_code = data.get("ResponseCode")

            logger.info(
                "STK Push initiated: CheckoutRequestID=%s, ResponseCode=%s, Phone=%s, Amount=%s",
                checkout_id, response_code, sanitized_phone, amount,
            )

            if response_code != "0":
                raise MpesaError(f"STK Push failed: {data.get('ResponseDescription', 'Unknown error')}")

            with db_manager.get_session() as session:
                txn = MpesaTransaction(
                    checkout_request_id=checkout_id,
                    merchant_request_id=data.get("MerchantRequestID"),
                    amount=amount,
                    phone_number=sanitized_phone,
                    status="PENDING",
                )
                session.add(txn)

            return {
                "checkout_request_id": checkout_id,
                "merchant_request_id": data.get("MerchantRequestID"),
                "response_code": response_code,
                "response_description": data.get("ResponseDescription"),
            }

        except httpx.TimeoutException:
            raise MpesaError("STK Push request timed out.")
        except httpx.HTTPStatusError as e:
            raise MpesaError(f"STK Push failed with status {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise MpesaError(f"Connection error during STK Push: {e}")

    def query_status(self, checkout_request_id: str) -> dict:
        token = self._get_access_token()
        password = self._get_password()
        timestamp = self._get_timestamp()

        payload = {
            "BusinessShortCode": self.settings.MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id,
        }

        url = f"{self._base_url}/mpesa/stkpushquery/v1/query"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()

            logger.info("Status query for %s: ResultCode=%s", checkout_request_id, data.get("ResultCode"))
            return data

        except httpx.TimeoutException:
            raise MpesaError("Status query timed out.")
        except httpx.HTTPStatusError as e:
            raise MpesaError(f"Status query failed with status {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise MpesaError(f"Connection error during status query: {e}")

    def process_callback(self, callback_data: dict) -> dict:
        if not callback_data:
            raise MpesaError("Empty callback data received.")

        body = callback_data.get("Body")
        if not body:
            raise MpesaError("Callback missing 'Body'.")

        stk_callback = body.get("stkCallback")
        if not stk_callback:
            raise MpesaError("Callback missing 'stkCallback'.")

        checkout_request_id = stk_callback.get("CheckoutRequestID")
        result_code = stk_callback.get("ResultCode")
        result_desc = stk_callback.get("ResultDesc", "")

        logger.info(
            "Callback received: CheckoutRequestID=%s, ResultCode=%s",
            checkout_request_id, result_code,
        )

        metadata_items = {}
        if result_code == 0:
            metadata = stk_callback.get("CallbackMetadata", {})
            for item in metadata.get("Item", []):
                name = item.get("Name")
                value = item.get("Value")
                if name and value is not None:
                    metadata_items[name] = value

        transaction_code = metadata_items.get("MpesaReceiptNumber")
        amount = metadata_items.get("Amount")
        phone_number = metadata_items.get("PhoneNumber")

        with db_manager.get_session() as session:
            txn = (
                session.query(MpesaTransaction)
                .filter_by(checkout_request_id=checkout_request_id)
                .first()
            )

            if txn:
                txn.status = "SUCCESS" if result_code == 0 else "FAILED"
                txn.result_desc = result_desc
                if transaction_code:
                    txn.transaction_code = transaction_code
                if amount:
                    txn.amount = float(amount)
                if phone_number:
                    txn.phone_number = str(phone_number)
            else:
                txn = MpesaTransaction(
                    checkout_request_id=checkout_request_id,
                    transaction_code=transaction_code,
                    amount=float(amount) if amount else 0,
                    phone_number=str(phone_number) if phone_number else None,
                    status="SUCCESS" if result_code == 0 else "FAILED",
                    result_desc=result_desc,
                )
                session.add(txn)

        return {
            "checkout_request_id": checkout_request_id,
            "result_code": result_code,
            "result_desc": result_desc,
            "transaction_code": transaction_code,
            "amount": float(amount) if amount else None,
            "phone_number": str(phone_number) if phone_number else None,
            "success": result_code == 0,
        }

    def verify_payment(self, checkout_request_id: str, expected_amount: float) -> bool:
        with db_manager.get_session() as session:
            txn = (
                session.query(MpesaTransaction)
                .filter_by(checkout_request_id=checkout_request_id)
                .first()
            )

        if not txn:
            logger.warning("No transaction found for checkout request %s", checkout_request_id)
            return False

        if txn.status != "SUCCESS":
            logger.warning(
                "Transaction %s status is %s, expected SUCCESS",
                checkout_request_id, txn.status,
            )
            return False

        if abs(txn.amount - expected_amount) > 0.01:
            logger.warning(
                "Amount mismatch for %s: expected %s, got %s",
                checkout_request_id, expected_amount, txn.amount,
            )
            return False

        return True
