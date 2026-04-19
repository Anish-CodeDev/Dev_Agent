from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Database Configuration
# Using SQLite for demonstration; in production, use PostgreSQL or MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///orderflowpro.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "customer_name": self.customer_name,
            "product_name": self.product_name,
            "quantity": self.quantity,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

# Database Initialization
with app.app_context():
    db.create_all()

# API Endpoints

@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Fetch all orders from the database."""
    orders = Order.query.all()
    return jsonify([order.to_dict() for order in orders]), 200

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Create a new order in the database."""
    data = request.get_json(force=True)
    if not data or 'customer_name' not in data or 'product_name' not in data or 'quantity' not in data:
        return jsonify({"error": "Invalid data. Required: customer_name, product_name, quantity"}), 400
    
    try:
        new_order = Order(
            customer_name=data['customer_name'],
            product_name=data['product_name'],
            quantity=data['quantity']
        )
        db.session.add(new_order)
        db.session.commit()
        return jsonify(new_order.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Fetch a single order by ID."""
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    return jsonify(order.to_dict()), 200

@app.route('/api/orders/<int:order_id>', methods=['PATCH'])
def update_order_status(order_id):
    """Update the status of an order (e.g., Pending -> Shipped)."""
    data = request.get_json()
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify({"error": "Order not found"}), 404
    
    if not data or 'status' not in data:
        return jsonify({"error": "Missing status field in payload"}), 400

    try:
        order.status = data['status']
        db.session.commit()
        return jsonify(order.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/orders/<int:order_id>', methods=['DELETE'])
def get_order_deletion(order_id):
    """Delete an order from the database."""
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    
    try:
        db.session.delete(order)
        db.session.commit()
        return jsonify({"message": "Order deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
