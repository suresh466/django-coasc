# COASC (Cooperative Accounting System Core)

A simple and well-tested core to build double-entry accounting systems upon. **Django-coasc** provides a robust model layer primarily aimed at cooperative organizations but suitable for various accounting needs.

Inspired by [Django-hordak](https://github.com/adamcharnock/django-hordak) and [gnucash](https://github.com/Gnucash/gnucash).

## 🚀 Key Features

- **Double-Entry Bookkeeping**: Ensures accounting integrity where each transaction has balanced debits and credits.
- **Hierarchical Accounts**: Flexible support for parent and child account relationships.
- **Multiple Account Types**: Built-in handling for Assets, Liabilities, Income, and Expenses.
- **Transaction Validation**: Rigorous validation logic to maintain data consistency.
- **Balance Calculation**: Efficient methods for calculating balances with support for date filtering.
- **Revertible Transactions**: Native support for safe transaction reversals.

## 🛠️ Tech Stack

- **Framework:** Django
- **Language:** Python
- **Database:** PostgreSQL (Recommended)
- **Tooling:** uv, Ruff, MyPy

## 📦 Getting Started

### Installation

1. **Install the package**:

   Using [uv](https://github.com/astral-sh/uv):

   ```bash
   uv add django-coasc
   ```

   Or using pip:

   ```bash
   pip install django-coasc
   ```

2. **Configure Django**:

   Add `coasc` to your `INSTALLED_APPS` in `settings.py`:

   ```python
   INSTALLED_APPS = [
       # ...
       'coasc',
       # ...
   ]
   ```

3. **Run Migrations**:

   ```bash
   python manage.py migrate coasc
   ```

   Or using uv:

   ```bash
   uv run ./manage.py migrate coasc
   ```

## 🧩 Core Components

- **Member**: Represents individuals or entities associated with accounts.
- **Ac (Account)**: The core entity representing different types of accounts.
  - *Parent accounts*: Group related accounts.
  - *Child accounts*: Belong to a parent account.
  - *Standalone accounts*: Independent accounts.
- **Transaction**: Represents a financial event affecting the books.
- **Split**: Represents individual debit or credit entries within a transaction.

## 🔗 Related Projects

- **[COASV](https://github.com/suresh466/coasv)** (Cooperative Accounting System View): A comprehensive accounting interface for Cooperatives built upon this core.

## ✅ TODOs

1. Add comments where appropriate.
2. Write tests for date filtered `bal()` and `total_bal()`.
3. Modify tests for transaction (renamed `date_created` to `created_at` and add `tx_date` field).
