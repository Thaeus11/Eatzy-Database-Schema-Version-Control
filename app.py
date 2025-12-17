from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'eatzy-secret-key-2025'

# ===== API: CUSTOMER DASHBOARD =====
@app.route('/api/customer/dashboard', methods=['GET'])
def api_get_customer_dashboard():
    """Get dashboard data for the logged-in customer"""
    if session.get('user_type') != 'customer':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    customer_id = int(session.get('user_id'))
    orders = Order.query.filter_by(customer_id=customer_id).order_by(Order.created_at.desc()).all()
    total_orders = len(orders)
    active_orders = len([o for o in orders if o.status in ['Pending', 'Accepted', 'Preparing', 'Out for Delivery']])
    money_spent = sum(float(o.total) if o.total else 0 for o in orders if o.status in ['Completed', 'Delivered'])

    # Favorite restaurant (most orders)
    from collections import Counter
    rest_ids = [o.restaurant_id for o in orders if o.restaurant_id]
    fav_restaurant = None
    if rest_ids:
        most_common_id, _ = Counter(rest_ids).most_common(1)[0]
        rest = Restaurant.query.get(most_common_id)
        fav_restaurant = rest.name if rest else None

    # Recent orders (up to 5)
    recent_orders = []
    for o in orders[:5]:
        rest = Restaurant.query.get(o.restaurant_id) if o.restaurant_id else None
        recent_orders.append({
            'id': o.id,
            'restaurant': rest.name if rest else 'N/A',
            'total': float(o.total) if o.total else 0,
            'status': o.status,
            'date': o.created_at.strftime('%Y-%m-%d %H:%M') if o.created_at else ''
        })

    return jsonify({
        'total_orders': total_orders,
        'active_orders': active_orders,
        'money_spent': round(money_spent, 2),
        'favorite_restaurant': fav_restaurant,
        'recent_orders': recent_orders
    })

# ===== DATABASE SETUP =====
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "eatzy.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from models import db, Customer, Restaurant, MenuItem, Order, OrderItem, init_db
db.init_app(app)

# ===== ROUTES =====
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/dashboard')
def dashboard():
    """Redirect to appropriate dashboard based on user session"""
    user_type = session.get('user_type')
    if user_type == 'customer':
        return redirect('/customer/home')
    elif user_type == 'restaurant':
        return redirect('/restaurant/dashboard')
    else:
        return redirect('/')

# ===== CUSTOMER AUTHENTICATION =====
@app.route('/customer/register', methods=['GET', 'POST'])
def customer_register():
    if request.method == 'POST':
        data = request.json
        
        # Check if email exists
        if Customer.query.filter_by(email=data.get('email')).first():
            return jsonify({'status': 'error', 'message': 'Email already exists'}), 400

        # Password validation: at least 8 chars and 1 special char
        import re
        password = data.get('password', '')
        if len(password) < 8 or not re.search(r'[^A-Za-z0-9]', password):
            return jsonify({'status': 'error', 'message': 'Password must be at least 8 characters and contain a special character.'}), 400

        # Create new customer
        new_customer = Customer(
            name=data.get('name'),
            email=data.get('email'),
            password=password,
            phone=data.get('phone', ''),
            address=data.get('address', '')
        )

        db.session.add(new_customer)
        db.session.commit()

        session['user_id'] = str(new_customer.id)
        session['user_type'] = 'customer'
        return jsonify({'status': 'success', 'message': 'Registration successful'})
    
    return render_template('customer_register.html')

