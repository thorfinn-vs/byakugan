import json
import re

def parse_framework_error(error_response):
    """
    Extracts required schema field names and inferred data types from validation error outputs.
    
    Supported Frameworks & Error Schemas:
    - FastAPI / Pydantic (Python)
    - Django REST Framework (Python)
    - Express / Zod / Joi (Node.js)
    - Spring Boot / Jackson (Java)
    
    :param error_response: Raw response string or decoded JSON from target API
    :return: Dict mapping field names to inferred types, e.g. {"email": "string", "age": "number"}
    """
    discovered_fields = {}

    if not error_response:
        return discovered_fields

    if isinstance(error_response, str):
        try:
            error_data = json.loads(error_response)
        except json.JSONDecodeError:
            error_data = error_response
    else:
        error_data = error_response

    # 1. List-based validation errors (FastAPI/Pydantic & Zod/Joi)
    if isinstance(error_data, list):
        for err in error_data:
            if isinstance(err, dict):
                # Pydantic schema: [{"loc": ["body", "email"], "msg": "field required", "type": "value_error.missing"}]
                if "loc" in err and isinstance(err["loc"], list):
                    field_path = [str(x) for x in err["loc"] if x != "body"]
                    if field_path:
                        field_name = field_path[-1]
                        err_type = str(err.get("type", "")).lower()
                        inferred_type = "string"
                        if any(t in err_type for t in ["int", "num", "float"]):
                            inferred_type = "number"
                        elif "bool" in err_type:
                            inferred_type = "boolean"
                        discovered_fields[field_name] = inferred_type

                # Zod/Joi schema: [{"code": "invalid_type", "expected": "string", "path": ["username"]}]
                elif "path" in err and isinstance(err["path"], list):
                    if len(err["path"]) > 0:
                        field_name = str(err["path"][-1])
                        expected_type = str(err.get("expected", "string")).lower()
                        if expected_type in ["number", "integer", "float"]:
                            inferred_type = "number"
                        elif expected_type in ["boolean", "bool"]:
                            inferred_type = "boolean"
                        else:
                            inferred_type = "string"
                        discovered_fields[field_name] = inferred_type

    # 2. Dictionary-based validation errors (Django REST Framework & generic web APIs)
    elif isinstance(error_data, dict):
        for field, messages in error_data.items():
            if field == "detail":
                continue

            field_name = str(field)
            msg_str = ""
            if isinstance(messages, list) and len(messages) > 0:
                msg_str = str(messages[0]).lower()
            elif isinstance(messages, str):
                msg_str = messages.lower()

            inferred_type = "string"
            if any(t in msg_str for t in ["integer", "number", "float"]):
                inferred_type = "number"
            elif any(t in msg_str for t in ["boolean", "bool"]):
                inferred_type = "boolean"

            discovered_fields[field_name] = inferred_type

    # 3. Text/Traceback regex parsing (Java Spring Boot / Jackson)
    elif isinstance(error_data, str):
        unrecognized_matches = re.findall(r'Unrecognized field [\\"]*([a-zA-Z0-9_]+)[\\"]*', error_data)
        for field in unrecognized_matches:
            discovered_fields[field] = "string"

        spring_matches = re.findall(r"on field ['\"]([a-zA-Z0-9_]+)['\"]", error_data)
        for field in spring_matches:
            discovered_fields[field] = "string"

    return discovered_fields
