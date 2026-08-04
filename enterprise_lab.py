from flask import Flask, request, jsonify
from flask_cors import CORS

enterprise_lab = Flask(__name__)
CORS(enterprise_lab)

# Simulated Enterprise SaaS Database
ENTERPRISE_DB = {
    "usr_456": {
        "id": "usr_456",
        "username": "alex_developer",
        "email": "alex@enterprise-corp.com",
        "job_title": "Senior Staff Engineer",
        "department": "Engineering",
        "organization_role": "member",
        "is_organization_owner": False,
        "permissions": ["read:logs", "write:code"],
        "billing_tier": "starter",
        "account_status": "active",
        "created_at": "2026-02-10T14:20:00Z"
    }
}

@enterprise_lab.route('/api/v2/organizations/<org_id>/users/<user_id>', methods=['GET'])
def get_enterprise_user(org_id, user_id):
    """Simulates an Enterprise REST API GET endpoint with Auth check."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({
            "type": "https://tools.ietf.org/html/rfc7235#section-3.1",
            "title": "Unauthorized",
            "status": 401,
            "detail": "Missing or invalid Bearer authentication token."
        }), 401

    user = ENTERPRISE_DB.get(user_id)
    if not user:
        return jsonify({"error": "User not found in organization"}), 404
        
    return jsonify(user)


@enterprise_lab.route('/api/v2/organizations/<org_id>/users/<user_id>', methods=['PUT', 'POST', 'PATCH'])
def update_enterprise_user(org_id, user_id):
    """
    Simulates a NestJS / ASP.NET RFC 7231 Enterprise Validation Error when mutating fields.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({
            "type": "https://tools.ietf.org/html/rfc7235#section-3.1",
            "title": "Unauthorized",
            "status": 401,
            "detail": "Missing or invalid Bearer authentication token."
        }), 401

    data = request.get_json(silent=True) or {}

    # Check for missing required enterprise profile fields
    missing_fields = []
    if "secondary_email" not in data:
        missing_fields.append("secondary_email is required and must be a valid email")
    if "phone_number" not in data:
        missing_fields.append("phone_number must be a string")
    if "emergency_contact" not in data:
        missing_fields.append("emergency_contact must be specified")

    if missing_fields:
        # NestJS / Class-Validator style response
        return jsonify({
            "statusCode": 422,
            "error": "Unprocessable Entity",
            "message": missing_fields
        }), 422

    user = ENTERPRISE_DB.get(user_id, {})
    user.update(data)
    return jsonify({"status": "success", "user": user}), 200


@enterprise_lab.route('/api/v2/organizations/<org_id>/users/<user_id>', methods=['DELETE'])
def delete_enterprise_user(org_id, user_id):
    """Simulates destructive DELETE endpoint."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Unauthorized"}), 401

    if user_id in ENTERPRISE_DB:
        del ENTERPRISE_DB[user_id]
        return jsonify({"message": f"User {user_id} removed from organization {org_id}"}), 200
    return jsonify({"error": "User not found"}), 404


@enterprise_lab.route('/api/v2/protected', methods=['GET', 'POST', 'PUT', 'DELETE'])
def protected_endpoint():
    """Mock endpoint to test 401 Unauthorized status and guidance."""
    return jsonify({
        "type": "https://tools.ietf.org/html/rfc7235#section-3.1",
        "title": "Unauthorized",
        "status": 401,
        "detail": "Missing or invalid Bearer authentication token."
    }), 401


@enterprise_lab.route('/api/v2/redirect', methods=['GET', 'POST'])
def redirect_endpoint():
    """Mock endpoint to test 302 Redirect handling."""
    from flask import redirect
    return redirect("/api/v2/organizations/org_99/users/usr_456", code=302)


@enterprise_lab.route('/api/v2/rate-limited', methods=['GET', 'POST'])
def rate_limited_endpoint():
    """Mock endpoint to test 429 Rate Limiting handling."""
    res = jsonify({"error": "Too Many Requests", "detail": "Rate limit exceeded. Please wait 60 seconds."})
    res.status_code = 429
    res.headers["Retry-After"] = "60"
    return res


@enterprise_lab.route('/api/v2/server-error', methods=['GET', 'POST'])
def server_error_endpoint():
    """Mock endpoint to test 500 Internal Server Error & stack trace parsing."""
    res = jsonify({
        "error": "Internal Server Error",
        "exception": "DatabaseConnectionTimeout: Connection pool exhausted at db_pool.py:142",
        "traceback": [
            "File '/app/db_pool.py', line 142, in get_connection",
            "File '/app/controllers/user_service.py', line 54, in query_user_metadata"
        ]
    })
    res.status_code = 500
    return res


if __name__ == '__main__':
    print("[ENTERPRISE LAB] Listening on http://localhost:5002")
    enterprise_lab.run(host='0.0.0.0', port=5002, debug=True)

