# Wines & Spirits POS System

A comprehensive Point of Sale system designed for wines and spirits retail businesses in Kenya. Features multi-branch management, inventory tracking, M-Pesa integration, eTIMS compliance, and real-time reporting.

## Features

- **Point of Sale** — Fast checkout with barcode scanning, discount management, and mixed payment methods
- **Inventory Management** — Stock tracking, low-stock alerts, stock movements, and transfers between branches
- **Multi-Branch Support** — Independent branch operations with centralized reporting
- **M-Pesa Integration** — Direct mobile money payment processing via Safaricom M-Pesa API
- **eTIMS Compliance** — KRA eTIMS invoice generation and submission
- **Reporting** — Daily sales, brand profitability, cashier performance, expense analysis
- **User Management** — Role-based access control (Admin, Manager, Cashier) with granular permissions
- **Receipt Printing** — Thermal receipt printing (58mm/80mm)
- **Offline-First** — Local SQLite database with background sync for multi-branch deployments
- **Audit Logging** — Complete audit trail of all system actions

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.13+ |
| GUI Framework | PyQt6 |
| Database | SQLite via SQLAlchemy 2.0 |
| Authentication | bcrypt |
| PDF/Receipts | ReportLab |
| QR Codes | qrcode[pil] |
| HTTP Client | httpx |
| Packaging | PyInstaller |

## Installation Guide

### Prerequisites

- Python 3.13 or higher
- pip package manager

### Step-by-Step Setup

1. **Clone the repository**

   ```
   git clone <repository-url>
   cd wines-spirits-pos
   ```

2. **Create a virtual environment**

   ```
   python -m venv venv
   ```

3. **Activate the virtual environment**

   - **Windows:**
     ```
     venv\Scripts\activate
     ```
   - **Linux/macOS:**
     ```
     source venv/bin/activate
     ```

4. **Install dependencies**

   ```
   pip install -r requirements.txt
   ```

5. **Run the application**

   ```
   python src/main.py
   ```

6. **Default login credentials**

   | Field | Value |
   |-------|-------|
   | Username | `admin` |
   | Password | `admin123` |
   | Branch Code | `HQ001` |

## Building Executable

To create a standalone executable (no Python required):

```
pip install pyinstaller
pyinstaller pos.spec
```

The executable will be created in the `dist/` directory as `WinesSpiritsPOS.exe`.

## Branch Setup

1. Log in as Admin
2. Navigate to **Admin > Branches**
3. Click **Add Branch** and fill in:
   - **Name** — Branch name (e.g., "Nairobi Main")
   - **Code** — Unique short code (e.g., "NBO01")
   - **Location** — Physical address
   - **Phone/Email** — Contact details
4. Assign users to the branch from **Admin > Users**

## M-Pesa Configuration

1. Register for M-Pesa API access at [Safaricom Developer Portal](https://developer.safaricom.co.ke)
2. Set the following in `src/config/settings.py` or via environment variables:

   | Setting | Description |
   |---------|-------------|
   | `MPESA_CONSUMER_KEY` | API consumer key |
   | `MPESA_CONSUMER_SECRET` | API consumer secret |
   | `MPESA_PASSKEY` | Online passkey |
   | `MPESA_SHORTCODE` | Business shortcode (174379 sandbox) |
   | `MPESA_CALLBACK_URL` | HTTPS callback endpoint |
   | `MPESA_ENVIRONMENT` | `sandbox` or `production` |

## Running Tests

```
pytest tests/ -v
```

With coverage report:

```
pytest tests/ --cov=src --cov-report=term-missing
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `sqlite3.OperationalError: no such table` | Run `schema.sql` against the database or restart the app to auto-create tables |
| PyQt6 import errors | Ensure PyQt6 is installed: `pip install PyQt6` |
| M-Pesa callback not received | Ensure the callback URL is HTTPS and accessible from the internet |
| Database locked | Delete `data/pos.db` (backup first) or restart the application |
| Permission denied on logs | Ensure the `logs/` directory exists and is writable |
| "Database not initialized" error | Ensure `src/config/settings.py` exists with correct paths |