@app.route('/customer/login', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        data = request.json
        customer = Customer.query.filter_by(email=data.get('email')).first()
        
        if customer and customer.password == data.get('password'):
            session['user_id'] = str(customer.id)
            session['user_type'] = 'customer'
            return jsonify({'status': 'success', 'message': 'Login successful'})
        
        return jsonify({'status': 'error', 'message': 'Invalid email or password'}), 401
    
    return render_template('customer_login.html')

# ===== RESTAURANT AUTHENTICATION =====
@app.route('/restaurant/register', methods=['GET', 'POST'])
def restaurant_register():
    if request.method == 'POST':
        data = request.json
        
        # Check if email exists
        if Restaurant.query.filter_by(email=data.get('email')).first():
            return jsonify({'status': 'error', 'message': 'Email already exists'}), 400

        # Password validation: at least 8 chars and 1 special char
        import re
        password = data.get('password', '')
        if len(password) < 8 or not re.search(r'[^A-Za-z0-9]', password):
            return jsonify({'status': 'error', 'message': 'Password must be at least 8 characters and contain a special character.'}), 400

        # Create new restaurant
        location = data.get('location', {})
        new_restaurant = Restaurant(
            name=data.get('name'),
            owner_name=data.get('owner_name'),
            email=data.get('email'),
            password=password,
            phone=data.get('phone', ''),
            address=data.get('address', ''),
            description=data.get('description', ''),
            latitude=location.get('lat'),
            longitude=location.get('lng')
        )

        db.session.add(new_restaurant)
        db.session.commit()

        session['user_id'] = str(new_restaurant.id)
        session['user_type'] = 'restaurant'
        return jsonify({'status': 'success', 'message': 'Registration successful'})
    
    return render_template('restaurant_register.html')

@app.route('/restaurant/login', methods=['GET', 'POST'])
def restaurant_login():
    if request.method == 'POST':
        data = request.json
        restaurant = Restaurant.query.filter_by(email=data.get('email')).first()
        
        if restaurant and restaurant.password == data.get('password'):
            session['user_id'] = str(restaurant.id)
            session['user_type'] = 'restaurant'
            return jsonify({'status': 'success', 'message': 'Login successful'})
        
        return jsonify({'status': 'error', 'message': 'Invalid email or password'}), 401
    
    return render_template('restaurant_login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ===== CUSTOMER ROUTES =====
@app.route('/customer/home')
def customer_home():
    if session.get('user_type') != 'customer':
        return redirect('/customer/login')
    return render_template('customer_home.html')

@app.route('/customer/orders')
def customer_orders():
    if session.get('user_type') != 'customer':
        return redirect('/customer/login')
    return render_template('customer_orders.html')

@app.route('/customer/profile')
def customer_profile():
    if session.get('user_type') != 'customer':
        return redirect('/customer/login')
    return render_template('customer_profile.html')

@app.route('/customer/browse')
def customer_browse():
    if session.get('user_type') != 'customer':
        return redirect('/customer/login')
    return render_template('customer_browse.html')

@app.route('/customer/order/<int:restaurant_id>')
def customer_order(restaurant_id):
    if session.get('user_type') != 'customer':
        return redirect('/customer/login')
    restaurant = Restaurant.query.get(restaurant_id)
    if not restaurant:
        return redirect('/customer/home')
    menu_items = MenuItem.query.filter_by(restaurant_id=restaurant_id).all()
    return render_template('restaurant_menu.html', restaurant=restaurant, menu_items=menu_items)

# ===== RESTAURANT ROUTES =====
@app.route('/restaurant/dashboard')
def restaurant_dashboard():
    if session.get('user_type') != 'restaurant':
        return redirect('/restaurant/login')
    return render_template('restaurant_dashboard.html')

@app.route('/restaurant/orders')
def restaurant_orders():
    if session.get('user_type') != 'restaurant':
        return redirect('/restaurant/login')
    return render_template('restaurant_orders.html')

@app.route('/restaurant/menu')
def restaurant_menu():
    if session.get('user_type') != 'restaurant':
        return redirect('/restaurant/login')
    return render_template('restaurant_menu.html')

@app.route('/restaurant/profile')
def restaurant_profile():
    if session.get('user_type') != 'restaurant':
        return redirect('/restaurant/login')
    return render_template('restaurant_profile.html')

# ===== CHECKOUT & TRACKING =====
@app.route('/checkout')
def checkout():
    if session.get('user_type') != 'customer':
        return redirect('/customer/login')
    return render_template('checkout.html')

@app.route('/track-delivery')
def track_delivery():
    if session.get('user_type') != 'customer':
        return redirect('/customer/login')
    return render_template('track_delivery.html')

# ===== API: RESTAURANTS =====
@app.route('/api/restaurants', methods=['GET'])
def api_get_restaurants():
    """Get all restaurants"""
    restaurants = Restaurant.query.all()
    return jsonify([restaurant.to_dict() for restaurant in restaurants])

@app.route('/api/restaurants/<int:restaurant_id>', methods=['GET'])
def api_get_restaurant(restaurant_id):
    """Get restaurant by ID"""
    restaurant = Restaurant.query.get(restaurant_id)
    if not restaurant:
        return jsonify({'status': 'error', 'message': 'Restaurant not found'}), 404
    return jsonify(restaurant.to_dict())

# ===== API: MENU =====
@app.route('/api/restaurant/menu', methods=['GET'])
def api_get_loggedin_restaurant_menu():
    """Get menu items for the logged-in restaurant (for management UI)"""
    if session.get('user_type') != 'restaurant':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    restaurant_id = int(session.get('user_id'))
    items = MenuItem.query.filter_by(restaurant_id=restaurant_id).all()
    return jsonify([item.to_dict() for item in items])

@app.route('/api/menu/<int:restaurant_id>', methods=['GET'])
def api_get_menu(restaurant_id):
    """Get menu items for a restaurant"""
    items = MenuItem.query.filter_by(restaurant_id=restaurant_id).all()
    return jsonify([item.to_dict() for item in items])

# ===== API: CUSTOMER PROFILE =====
@app.route('/api/customer/profile', methods=['GET'])
def api_get_customer_profile():
    """Get customer profile"""
    if session.get('user_type') != 'customer':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    customer = Customer.query.get(int(session.get('user_id')))
    if not customer:
        return jsonify({'status': 'error', 'message': 'Customer not found'}), 404
    
    return jsonify(customer.to_dict())

@app.route('/api/customer/profile', methods=['PUT'])
def api_update_customer_profile():
    """Update customer profile"""
    if session.get('user_type') != 'customer':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    customer = Customer.query.get(int(session.get('user_id')))
    if not customer:
        return jsonify({'status': 'error', 'message': 'Customer not found'}), 404
    
    data = request.json
    customer.name = data.get('name', customer.name)
    customer.phone = data.get('phone', customer.phone)
    customer.address = data.get('address', customer.address)
    
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Profile updated', 'customer': customer.to_dict()})

# ===== API: CUSTOMER ORDERS =====
@app.route('/api/customer/orders', methods=['GET'])
def api_get_customer_orders():
    """Get orders for logged-in customer"""
    if session.get('user_type') != 'customer':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    customer_id = int(session.get('user_id'))
    orders = Order.query.filter_by(customer_id=customer_id).all()
    return jsonify([order.to_dict() for order in orders])

@app.route('/api/customer/order', methods=['POST'])
def api_create_order():
    """Create new order"""
    if session.get('user_type') != 'customer':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    data = request.json
    customer_id = int(session.get('user_id'))
    
    # Generate order number
    last_order = Order.query.order_by(Order.id.desc()).first()
    order_number = f"ORD-{(last_order.id + 1) if last_order else 1}"
    
    new_order = Order(
        order_number=order_number,
        customer_id=customer_id,
        restaurant_id=int(data.get('restaurant_id')) if data.get('restaurant_id') else None,
        status='Pending',
        total=data.get('total'),
        payment_method=data.get('payment_method'),
        delivery_address=data.get('delivery_address')
    )
    
    # Add order items
    for item in data.get('items', []):
        order_item = OrderItem(
            name=item.get('name'),
            price=item.get('price'),
            quantity=item.get('quantity')
        )
        new_order.items.append(order_item)
    
    db.session.add(new_order)
    db.session.commit()
    
    return jsonify({'status': 'success', 'order_number': new_order.order_number, 'order': new_order.to_dict()})

# ===== API: RESTAURANT PROFILE =====
@app.route('/api/restaurant/profile', methods=['GET'])
def api_get_restaurant_profile():
    """Get restaurant profile"""
    if session.get('user_type') != 'restaurant':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    restaurant = Restaurant.query.get(int(session.get('user_id')))
    if not restaurant:
        return jsonify({'status': 'error', 'message': 'Restaurant not found'}), 404
    
    return jsonify(restaurant.to_dict())

@app.route('/api/restaurant/profile', methods=['PUT'])
def api_update_restaurant_profile():
    """Update restaurant profile"""
    if session.get('user_type') != 'restaurant':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    restaurant = Restaurant.query.get(int(session.get('user_id')))
    if not restaurant:
        return jsonify({'status': 'error', 'message': 'Restaurant not found'}), 404
    
    data = request.json
    restaurant.name = data.get('name', restaurant.name)
    restaurant.owner_name = data.get('owner_name', restaurant.owner_name)
    restaurant.phone = data.get('phone', restaurant.phone)
    restaurant.address = data.get('address', restaurant.address)
    restaurant.description = data.get('description', restaurant.description)
    
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Profile updated', 'restaurant': restaurant.to_dict()})

# ===== API: RESTAURANT ORDERS =====
@app.route('/api/restaurant/orders', methods=['GET'])
def api_get_restaurant_orders():
    """Get orders for logged-in restaurant"""
    if session.get('user_type') != 'restaurant':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    restaurant_id = int(session.get('user_id'))
    orders = Order.query.filter_by(restaurant_id=restaurant_id).all()
    return jsonify([order.to_dict() for order in orders])

@app.route('/api/restaurant/dashboard', methods=['GET'])
def api_get_restaurant_dashboard():
    """Get restaurant dashboard data"""
    if session.get('user_type') != 'restaurant':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    restaurant_id = int(session.get('user_id'))
    
    # Get orders
    orders = Order.query.filter_by(restaurant_id=restaurant_id).all()
    active_orders = [o for o in orders if o.status in ['Pending', 'Accepted', 'Preparing', 'Out for Delivery']]
    
    # Calculate totals
    total_revenue = sum(float(o.total) if o.total else 0 for o in orders if o.status == 'Completed')
    
    # Get menu count
    menu_count = MenuItem.query.filter_by(restaurant_id=restaurant_id).count()
    
    # Get recent orders with customer name and formatted date
    recent_orders = []
    for o in orders[-5:]:
        cust = Customer.query.get(o.customer_id) if o.customer_id else None
        recent_orders.append({
            'id': o.id,
            'customer': cust.name if cust else 'Guest',
            'total': float(o.total) if o.total else 0,
            'status': o.status,
            'date': o.created_at.strftime('%Y-%m-%d %H:%M') if o.created_at else ''
        })
    
    return jsonify({
        'name': Restaurant.query.get(restaurant_id).name,
        'total_orders': len(orders),
        'active_orders': len(active_orders),
        'today_revenue': total_revenue,
        'menu_count': menu_count,
        'recent_orders': recent_orders
    })

# ===== API: ORDERS =====
@app.route('/api/orders/<int:order_id>', methods=['GET'])
def api_get_order(order_id):
    """Get order by ID"""
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'status': 'error', 'message': 'Order not found'}), 404
    
    # Check if user has access
    if session.get('user_type') == 'customer' and order.customer_id != int(session.get('user_id')):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    if session.get('user_type') == 'restaurant' and order.restaurant_id != int(session.get('user_id')):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    return jsonify(order.to_dict())

