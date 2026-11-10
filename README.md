# 🏪 ShopKH — E-Commerce Web Application

A full-featured online shopping platform built with **Python Flask** for BIU Year 4 Semester 2 Tuesday Assignment.

🌐 **Live Demo:** [https://assignmentpython.vercel.app](https://assignmentpython.vercel.app)

---

## 📋 Project Overview

ShopKH is a complete e-commerce web application where users can browse products, add items to cart, place orders, and write reviews. Admin users can manage products, categories, orders, and users through a dedicated admin dashboard.

---

## 🛠 Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.x, Flask 3.1 |
| Database | SQLite + SQLAlchemy ORM |
| Frontend | HTML5, CSS3, JavaScript |
| UI Framework | Bootstrap 5.3 |
| Icons | Font Awesome 6.5 |
| Fonts | Google Fonts (Inter) |
| Deployment | Vercel |

---

## ✨ Features

### Customer Features
- 🔍 Browse and search products
- 🏷 Filter by category, price range, and sort options
- 🛒 Add to cart and manage quantities
- 💳 Checkout with shipping address and payment method
- ⭐ Write product reviews and ratings
- 👤 User account with order history and profile

### Admin Features
- 📊 Dashboard with live statistics (products, orders, revenue, users)
- 📦 Full product management (Add / Edit / Delete)
- 🏷 Category management
- 🛍 Order management with status updates
- 👥 User management with admin role control

---

## 📁 Project Structure

```
python-flask-shop/
├── server.py              # Main Flask application (routes + models)
├── requirements.txt       # Python dependencies
├── vercel.json            # Vercel deployment config
├── static/
│   ├── css/style.css      # Custom styles
│   └── js/main.js         # JavaScript interactions
└── templates/
    ├── base.html           # Base layout (navbar, footer)
    ├── index.html          # Home page
    ├── products.html       # Product listing with filters
    ├── product_detail.html # Product detail with reviews
    ├── cart.html           # Shopping cart
    ├── checkout.html       # Checkout form
    ├── orders.html         # Order history
    ├── profile.html        # User profile
    ├── login.html          # Login page
    ├── register.html       # Register page
    ├── shared/
    │   └── product_card.html  # Reusable product card component
    └── admin/
        ├── base_admin.html    # Admin layout
        ├── dashboard.html     # Admin dashboard
        ├── products.html      # Manage products
        ├── categories.html    # Manage categories
        ├── orders.html        # Manage orders
        └── users.html         # Manage users
```

---

## 🗄 Database Models

```
User        — username, email, password (hashed), is_admin, phone, address
Category    — name, description, icon
Product     — name, description, price, original_price, stock, image_url, is_featured
Order       — user_id, total, status, shipping_address, phone, note
OrderItem   — order_id, product_id, quantity, price
Review      — user_id, product_id, rating (1-5), comment
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- pip

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/tonlecode/python-flask-shop.git
cd python-flask-shop

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
python server.py
```

### Access the Application

| Page | URL |
|------|-----|
| Home | http://localhost:5000 |
| Products | http://localhost:5000/products |
| Login | http://localhost:5000/login |
| Admin Panel | http://localhost:5000/admin |

### Default Admin Account

| Field | Value |
|-------|-------|
| Email | admin@shopkh.com |
| Password | admin123 |

> The database is seeded automatically on first run with 6 categories, 20 products, and an admin account.

---

## 📸 Screenshots

### Home Page
![Home](https://assignmentpython.vercel.app)

### Products Page
Browse 20+ products with filter and sort options.

### Admin Dashboard
Manage the entire store from the admin panel at `/admin`.

---

## 👥 Team Members — BIU Year 4 Semester 2

| # | Name | Role |
|---|------|------|
| 1 | Member 1 | Introduction & Overview |
| 2 | Member 2 | Architecture & Database |
| 3 | Member 3 | UI Design & Frontend |
| 4 | Member 4 | E-Commerce Features |
| 5 | Member 5 | Admin Panel & Backend |
| 6 | Member 6 | Demo & Conclusion |

---

## 📄 License

This project is for educational purposes — BIU Year 4 Semester 2 Tuesday Assignment.
