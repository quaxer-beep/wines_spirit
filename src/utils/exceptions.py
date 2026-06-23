class POSException(Exception):
    """Base exception for POS system"""

class AuthenticationError(POSException):
    """Raised on login failure"""

class AuthorizationError(POSException):
    """Raised when user lacks permission"""

class ValidationError(POSException):
    """Raised on data validation failure"""

class InsufficientStockError(POSException):
    """Raised when stock is insufficient"""

class DuplicateRecordError(POSException):
    """Raised on duplicate entry"""

class NotFoundError(POSException):
    """Raised when resource not found"""

class PaymentError(POSException):
    """Base for payment errors"""

class MpesaError(PaymentError):
    """M-Pesa integration error"""

class EtimsError(POSException):
    """eTIMS integration error"""

class SyncError(POSException):
    """Synchronization error"""

class DatabaseError(POSException):
    """Database operation error"""
