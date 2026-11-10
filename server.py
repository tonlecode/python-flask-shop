from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps

import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'shopkh-secret-key-biu-2024'
# Use /tmp on Vercel (read-only filesystem), local instance folder otherwise
if os.environ.get('VERCEL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/shopkh.db'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shopkh.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ===== MODELS =====

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    phone = db.Column(db.String(20), default='')
    address = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    orders = db.relationship('Order', backref='user', lazy=True)
    reviews = db.relationship('Review', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, default='')
    icon = db.Column(db.String(60), default='fas fa-tag')
    products = db.relationship('Product', backref='category', lazy=True)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    price = db.Column(db.Float, nullable=False)
    original_price = db.Column(db.Float, nullable=True)
    stock = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    image_url = db.Column(db.String(300), default='')
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    reviews = db.relationship('Review', backref='product', lazy=True)

    @property
    def avg_rating(self):
        if self.reviews:
            return round(sum(r.rating for r in self.reviews) / len(self.reviews), 1)
        return 0

    @property
    def discount_percent(self):
        if self.original_price and self.original_price > self.price:
            return int((1 - self.price / self.original_price) * 100)
        return 0


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    shipping_address = db.Column(db.Text, default='')
    phone = db.Column(db.String(20), default='')
    note = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True)


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ===== HELPERS =====

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login.', 'warning')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated


def get_cart():
    return session.get('cart', {})


def get_cart_count():
    cart = get_cart()
    return sum(item['qty'] for item in cart.values())


def get_cart_total():
    cart = get_cart()
    return sum(item['price'] * item['qty'] for item in cart.values())


@app.context_processor
def inject_globals():
    current_user = None
    if 'user_id' in session:
        current_user = User.query.get(session['user_id'])
    categories = Category.query.all()
    return dict(
        current_user=current_user,
        categories=categories,
        cart_count=get_cart_count()
    )


# ===== PUBLIC ROUTES =====

@app.route('/')
def home():
    featured = Product.query.filter_by(is_featured=True).limit(8).all()
    new_products = Product.query.order_by(Product.created_at.desc()).limit(8).all()
    categories = Category.query.all()
    total_products = Product.query.count()
    total_users = User.query.filter_by(is_admin=False).count()
    total_orders = Order.query.count()
    return render_template('index.html',
                           featured=featured,
                           new_products=new_products,
                           categories=categories,
                           total_products=total_products,
                           total_users=total_users,
                           total_orders=total_orders)


@app.route('/products')
def products():
    query = request.args.get('q', '')
    category_id = request.args.get('category', type=int)
    sort = request.args.get('sort', 'newest')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    page = request.args.get('page', 1, type=int)

    q = Product.query
    if query:
        q = q.filter(Product.name.ilike(f'%{query}%'))
    if category_id:
        q = q.filter_by(category_id=category_id)
    if min_price is not None:
        q = q.filter(Product.price >= min_price)
    if max_price is not None:
        q = q.filter(Product.price <= max_price)

    if sort == 'price_asc':
        q = q.order_by(Product.price.asc())
    elif sort == 'price_desc':
        q = q.order_by(Product.price.desc())
    elif sort == 'name':
        q = q.order_by(Product.name.asc())
    else:
        q = q.order_by(Product.created_at.desc())

    pagination = q.paginate(page=page, per_page=12, error_out=False)
    categories = Category.query.all()
    return render_template('products.html',
                           products=pagination.items,
                           pagination=pagination,
                           categories=categories,
                           query=query,
                           selected_category=category_id,
                           sort=sort,
                           min_price=min_price,
                           max_price=max_price)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    related = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id
    ).limit(4).all()
    return render_template('product_detail.html', product=product, related=related)


