from flask import Flask, request, jsonify
from flask_cors import CORS

lab = Flask(__name__)
CORS(lab)

# Simulated target dataset
USERS_DB = {
    "123": {
        "id": 123,
        "username": "johndoe",
        "email": "johndoe@example.com",
        "role": "user",
        "is_admin": False,
        "tier": "free",
        "created_at": "2026-01-15T08:30:00Z"
    }
}

@lab.route('/api/v1/users/<user_id>', methods=['GET'])
def get_user(user_id):
    user = USERS_DB.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user)

@lab.route('/api/v1/users/<user_id>', methods=['PUT', 'POST', 'PATCH'])
def update_user(user_id):
    data = request.get_json(silent=True) or {}
    missing_errors = []

    if "phone_number" not in data:
        missing_errors.append({
            "loc": ["body", "phone_number"],
            "msg": "field required",
            "type": "value_error.missing"
        })

    if "age" not in data:
        missing_errors.append({
            "loc": ["body", "age"],
            "msg": "field required",
            "type": "value_error.missing"
        })

    if missing_errors:
        return jsonify(missing_errors), 422

    user = USERS_DB.get(user_id, {})
    user.update(data)
    return jsonify({"status": "success", "updated_user": user}), 200

@lab.route('/api/v1/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    if user_id in USERS_DB:
        del USERS_DB[user_id]
        return jsonify({"message": f"User {user_id} deleted successfully"}), 200
    return jsonify({"error": "User not found"}), 404

if __name__ == '__main__':
    print("[LAB] Target server listening on http://localhost:5001")
    lab.run(host='0.0.0.0', port=5001, debug=True)
