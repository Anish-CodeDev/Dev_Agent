from flask import Flask, request, jsonify

app = Flask(__name__)

# Mock Database
menu_items = [
    {"id": 1, "name": "Margherita Pizza", "price": 15.99, "category": "Main"},
    {"id": 2, "name": "Truffle Pasta", "price": 18.50, "category": "Main"},
    {"id": 3, "name": "Garlic Bread", "price": 4.50, "category": "Side"},
    {"id": 4, "name": "Margherita Pizza", "price": 15.99, "category": "Main"},
    {"id": 5, "name": "Caesar Salad", "price": 12.00, "category": "Salad"}
]

orders = []

@app.route('/api/menu', methods=['GET'])
def get_menu():
    return jsonify({"menu": menu_items}), 200

@app.route('/api/menu/<int:item_id>', methods=['GET'])
def get_menu_item(item_id):
    item = next((item for item in menu_items if item['id'] == item_id), None)
    if item:
        return jsonify(item), 200
    return jsonify({"error": "Item not found"}), 404

@app.route('/api/order', methods=['POST'])
def place_order():
    data = request.get_json()
    if not data or 'items' not in data:
        return jsonify({"error": "Invalid order format. 'items' list is required."}), 400
    
    new_order = {
        "order_id": len(orders) + 1,
        "items": data['items'],
        "total_price": sum(item['price'] * item['quantity'] for item in data['items']),
        "status": "pending"
    }
    
    # Check if items actually exist in the menu
    for item in data['items']:
        if not any(m['id'] == item.get('id') for m in menu_items):
            return jsonify({"error": f"Item ID {item.get('id')} not found in menu"}), 400

    orders.append(new_order)
    return jsonify({"message": "Order placed successfully", "order": new_order}), 201

@app.route('/api/orders', methods=['GET'])
def get_orders():
    return jsonify({"orders": orders}), 200

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({"status": "online", "restaurant": "The Flask Bistro"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)