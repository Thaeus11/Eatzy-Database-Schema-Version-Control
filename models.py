from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from flask import current_app

db = SQLAlchemy()

# ===== DATABASE MODELS =====
class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    orders = db.relationship('Order', backref='customer', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'created_at': self.created_at.isoformat()
        }

class Restaurant(db.Model):
    __tablename__ = 'restaurants'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    owner_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    rating = db.Column(db.Float, default=4.5)
    description = db.Column(db.Text)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    menu_items = db.relationship('MenuItem', backref='restaurant', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='restaurant', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'owner_name': self.owner_name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'rating': self.rating,
            'description': self.description,
            'location': {
                'lat': self.latitude,
                'lng': self.longitude
            }
        }

class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100))
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    image_url = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    order_items = db.relationship('OrderItem', backref='menu_item', lazy=True)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'restaurant_id': str(self.restaurant_id),
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'price': float(self.price),
            'image_url': self.image_url
        }

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'))
    status = db.Column(db.String(50), default='Pending')
    total = db.Column(db.Numeric(10, 2))
    payment_method = db.Column(db.String(100))
    delivery_address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    estimated_delivery = db.Column(db.DateTime)
    
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'order_number': self.order_number,
            'customer_id': str(self.customer_id),
            'restaurant_id': str(self.restaurant_id) if self.restaurant_id else None,
            'items': [item.to_dict() for item in self.items],
            'total': float(self.total) if self.total else None,
            'status': self.status,
            'payment_method': self.payment_method,
            'delivery_address': self.delivery_address,
            'created_at': self.created_at.isoformat(),
            'estimated_delivery': self.estimated_delivery.isoformat() if self.estimated_delivery else None
        }


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)  # Snapshot of item name
    price = db.Column(db.Numeric(10, 2), nullable=False)  # Snapshot of item price
    quantity = db.Column(db.Integer, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': float(self.price),
            'quantity': self.quantity
        }

def init_db():
    """Initialize database tables"""
    db.create_all()
    print("Database tables created")
