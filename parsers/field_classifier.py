"""
Field Classifier & Payload Synthesizer Module for Byakugan.

This module is responsible for analyzing extracted API parameters, categorizing properties
into functional field matrices (Allowed, Read-Only, Mass-Assignment, Required), and
synthesizing ready-to-use JSON request body payloads for penetration testing.
"""

def classify_fields(get_response_data, error_discovered_fields=None):
    """
    Categorizes fields extracted from GET responses and validation errors into:
    - allowed_fields: Writable properties accepted by mutating endpoints.
    - read_only_fields: System metadata properties (e.g. id, created_at) that should not be modified.
    - mass_assignment_candidates: Security-sensitive fields (e.g. role, is_admin) flagged for privilege testing.
    - required_fields: Fields explicitly flagged as missing by framework validation errors.
    
    :param get_response_data: Parsed GET response JSON object or list
    :param error_discovered_fields: Dict of fields inferred from validation error responses
    :return: Dict containing categorized field lists
    """
    if error_discovered_fields is None:
        error_discovered_fields = {}

    allowed_fields = []
    read_only_fields = []
    mass_assignment_candidates = []

    READ_ONLY_KEYS = {
        "id", "uuid", "guid", "created_at", "updated_at", "deleted_at", 
        "_id", "v", "__v", "created_by", "updated_by", "timestamp", "etag"
    }

    MASS_ASSIGNMENT_KEYS = {
        "role", "roles", "is_admin", "admin", "is_staff", "is_superuser", 
        "permissions", "privileges", "scope", "scopes", "verified", 
        "email_verified", "tier", "billing_tier", "plan", "balance", 
        "credits", "is_owner", "owner_id", "org_role", "organization_role"
    }

    if isinstance(get_response_data, dict):
        for key in get_response_data.keys():
            key_lower = str(key).lower()

            if key_lower in READ_ONLY_KEYS:
                if key not in read_only_fields:
                    read_only_fields.append(key)
            elif key_lower in MASS_ASSIGNMENT_KEYS:
                if key not in mass_assignment_candidates:
                    mass_assignment_candidates.append(key)
                if key not in allowed_fields:
                    allowed_fields.append(key)
            else:
                if key not in allowed_fields:
                    allowed_fields.append(key)

    elif isinstance(get_response_data, list) and len(get_response_data) > 0:
        first_item = get_response_data[0]
        if isinstance(first_item, dict):
            for key in first_item.keys():
                key_lower = str(key).lower()
                if key_lower in READ_ONLY_KEYS:
                    if key not in read_only_fields:
                        read_only_fields.append(key)
                elif key_lower in MASS_ASSIGNMENT_KEYS:
                    if key not in mass_assignment_candidates:
                        mass_assignment_candidates.append(key)
                    if key not in allowed_fields:
                        allowed_fields.append(key)
                else:
                    if key not in allowed_fields:
                        allowed_fields.append(key)

    for req_field in error_discovered_fields.keys():
        if req_field not in allowed_fields and req_field not in read_only_fields:
            allowed_fields.append(req_field)

    return {
        "allowed_fields": allowed_fields,
        "read_only_fields": read_only_fields,
        "mass_assignment_candidates": mass_assignment_candidates,
        "required_fields": list(error_discovered_fields.keys())
    }


def synthesize_payload(get_response_data, error_discovered_fields=None):
    """
    Synthesizes a valid JSON request body combining GET response structures and required error fields.
    
    :param get_response_data: Parsed GET response JSON object
    :param error_discovered_fields: Dict of fields inferred from validation error responses
    :return: Synthesized JSON payload dictionary
    """
    if error_discovered_fields is None:
        error_discovered_fields = {}

    payload = {}

    READ_ONLY_KEYS = {"id", "uuid", "guid", "_id", "v", "__v", "created_at", "updated_at"}

    if isinstance(get_response_data, dict):
        for key, val in get_response_data.items():
            if str(key).lower() not in READ_ONLY_KEYS:
                payload[key] = val

    elif isinstance(get_response_data, list) and len(get_response_data) > 0:
        first_item = get_response_data[0]
        if isinstance(first_item, dict):
            for key, val in first_item.items():
                if str(key).lower() not in READ_ONLY_KEYS:
                    payload[key] = val

    for field, field_type in error_discovered_fields.items():
        if field not in payload:
            if field_type == "number" or field_type == "integer":
                payload[field] = 0
            elif field_type == "boolean":
                payload[field] = False
            elif field_type == "array" or field_type == "list":
                payload[field] = []
            elif field_type == "object" or field_type == "dict":
                payload[field] = {}
            else:
                payload[field] = "sample_value"

    return payload