@app.route('/product/<int:product_id>/review', methods=['POST'])
@login_required
def add_review(product_id):
    product = Product.query.get_or_404(product_id)
    existing = Review.query.filter_by(user_id=session['user_id'], product_id=product_id).first()
    if existing:
        flash('You already reviewed this product.', 'warning')
        return redirect(url_for('product_detail', product_id=product_id))
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment', '')
    if not rating or rating < 1 or rating > 5:
        flash('Please select a valid rating.', 'danger')
        return redirect(url_for('product_detail', product_id=product_id))
    review = Review(user_id=session['user_id'], product_id=product_id,
                    rating=rating, comment=comment)
    db.session.add(review)
    db.session.commit()
    flash('Review submitted successfully!', 'success')
    return redirect(url_for('product_detail', product_id=product_id))


@app.route('/category/<int:category_id>')
def category(category_id):
    cat = Category.query.get_or_404(category_id)
    page = request.args.get('page', 1, type=int)
    pagination = Product.query.filter_by(category_id=category_id).paginate(page=page, per_page=12)
    return render_template('products.html',
                           products=pagination.items,
                           pagination=pagination,
                           categories=Category.query.all(),
                           selected_category=category_id,
                           cat_name=cat.name,
                           query='', sort='newest',
                           min_price=None, max_price=None)


# ===== CART ROUTES =====

@app.route('/cart')
def cart():
    cart = get_cart()
    items = []
    for pid, item in cart.items():
        product = Product.query.get(int(pid))
        if product:
            items.append({'product': product, 'qty': item['qty'], 'subtotal': item['price'] * item['qty']})
    total = get_cart_total()
    return render_template('cart.html', items=items, total=total)


@app.route('/cart/add', methods=['POST'])
def cart_add():
    product_id = str(request.form.get('product_id'))
    qty = int(request.form.get('qty', 1))
    product = Product.query.get_or_404(int(product_id))
    cart = get_cart()
    if product_id in cart:
        cart[product_id]['qty'] += qty
    else:
        cart[product_id] = {'name': product.name, 'price': product.price, 'qty': qty, 'image': product.image_url}
    session['cart'] = cart
    flash(f'"{product.name}" added to cart!', 'success')
    return redirect(request.referrer or url_for('cart'))


@app.route('/cart/update', methods=['POST'])
def cart_update():
    product_id = str(request.form.get('product_id'))
    qty = int(request.form.get('qty', 1))
    cart = get_cart()
    if product_id in cart:
        if qty <= 0:
            del cart[product_id]
        else:
            cart[product_id]['qty'] = qty
    session['cart'] = cart
    return redirect(url_for('cart'))


@app.route('/cart/remove/<int:product_id>')
def cart_remove(product_id):
    cart = get_cart()
    pid = str(product_id)
    if pid in cart:
        del cart[pid]
    session['cart'] = cart
    flash('Item removed from cart.', 'info')
    return redirect(url_for('cart'))


@app.route('/cart/clear')
def cart_clear():
    session['cart'] = {}
    flash('Cart cleared.', 'info')
    return redirect(url_for('cart'))


# ===== CHECKOUT / ORDER ROUTES =====

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart = get_cart()
    if not cart:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart'))
    user = User.query.get(session['user_id'])
    items = []
    for pid, item in cart.items():
        product = Product.query.get(int(pid))
        if product:
            items.append({'product': product, 'qty': item['qty'], 'subtotal': item['price'] * item['qty']})
    total = get_cart_total()

    if request.method == 'POST':
        address = request.form.get('address', '').strip()
        phone = request.form.get('phone', '').strip()
        note = request.form.get('note', '')
        if not address or not phone:
            flash('Please fill in address and phone.', 'danger')
            return render_template('checkout.html', items=items, total=total, user=user)

        order = Order(user_id=session['user_id'], total=total,
                      shipping_address=address, phone=phone, note=note)
        db.session.add(order)
        db.session.flush()

        for pid, item in cart.items():
            product = Product.query.get(int(pid))
            if product:
                oi = OrderItem(order_id=order.id, product_id=product.id,
                               quantity=item['qty'], price=item['price'])
                db.session.add(oi)
                if product.stock >= item['qty']:
                    product.stock -= item['qty']

        db.session.commit()
        session['cart'] = {}
        flash('Order placed successfully!', 'success')
        return redirect(url_for('order_success', order_id=order.id))

    return render_template('checkout.html', items=items, total=total, user=user)


