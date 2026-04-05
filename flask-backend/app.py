from flask import Flask, request, jsonify

app = Flask(__name__)

# Mock database for restaurant data
menu_items = [
    {"id": 1, "name": "Margherita Pizza", "price": 15.99, "category": "Main"},
    {"id": 2, "name": "Truffle Pasta", "price": 18.50, "category": "Main"},
    {"id": 3, "name": "Garlic Bread", "price": 4.50, "category": "Dessert"},
    {"id": 4, "name": "Caesar Salad", "price": 12.00, "category": "Salad"}
]

orders = []

@app.route('/api/menu', methods=['GET'])
def get_menu():
    """Returns the full restaurant menu."""
    return jsonify({"menu": menu_items}), 200

@app.route('/api/menu/<int:item_id>', methods=['GET'])
def get_menu_item(item_id):
    """Returns a specific menu item by ID."""
    item = next((item for item in menu_items if item['id'] == item_id), None)
    if item:
        return jsonify(item), 200
    return jsonify({"error": "Item not found"}), 404

@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Returns all current orders."""
    return jsonify({"orders": orders}), 200

@app.route('/api/orders', methods=['POST'])
def create_order(request_data):
    """Creates a new order by accepting JSON data."""
    # In a real application, request_data would be passed as an argument or retrieved from the via request.get_json()
    # For this implementation, we follow the logic in the skill guidelines
    
    # We use the standard Flask request object directly
    data = request.get_json()
    if not data or 'items' not in data:
        return jsonify({"error": "Invalid order format. 'items' must be a list of IDs."}), 400
        
    # Validate item IDs
    order_items = []
    for item_id in data['items']:
        item = next((item for item in menu_items if item['id'] == item_id), None)
            
        if item:
            order_items.append(item)
        else:
            return jsonify({"error": f"Item with ID {item_id} not found in menu."}), 404
            
    if not order_items:
        return jsonify({"error": "No valid items selected for the order."}), 400

    # Create the order object
    new_order = {
        "order_id": len(orders) + 1,
        "items": order_items,
        "total_price": sum(item['price'] for item in order_items),
        "status": "pending"
    }
    orders.append(new_order)
    return jsonify(new_order), 201

@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order_details(order_id):
    """Retrieves details of a specific order."""
    order = next((order for order in orders if order['order_id'] == order_id), None)
    if order:
        return jsonify(order), 200
    return jsonify({"error": "Order not found"}), 404

if __name__ == '__main__':
    # Run the server on port 5000 with debug mode enabled
    app.run(host='0.0.0.0', port=5000, debug=True)
