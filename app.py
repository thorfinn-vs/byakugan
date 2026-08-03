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
        "get_response_data": None,
        "error_logs": [],
        "field_analysis": {},
        "synthesized_payload": {}
    }

    # 1. Probe OPTIONS for CORS/Allowed verbs
    try:
        opt_res = requests.options(url, headers=request_headers, timeout=5)
        allow_header = opt_res.headers.get("Allow") or opt_res.headers.get("Access-Control-Allow-Methods")
        if allow_header:
            results["method_status"]["OPTIONS_Allowed"] = allow_header
    except Exception as e:
        results["method_status"]["OPTIONS_Error"] = str(e)

    # 2. Probe GET for baseline object structure
    if "GET" in [m.upper() for m in methods]:
        try:
            get_res = requests.get(url, headers=request_headers, timeout=5)
            results["method_status"]["GET"] = get_res.status_code
            if get_res.status_code == 200:
                try:
                    results["get_response_data"] = get_res.json()
                except Exception:
                    results["get_response_data"] = {"raw": get_res.text[:500]}
        except Exception as e:
            results["method_status"]["GET_Error"] = str(e)

    # Initialize get_data safely before parsing errors
    get_data = results["get_response_data"] if isinstance(results["get_response_data"], dict) else {}

    # 3. Probe mutating verbs (POST, PUT, PATCH) to extract validation schemas
    error_discovered_fields = {}
    for method in ["POST", "PUT", "PATCH"]:
        if method in [m.upper() for m in methods]:
            try:
                req_func = getattr(requests, method.lower())
                res = req_func(url, headers=request_headers, json={}, timeout=5)
                results["method_status"][method] = res.status_code

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