@app.route('/order/success/<int:order_id>')
@login_required
def order_success(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != session['user_id']:
        return redirect(url_for('home'))
    return render_template('order_success.html', order=order)


@app.route('/orders')
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=session['user_id'])\
                             .order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=user_orders)


@app.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != session['user_id']:
        flash('Access denied.', 'danger')
        return redirect(url_for('orders'))
    return render_template('order_detail.html', order=order)


# ===== AUTH ROUTES =====

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash(f'Welcome back, {user.username}!', 'success')
            next_url = request.args.get('next')
            return redirect(next_url or url_for('home'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('register.html')
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('register.html')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('register.html')
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return render_template('register.html')
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        flash('Account created successfully! Welcome!', 'success')
        return redirect(url_for('home'))
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        user.username = request.form.get('username', user.username).strip()
        user.phone = request.form.get('phone', '').strip()
        user.address = request.form.get('address', '').strip()
        new_password = request.form.get('new_password', '')
        if new_password:
            if len(new_password) < 6:
                flash('Password must be at least 6 characters.', 'danger')
                return render_template('profile.html', user=user)
            user.set_password(new_password)
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html', user=user)


# ===== ADMIN ROUTES =====

@app.route('/admin')
@admin_required
def admin_dashboard():
    stats = {
        'total_products': Product.query.count(),
        'total_orders': Order.query.count(),
        'total_users': User.query.filter_by(is_admin=False).count(),
        'total_revenue': db.session.query(db.func.sum(Order.total)).scalar() or 0,
        'pending_orders': Order.query.filter_by(status='pending').count(),
        'low_stock': Product.query.filter(Product.stock < 5).count(),
    }
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    return render_template('admin/dashboard.html', stats=stats, recent_orders=recent_orders)


@app.route('/admin/products')
@admin_required
def admin_products():
    page = request.args.get('page', 1, type=int)
    products = Product.query.order_by(Product.created_at.desc()).paginate(page=page, per_page=15)
    return render_template('admin/products.html', products=products)


@app.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
def admin_product_add():
    categories = Category.query.all()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '')
        price = request.form.get('price', type=float)
        original_price = request.form.get('original_price', type=float)
        stock = request.form.get('stock', 0, type=int)
        category_id = request.form.get('category_id', type=int)
        image_url = request.form.get('image_url', '').strip()
        is_featured = 'is_featured' in request.form
        if not name or not price:
            flash('Name and price are required.', 'danger')
            return render_template('admin/product_form.html', categories=categories, product=None)
        product = Product(name=name, description=description, price=price,
                          original_price=original_price, stock=stock,
                          category_id=category_id, image_url=image_url, is_featured=is_featured)
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/product_form.html', categories=categories, product=None)


@app.route('/admin/products/<int:product_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_product_edit(product_id):
    product = Product.query.get_or_404(product_id)
    categories = Category.query.all()
    if request.method == 'POST':
        product.name = request.form.get('name', '').strip()
        product.description = request.form.get('description', '')
        product.price = request.form.get('price', type=float)
        product.original_price = request.form.get('original_price', type=float)
        product.stock = request.form.get('stock', 0, type=int)
        product.category_id = request.form.get('category_id', type=int)
        product.image_url = request.form.get('image_url', '').strip()
        product.is_featured = 'is_featured' in request.form
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/product_form.html', categories=categories, product=product)


@app.route('/admin/products/<int:product_id>/delete', methods=['POST'])
@admin_required
def admin_product_delete(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted.', 'info')
    return redirect(url_for('admin_products'))


@app.route('/admin/categories')
@admin_required
def admin_categories():
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)


@app.route('/admin/categories/add', methods=['POST'])
@admin_required
def admin_category_add():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '')
    icon = request.form.get('icon', 'fas fa-tag')
    if not name:
        flash('Category name is required.', 'danger')
        return redirect(url_for('admin_categories'))
    cat = Category(name=name, description=description, icon=icon)
    db.session.add(cat)
    db.session.commit()
    flash('Category added!', 'success')
    return redirect(url_for('admin_categories'))


@app.route('/admin/categories/<int:cat_id>/delete', methods=['POST'])
@admin_required
def admin_category_delete(cat_id):
    cat = Category.query.get_or_404(cat_id)
    db.session.delete(cat)
    db.session.commit()
    flash('Category deleted.', 'info')
    return redirect(url_for('admin_categories'))


@app.route('/admin/orders')
@admin_required
def admin_orders():
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    q = Order.query
    if status:
        q = q.filter_by(status=status)
    orders = q.order_by(Order.created_at.desc()).paginate(page=page, per_page=15)
    return render_template('admin/orders.html', orders=orders, status=status)


@app.route('/admin/orders/<int:order_id>/update', methods=['POST'])
@admin_required
def admin_order_update(order_id):
    order = Order.query.get_or_404(order_id)
    order.status = request.form.get('status', order.status)
    db.session.commit()
    flash('Order status updated.', 'success')
    return redirect(url_for('admin_orders'))


@app.route('/admin/users')
@admin_required
def admin_users():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=15)
    return render_template('admin/users.html', users=users)