@app.route('/api/orders/<int:order_id>', methods=['PUT'])
def api_update_order(order_id):
    """Update order status"""
    if session.get('user_type') != 'restaurant':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'status': 'error', 'message': 'Order not found'}), 404
    
    if order.restaurant_id != int(session.get('user_id')):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    data = request.json
    order.status = data.get('status', order.status)
    
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Order updated', 'order': order.to_dict()})


@app.route('/api/restaurants/<int:restaurant_id>/menu', methods=['GET'])
def api_get_restaurant_menu_alias(restaurant_id):
    # Alias for /api/menu/<restaurant_id>
    items = MenuItem.query.filter_by(restaurant_id=restaurant_id).all()
    return jsonify([item.to_dict() for item in items])

@app.route('/api/menu/add', methods=['POST'])
def api_add_menu_item():
    if session.get('user_type') != 'restaurant':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    data = request.json
    restaurant_id = int(session.get('user_id'))
    name = data.get('name')
    category = data.get('category')
    description = data.get('description', '')
    price = data.get('price')
    image_url = data.get('image_url') or 'https://via.placeholder.com/150?text=Food'
    # Auto-increment ID
    last_item = MenuItem.query.order_by(MenuItem.id.desc()).first()
    new_item = MenuItem(
        id=(last_item.id + 1) if last_item else 1,
        restaurant_id=restaurant_id,
        name=name,
        category=category,
        description=description,
        price=price,
        image_url=image_url
    )
    db.session.add(new_item)
    db.session.commit()
    return jsonify({'status': 'success', 'item': new_item.to_dict()})

