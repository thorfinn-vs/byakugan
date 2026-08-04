import os
import json
import requests
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

from parsers.error_parser import parse_framework_error
from parsers.field_classifier import classify_fields, synthesize_payload

app = Flask(__name__, template_folder='templates')
CORS(app)

@app.route('/')
def index():
    """Serves the Byakugan Web UI application."""
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    return send_file(os.path.join(templates_dir, 'index.html'))

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring service status."""
    return jsonify({
        "status": "online",
        "service": "Byakugan Backend Server",
        "version": "1.0.0"
    })

def analyze_http_response(res, method):
    """
    Extracts response headers, body snippet, status phrase, and security guidance
    for the target HTTP response.
    """
    status_code = res.status_code
    reason = res.reason
    headers_dict = dict(res.headers)
    body_text = res.text[:4000] if res.text else ""

    guidance = None
    auth_warning = False
    redirect_target = None

    if status_code in [401, 403]:
        auth_warning = True
        guidance = "Authentication Required: Provide a valid Authorization header (e.g., 'Bearer <token>') or Cookie in the request settings."
    elif status_code in [301, 302, 307, 308]:
        redirect_target = headers_dict.get("Location") or headers_dict.get("location")
        guidance = f"Redirect Destination: Endpoint redirected to '{redirect_target}'." if redirect_target else "Redirect Destination: 3xx redirect detected."
    elif status_code == 429:
        retry_after = headers_dict.get("Retry-After") or headers_dict.get("retry-after")
        guidance = f"Rate Limit Exceeded: Server returned 429. Retry-After: {retry_after} seconds." if retry_after else "Rate Limit Exceeded."
    elif status_code >= 500:
        guidance = "Server Error (500): The server threw an unhandled exception. Inspect raw response body for stack trace or internal variable leakage."
    elif status_code in [400, 422]:
        guidance = "Validation Error (400/422): Input parameters failed framework validation rules. Automatically parsing missing required fields..."
    elif status_code == 200:
        guidance = "Success (200 OK): Request completed successfully."

    return {
        "method": method,
        "status_code": status_code,
        "reason": reason,
        "headers": headers_dict,
        "body": body_text,
        "guidance": guidance,
        "auth_warning": auth_warning,
        "redirect_target": redirect_target
    }

@app.route('/api/probe', methods=['POST'])
def probe_endpoint():
    """
    Main endpoint execution route. Probes target API endpoints for allowed HTTP verbs,
    extracts validation error schemas, and categorizes field structures.
    """
    data = request.get_json() or {}
    url = data.get("url")
    cookie = data.get("cookie")
    headers = data.get("headers", {})
    methods = data.get("methods", [])

    if not url:
        return jsonify({"error": "Target URL parameter is required."}), 400

    request_headers = {"User-Agent": "Byakugan-Security-Probe/1.0"}
    request_headers.update(headers)
    if cookie:
        request_headers["Cookie"] = cookie

    results = {
        "url": url,
        "method_status": {},
        "response_inspector": [],
        "get_response_data": None,
        "error_logs": [],
        "field_analysis": {},
        "synthesized_payload": {},
        "auth_required": False,
        "redirects_detected": []
    }

    # 1. Probe OPTIONS for CORS/Allowed verbs
    try:
        opt_res = requests.options(url, headers=request_headers, timeout=5, allow_redirects=False)
        allow_header = opt_res.headers.get("Allow") or opt_res.headers.get("Access-Control-Allow-Methods")
        if allow_header:
            results["method_status"]["OPTIONS_Allowed"] = allow_header
        
        inspector_data = analyze_http_response(opt_res, "OPTIONS")
        results["response_inspector"].append(inspector_data)
    except Exception as e:
        results["method_status"]["OPTIONS_Error"] = str(e)

    # 2. Probe GET for baseline object structure
    if "GET" in [m.upper() for m in methods]:
        try:
            get_res = requests.get(url, headers=request_headers, timeout=5, allow_redirects=False)
            results["method_status"]["GET"] = get_res.status_code
            
            inspector_data = analyze_http_response(get_res, "GET")
            results["response_inspector"].append(inspector_data)

            if inspector_data["auth_warning"]:
                results["auth_required"] = True
            if inspector_data["redirect_target"]:
                results["redirects_detected"].append({"method": "GET", "target": inspector_data["redirect_target"]})

            if get_res.status_code == 200:
                try:
                    results["get_response_data"] = get_res.json()
                except Exception:
                    results["get_response_data"] = {"raw": get_res.text[:500]}
        except Exception as e:
            results["method_status"]["GET_Error"] = str(e)

    # Initialize get_data safely before parsing errors
    get_data = results["get_response_data"] if isinstance(results["get_response_data"], dict) else {}

    # 3. Probe mutating verbs (POST, PUT, PATCH, DELETE) to extract validation schemas & log responses
    error_discovered_fields = {}
    for method in ["POST", "PUT", "PATCH", "DELETE"]:
        if method in [m.upper() for m in methods]:
            try:
                req_func = getattr(requests, method.lower())
                kwargs = {"headers": request_headers, "timeout": 5, "allow_redirects": False}
                if method != "DELETE":
                    kwargs["json"] = {}
                res = req_func(url, **kwargs)
                results["method_status"][method] = res.status_code

                inspector_data = analyze_http_response(res, method)
                results["response_inspector"].append(inspector_data)

                if inspector_data["auth_warning"]:
                    results["auth_required"] = True
                if inspector_data["redirect_target"]:
                    results["redirects_detected"].append({"method": method, "target": inspector_data["redirect_target"]})

                if res.status_code in [400, 422]:
                    results["error_logs"].append({
                        "method": method,
                        "status_code": res.status_code,
                        "response": res.text
                    })
                    parsed_fields = parse_framework_error(res.text, get_data)
                    error_discovered_fields.update(parsed_fields)
            except Exception as e:
                results["method_status"][f"{method}_Error"] = str(e)

    # 4. Classify fields and synthesize JSON payload
    results["field_analysis"] = classify_fields(get_data, error_discovered_fields)
    results["synthesized_payload"] = synthesize_payload(get_data, error_discovered_fields)

    return jsonify(results)

if __name__ == '__main__':
    print("[INFO] Byakugan server listening on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