@app.route('/admin/users/<int:user_id>/toggle-admin', methods=['POST'])
@admin_required
def admin_toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id != session['user_id']:
        user.is_admin = not user.is_admin
        db.session.commit()
        flash(f'Admin status updated for {user.username}.', 'success')
    return redirect(url_for('admin_users'))


# ===== ERROR HANDLERS =====

@app.errorhandler(404)
def not_found(e):
    return render_template('not_found.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('not_found.html', error=500), 500


# ===== SEED DATA =====

def seed_data():
    if Category.query.count() > 0:
        return

    categories = [
        Category(name='Electronics', description='Phones, laptops, gadgets', icon='fas fa-laptop'),
        Category(name='Clothing', description='Fashion for men and women', icon='fas fa-tshirt'),
        Category(name='Food & Drinks', description='Fresh food and beverages', icon='fas fa-utensils'),
        Category(name='Books', description='Educational and entertainment books', icon='fas fa-book'),
        Category(name='Sports', description='Sports equipment and gear', icon='fas fa-futbol'),
        Category(name='Home & Living', description='Furniture and home decor', icon='fas fa-home'),
    ]
    for cat in categories:
        db.session.add(cat)
    db.session.flush()

    electronics = categories[0]
    clothing = categories[1]
    food = categories[2]
    books = categories[3]
    sports = categories[4]
    home = categories[5]

    products = [
        Product(name='iPhone 15 Pro', description='Apple iPhone 15 Pro with A17 Pro chip, 48MP camera, titanium design.',
                price=999.99, original_price=1199.99, stock=15, category_id=electronics.id,
                image_url='https://picsum.photos/seed/iphone/400/300', is_featured=True),
        Product(name='Samsung Galaxy S24', description='Samsung flagship phone with Snapdragon 8 Gen 3.',
                price=849.99, original_price=999.99, stock=12, category_id=electronics.id,
                image_url='https://picsum.photos/seed/samsung/400/300', is_featured=True),
        Product(name='MacBook Pro 14"', description='Apple MacBook Pro with M3 chip, 16GB RAM, 512GB SSD.',
                price=1999.99, original_price=2199.99, stock=8, category_id=electronics.id,
                image_url='https://picsum.photos/seed/macbook/400/300', is_featured=True),
        Product(name='Sony WH-1000XM5', description='Premium noise cancelling wireless headphones.',
                price=279.99, original_price=349.99, stock=20, category_id=electronics.id,
                image_url='https://picsum.photos/seed/headphone/400/300', is_featured=False),
        Product(name='iPad Air', description='iPad Air with M1 chip, 10.9 inch display.',
                price=599.99, original_price=699.99, stock=10, category_id=electronics.id,
                image_url='https://picsum.photos/seed/ipad/400/300', is_featured=True),
        Product(name='Men\'s Classic T-Shirt', description='Premium cotton t-shirt, available in multiple colors.',
                price=19.99, original_price=29.99, stock=100, category_id=clothing.id,
                image_url='https://picsum.photos/seed/tshirt/400/300', is_featured=False),
        Product(name='Women\'s Summer Dress', description='Light and elegant summer dress with floral print.',
                price=49.99, original_price=69.99, stock=50, category_id=clothing.id,
                image_url='https://picsum.photos/seed/dress/400/300', is_featured=True),
        Product(name='Denim Jeans', description='Classic slim fit denim jeans for all occasions.',
                price=59.99, original_price=79.99, stock=60, category_id=clothing.id,
                image_url='https://picsum.photos/seed/jeans/400/300', is_featured=False),
        Product(name='Running Sneakers', description='Lightweight athletic shoes for running and sports.',
                price=89.99, original_price=120.00, stock=35, category_id=clothing.id,
                image_url='https://picsum.photos/seed/sneakers/400/300', is_featured=True),
        Product(name='Organic Coffee Beans', description='100% organic Arabica coffee beans, medium roast.',
                price=14.99, original_price=None, stock=200, category_id=food.id,
                image_url='https://picsum.photos/seed/coffee/400/300', is_featured=False),
        Product(name='Green Tea Pack', description='Premium Japanese green tea, 50 bags pack.',
                price=9.99, original_price=12.99, stock=150, category_id=food.id,
                image_url='https://picsum.photos/seed/greentea/400/300', is_featured=False),
        Product(name='Dark Chocolate Box', description='Assorted premium dark chocolates from Belgium.',
                price=24.99, original_price=None, stock=80, category_id=food.id,
                image_url='https://picsum.photos/seed/chocolate/400/300', is_featured=True),
        Product(name='Python Programming', description='Complete Python programming guide for beginners to advanced.',
                price=39.99, original_price=55.00, stock=40, category_id=books.id,
                image_url='https://picsum.photos/seed/python/400/300', is_featured=True),
        Product(name='Flask Web Development', description='Building web applications with Python and Flask.',
                price=34.99, original_price=45.00, stock=30, category_id=books.id,
                image_url='https://picsum.photos/seed/flaskbook/400/300', is_featured=False),
        Product(name='The Art of War', description='Ancient wisdom by Sun Tzu for modern life.',
                price=12.99, original_price=None, stock=60, category_id=books.id,
                image_url='https://picsum.photos/seed/artofwar/400/300', is_featured=False),
        Product(name='Football', description='Official size professional football, FIFA approved.',
                price=34.99, original_price=49.99, stock=45, category_id=sports.id,
                image_url='https://picsum.photos/seed/football/400/300', is_featured=False),
        Product(name='Yoga Mat', description='Non-slip eco-friendly yoga mat, 6mm thick.',
                price=29.99, original_price=39.99, stock=55, category_id=sports.id,
                image_url='https://picsum.photos/seed/yogamat/400/300', is_featured=True),
        Product(name='Dumbbell Set', description='Adjustable dumbbell set 5-25kg for home gym.',
                price=149.99, original_price=199.99, stock=20, category_id=sports.id,
                image_url='https://picsum.photos/seed/dumbbell/400/300', is_featured=False),
        Product(name='Ergonomic Chair', description='Office ergonomic chair with lumbar support.',
                price=299.99, original_price=399.99, stock=15, category_id=home.id,
                image_url='https://picsum.photos/seed/chair/400/300', is_featured=True),
        Product(name='LED Desk Lamp', description='Adjustable LED desk lamp with touch control.',
                price=45.99, original_price=59.99, stock=40, category_id=home.id,
                image_url='https://picsum.photos/seed/lamp/400/300', is_featured=False),
    ]
    for p in products:
        db.session.add(p)

    admin = User(username='admin', email='admin@shopkh.com', is_admin=True)
    admin.set_password('admin123')
    db.session.add(admin)

    db.session.commit()
    print("Seed data created successfully!")


# ===== MAIN =====

with app.app_context():
    db.create_all()
    seed_data()

if __name__ == '__main__':
    app.run(debug=True)
