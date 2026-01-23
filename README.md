# Django-coasc

Double entry bookkeeping in Django. Inspired by [Django-hordak](https://github.com/adamcharnock/django-hordak) and [gnucash](https://github.com/Gnucash/gnucash)

A simple and well tested core to build double entry system accounting apps upon. Django-coasc provides a model layer for a double-entry accounting system, primarily aimed at cooperative organizations but suitable for various accounting needs.

## Interface built upon Django-coasc

> [COASV](https://github.com/suresh466/coasv) Accounting app for Cooperatives

## Using Django-coasc in your project

### Install

Install using [uv](https://github.com/astral-sh/uv)

```bash
uv add django-coasc
```

Or using pip:

```bash
pip install django-coasc
```

Add `coasc` to your `INSTALLED_APPS` in Django settings:

```python
INSTALLED_APPS = [
    # ...
    'coasc',
    # ...
]
```

### Run migrations

```bash
python manage.py migrate coasc

```

Or using uv:

```bash
uv run ./manage.py migrate coasc
```

## Features

- **Double-entry bookkeeping** - Each transaction must have balanced debits and credits
- **Hierarchical accounts** - Support for parent and child account relationships
- **Multiple account types** - Assets, Liabilities, Income, and Expenses
- **Transaction validation** - Ensures accounting integrity
- **Balance calculation** - Methods to calculate account balances with optional date filters
- **Revertible transactions** - Built-in support for reverting transactions

## Core Components

- **Member**: Represents individuals or entities associated with accounts
- **Ac (Account)**: The core entity representing different types of accounts
  - Parent accounts - Group related accounts
  - Child accounts - Belong to a parent account
  - Standalone accounts - Independent accounts
- **Transaction**: Represents financial transactions
- **Split**: Represents individual debit or credit entries within a transaction

### Terminology

COASC: Cooperative Accounting System Core
COASV: Cooperative Accounting System View

## TODOs

1. add comments where appropriate
2. write tests for date filtered bal and total_bal()
3. modify tests for transaction(renamed date_created to created_at and add tx_date field)
