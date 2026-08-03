def classify_fields(get_response_data, error_discovered_fields=None):
    """
    Categorizes fields extracted from GET responses and validation errors into:
    - allowed_fields: Writable properties accepted by mutating endpoints.
    - read_only_fields: System metadata properties (e.g. id, created_at) that should not be modified.
    - mass_assignment_candidates: Security-sensitive fields (e.g. role, is_admin) flagged for privilege testing.
    - required_fields: Fields explicitly flagged as missing by framework validation errors.
    
    :param get_response_data: Parsed GET response JSON object
    :param error_discovered_fields: Dict of fields inferred from validation error responses
    :return: Dict containing categorized field lists
    """
    if error_discovered_fields is None:
        error_discovered_fields = {}

    allowed_fields = []
    read_only_fields = []
    mass_assignment_candidates = []

    READ_ONLY_KEYS = {"id", "uuid", "created_at", "updated_at", "_id", "v", "__v"}
    MASS_ASSIGNMENT_KEYS = {"role", "is_admin", "admin", "permissions", "verified", "email_verified", "tier", "balance", "scope", "is_staff", "is_superuser"}

    if isinstance(get_response_data, dict):
        for key, value in get_response_data.items():
            key_lower = str(key).lower()

            if key_lower in READ_ONLY_KEYS:
                read_only_fields.append(key)
            elif key_lower in MASS_ASSIGNMENT_KEYS:
                mass_assignment_candidates.append(key)
                allowed_fields.append(key)
            else:
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

    if isinstance(get_response_data, dict):
        for key, val in get_response_data.items():
            if str(key).lower() not in {"id", "uuid", "_id", "__v"}:
                payload[key] = val

    for field, field_type in error_discovered_fields.items():
        if field not in payload:
            if field_type == "number":
                payload[field] = 0
            elif field_type == "boolean":
                payload[field] = False
            else:
                payload[field] = "sample_value"

    return payload
