# Inventory Management

## Table of Contents

- [About the Project](#about-the-project)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Start from Scratch](#start-from-scratch-fresh-project-setup)
- [Setup & Installation](#setup--installation)
- [User Roles](#user-roles)
- [URL Structure](#url-structure)
- [Email Notifications](#email-notifications)
- [Database Backup](#database-backup)
- [Useful Commands](#useful-commands)
- [Main Dependencies](#main-dependencies)
- [License](#license)

---

## About the Project

**Inventory Management** is a comprehensive web-based warehouse management system built with Django.
It provides full management of products, invoices, stock transactions, and users,
with a Persian (Farsi) interface and complete Jalali (Shamsi) calendar support.

### Key Features

- **Product Management** — Add, edit, delete, and search products with advanced filters
- **Invoice Management** — Create, edit, delete, and print sales invoices
- **Stock Transactions** — Record incoming and outgoing stock with automatic inventory updates
- **Product Returns** — Register full invoice returns and restore stock automatically
- **User Management** — Two roles (Admin and Customer) with separate access levels
- **Reports** — View transaction history and user activity logs
- **Jalali Calendar** — Full Shamsi date support throughout the system via custom template tags
- **Email Notifications** — Automatic email alerts sent on every outgoing stock transaction
- **Database Backup** — Built-in backup script (`backup_db.py`)

---

## Project Structure

```text
Inventory_management/                        ← Root directory
├── manage.py                                ← Django management entry point
├── requirements.txt                         ← Python dependencies
├── README.md                                ← Project documentation
├── backup_db.py                             ← Database backup utility script
├── db.sqlite3                               ← SQLite database (development only)
│
├── Inventory_management/                    ← Django project settings package
│   ├── __init__.py
│   ├── settings.py                          ← Main settings (reads from .env)
│   ├── urls.py                              ← Root URL configuration
│   ├── asgi.py                              ← ASGI entry point
│   └── wsgi.py                              ← WSGI entry point
│
└── warehouse/                               ← Main application
    ├── __init__.py
    ├── admin.py                             ← Django admin configuration
    ├── apps.py                              ← App configuration & signals loader
    ├── filters.py                           ← Django-filter definitions
    ├── forms.py                             ← All application forms
    ├── models.py                            ← Database models & signals
    ├── signals.py                           ← Post-save signal for email notifications
    ├── views.py                             ← All view functions
    ├── urls.py                              ← App URL patterns
    ├── tests.py                             ← Unit tests
    │
    ├── templatetags/                        ← Custom template tags
    │   ├── __init__.py
    │   └── jalali_filters.py                ← Jalali date filters for templates
    │
    ├── static/                              ← Static files
    │   ├── css/
    │   │   └── style.css                    ← Main stylesheet
    │   └── images/
    │       └── logo.png                     ← Application logo
    │
    └── templates/                           ← HTML templates
        ├── base.html                        ← Base layout template
        ├── login.html                       ← Login page
        ├── dashboard.html                   ← Main dashboard
        ├── invoices/
        │   ├── list.html
        │   ├── create.html
        │   ├── edit.html
        │   ├── detail.html
        │   ├── print.html
        │   └── delete_confirm.html
        ├── items/
        │   ├── list.html
        │   ├── create.html
        │   ├── edit.html
        │   └── delete_confirm.html
        ├── users/
        │   ├── list.html
        │   ├── create.html
        │   ├── edit.html
        │   ├── reports.html
        │   └── delete_confirm.html
        ├── reports/
        │   └── report.html
        ├── returns/
        │   └── return_purchase.html
        └── transactions/
            ├── incoming.html
            └── outgoing.html
```

---

## Prerequisites

- Python 3.10 or higher
- PostgreSQL 13 or higher (recommended for production)
- pip

> **Note:** The repository includes a `db.sqlite3` file for quick local development.
> For production use, PostgreSQL is strongly recommended.

---

## Start from Scratch (Fresh Project Setup)

If you want to build this project from the ground up rather than cloning the repository,
follow these steps in order:

```bash
# 1. Create the project root directory and navigate into it
mkdir Inventory
cd Inventory

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate          # On Windows: venv\Scripts\activate

# 3. Upgrade pip and install Django
pip install --upgrade pip
pip install django

# 4. Create the Django project
django-admin startproject Inventory_management

# 5. Navigate into the project directory
cd Inventory_management

# 6. Create the warehouse app
python manage.py startapp warehouse
```

Then open `Inventory_management/settings.py` and add the app to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    'warehouse.apps.WarehouseConfig',
    'widget_tweaks',
    'django_jalali',
]
```

Continue with the remaining steps:

```bash
# 7. Install all required packages
pip install -r requirements.txt

# 8. Apply migrations
python manage.py makemigrations
python manage.py migrate

# 9. Create a superuser
python manage.py createsuperuser

# 10. Run the development server
python manage.py runserver
```

---

## Setup & Installation

> Use this section if you are cloning an existing copy of the project.

### 1. Clone the Repository

```bash
git clone <repository-url> Inventory
cd Inventory/Inventory_management
```

### 2. Create a Virtual Environment

```bash
python3 -m venv venv
```

### 3. Activate the Virtual Environment

On Linux / macOS:

```bash
source venv/bin/activate
```

On Windows:

```bash
venv\Scripts\activate
```

Once activated, `(venv)` will appear at the beginning of your terminal prompt.

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables (.env)

Inside `Inventory_management/Inventory_management/`, create a file named `.env`:

```bash
nano Inventory_management/.env
```

Contents of the `.env` file:

```ini
SECRET_KEY=your-long-random-secret-key-here
DEBUG=True
DB_NAME=inventory_management
DB_USER=your-db-username
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432
```

> **Tip:** To generate a secure `SECRET_KEY`, run:
>
> ```bash
> python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
> ```

### 6. Set Up the PostgreSQL Database

```bash
sudo -u postgres psql
```

Then inside the psql shell:

```sql
CREATE DATABASE inventory_management;
CREATE USER your_db_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE inventory_management TO your_db_user;
\q
```

### 7. Apply Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 8. Create a Superuser

```bash
python manage.py createsuperuser
```

You will be prompted to enter:

```
Username: admin
Email address: example@email.com
Password: ********
Password (again): ********
```

> **Important:** After creating the superuser, log in to the Django admin panel and manually
> create a `Profile` for this user with the role set to `admin`.
> Without this step, the superuser will **not** be able to access the dashboard.
>
> Django admin panel: `http://127.0.0.1:8000/admin/`

### 9. Collect Static Files

```bash
python manage.py collectstatic
```

### 10. Run the Development Server

```bash
python manage.py runserver
```

Then open your browser and go to:

```
http://127.0.0.1:8000/
```

---

## User Roles

| Role      | Access                                                       |
|-----------|--------------------------------------------------------------|
| admin     | Dashboard, products, invoices, reports, stock returns        |
| customer  | Receive invoices only (no dashboard access)                  |
| superuser | Full user management + all admin access                      |

---

## URL Structure

| URL                      | Description                    |
|--------------------------|--------------------------------|
| `/`                      | Dashboard                      |
| `/login/`                | Login page                     |
| `/logout/`               | Logout                         |
| `/items/`                | Product list                   |
| `/items/create/`         | Add new product                |
| `/items/<id>/edit/`      | Edit product                   |
| `/items/<id>/delete/`    | Delete product                 |
| `/invoices/`             | Invoice list                   |
| `/invoices/create/`      | Create invoice                 |
| `/invoices/<id>/edit/`   | Edit invoice                   |
| `/invoices/<id>/detail/` | Invoice detail                 |
| `/invoices/<id>/print/`  | Print invoice                  |
| `/return/`               | Register product return        |
| `/reports/`              | Transaction & activity reports |
| `/users/`                | User list (superuser only)     |
| `/users/create/`         | Add new user                   |
| `/users/<id>/edit/`      | Edit user                      |
| `/users/<id>/reports/`   | User activity report           |
| `/admin/`                | Django admin panel             |

---

## Email Notifications

The project automatically sends an email whenever an **outgoing stock transaction** is recorded.
This is handled by `warehouse/signals.py` using Django's `post_save` signal on the `Transaction` model.

### How It Works

- Triggers only on **new** transactions of type `out`
- If the user has an email address, the notification is sent to them
- If not, it falls back to `ADMIN_EMAILS` defined in `settings.py`
- If neither is set, it falls back to `DEFAULT_FROM_EMAIL`

### Email Configuration

The following settings are already configured in `settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your_email@gmail.com'
EMAIL_HOST_PASSWORD = 'your_app_password_here'
DEFAULT_FROM_EMAIL = 'your_email@gmail.com'

# Fallback admin email list if the user has no email set
ADMIN_EMAILS = ['your_email@gmail.com']
```

> **Important:** Move sensitive values like `EMAIL_HOST_PASSWORD` to your `.env` file
> and read them with `python-decouple` to avoid exposing credentials in your codebase:
>
> ```ini
> # .env
> EMAIL_HOST_PASSWORD=your_app_password_here
> ```
>
> ```python
> # settings.py
> EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
> ```

> **Note:** For Gmail, you must use an **App Password**, not your main account password.
> Generate one from: Google Account → Security → 2-Step Verification → App Passwords.

---

## Database Backup

The project includes a `backup_db.py` script for backing up the database.
To run it:

```bash
python backup_db.py
```

Make sure the virtual environment is activated before running the script.

---

## Useful Commands

```bash
# Activate virtual environment (Linux/macOS)
source venv/bin/activate

# Run development server
python manage.py runserver

# Create and apply migrations after changing models
python manage.py makemigrations
python manage.py migrate

# Create a superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Run tests
python manage.py test warehouse

# Back up the database
python backup_db.py

# Deactivate virtual environment
deactivate
```

---

## Main Dependencies

| Package | Description |
|---------|-------------|
| [Django](https://www.djangoproject.com/) | Web framework |
| [psycopg2-binary](https://pypi.org/project/psycopg2-binary/) | PostgreSQL adapter |
| [python-decouple](https://pypi.org/project/python-decouple/) | Environment variable management |
| [jdatetime](https://pypi.org/project/jdatetime/) | Jalali date conversion and display |
| [django-jalali](https://pypi.org/project/django-jalali/) | Jalali calendar support for Django |
| [django-widget-tweaks](https://pypi.org/project/django-widget-tweaks/) | Form widget customization in templates |
| [django-filter](https://pypi.org/project/django-filter/) | Advanced queryset filtering |
| [Pillow](https://pypi.org/project/Pillow/) | Image processing support |
| [openpyxl](https://pypi.org/project/openpyxl/) | Excel file support |
| [pandas](https://pypi.org/project/pandas/) | Data analysis and export |

---

## Screenshots

## Note:** The `.env` file is intentionally excluded from the repository for security reasons. You must create it manually before running the project.

## License

This project was developed for personal and educational use.