@app.route('/api/menu/<int:item_id>', methods=['PUT'])
def api_update_menu_item_json(item_id):
    if session.get('user_type') != 'restaurant':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    item = MenuItem.query.get(item_id)
    if not item:
        return jsonify({'status': 'error', 'message': 'Menu item not found'}), 404
    if item.restaurant_id != int(session.get('user_id')):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    data = request.json
    item.name = data.get('name', item.name)
    item.category = data.get('category', item.category)
    item.description = data.get('description', item.description)
    item.price = data.get('price', item.price)
    item.image_url = data.get('image_url', item.image_url)
    db.session.commit()
    return jsonify({'status': 'success', 'item': item.to_dict()})

@app.route('/api/menu/<int:item_id>', methods=['DELETE'])
def api_delete_menu_item_json(item_id):
    if session.get('user_type') != 'restaurant':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    item = MenuItem.query.get(item_id)
    if not item:
        return jsonify({'status': 'error', 'message': 'Menu item not found'}), 404
    if item.restaurant_id != int(session.get('user_id')):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    db.session.delete(item)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Menu item deleted'})

@app.route('/api/orders', methods=['POST'])
def api_create_order_json():
    if session.get('user_type') != 'customer':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    data = request.json
    customer_id = int(session.get('user_id'))
    last_order = Order.query.order_by(Order.id.desc()).first()
    order_id = (last_order.id + 1) if last_order else 1
    order_number = f"ORD-{order_id}"
    new_order = Order(
        id=order_id,
        order_number=order_number,
        customer_id=customer_id,
        restaurant_id=int(data.get('restaurant_id')) if data.get('restaurant_id') else None,
        status='Pending',
        total=data.get('total'),
        payment_method=data.get('payment_method'),
        delivery_address=data.get('delivery_address'),
        created_at=datetime.now(),
        estimated_delivery=None
    )
    for item in data.get('items', []):
        order_item = OrderItem(
            menu_item_id=item.get('id'),
            name=item.get('name'),
            price=item.get('price'),
            quantity=item.get('quantity')
        )
        new_order.items.append(order_item)
    db.session.add(new_order)
    db.session.commit()
    return jsonify({'status': 'success', 'order_number': new_order.order_number, 'order': new_order.to_dict()})

@app.route('/api/orders/<int:order_id>', methods=['GET'])
def api_get_order_json(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'status': 'error', 'message': 'Order not found'}), 404
    # Only allow access if user is customer (their order) or restaurant (their order)
    if session.get('user_type') == 'customer' and order.customer_id != int(session.get('user_id')):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    if session.get('user_type') == 'restaurant' and order.restaurant_id != int(session.get('user_id')):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    return jsonify(order.to_dict())

@app.route('/api/orders/<int:order_id>', methods=['PUT'])
def api_update_order_json(order_id):
    if session.get('user_type') != 'restaurant':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'status': 'error', 'message': 'Order not found'}), 404
    if order.restaurant_id != int(session.get('user_id')):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    data = request.json
    order.status = data.get('status', order.status)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Order updated', 'order': order.to_dict()})

@app.route('/user_account')
def user_account():
    user_type = session.get('user_type')
    if user_type == 'customer':
        return redirect('/customer/profile')
    elif user_type == 'restaurant':
        return redirect('/restaurant/profile')
    else:
        return redirect('/')

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True, port=5000)
