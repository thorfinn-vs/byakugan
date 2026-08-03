import json
import re

def parse_framework_error(error_response):
    """
    Extracts required schema field names and inferred data types from validation error outputs.
    
    Supported Framework & Error Schemas:
    1. FastAPI / Pydantic (Python)
    2. Django REST Framework (Python)
    3. Express / Zod / Joi (Node.js / TypeScript)
    4. PHP / Laravel Validation (PHP)
    5. ASP.NET Core RFC 7231 ProblemDetails (C#)
    6. Ruby on Rails ActiveModel (Ruby)
    7. Go / Gin Validator (Golang)
    8. Java Spring Boot / Jackson (Java)
    9. Custom REST JSON Wrappers & Generic Error Arrays
    
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

    # Helper function to extract field name and inferred type from an error object dict
    def extract_from_error_item(err):
        if not isinstance(err, dict):
            return None, None

        field_name = None
        inferred_type = "string"

        # Pydantic schema: {"loc": ["body", "username"]}
        if "loc" in err and isinstance(err["loc"], list):
            field_path = [str(x) for x in err["loc"] if x != "body"]
            if field_path:
                field_name = field_path[-1]
                err_type = str(err.get("type", "")).lower()
                if any(t in err_type for t in ["int", "num", "float"]):
                    inferred_type = "number"
                elif "bool" in err_type:
                    inferred_type = "boolean"

        # Zod / Joi schema: {"path": ["username"], "expected": "string"}
        elif "path" in err and isinstance(err["path"], list):
            if len(err["path"]) > 0:
                field_name = str(err["path"][-1])
                expected = str(err.get("expected", "")).lower()
                if expected in ["number", "integer", "float"]:
                    inferred_type = "number"
                elif expected in ["boolean", "bool"]:
                    inferred_type = "boolean"

        # Rails / Custom / Go / Spring schema: {"field": "username"}, {"attribute": "username"}, {"param": "username"}
        else:
            for key in ["field", "attribute", "param", "name", "property"]:
                if key in err:
                    field_name = str(err[key])
                    break
            
            msg = str(err.get("message") or err.get("msg") or err.get("reason") or err.get("defaultMessage") or "").lower()
            if any(t in msg for t in ["integer", "number", "float"]):
                inferred_type = "number"
            elif any(t in msg for t in ["boolean", "bool"]):
                inferred_type = "boolean"

        return field_name, inferred_type

    # Case A: Top-level List of errors
    if isinstance(error_data, list):
        for err in error_data:
            fname, ftype = extract_from_error_item(err)
            if fname:
                discovered_fields[fname] = ftype

    # Case B: Top-level Dictionary
    elif isinstance(error_data, dict):
        # 1. Check if dictionary contains a nested errors array (e.g. {"errors": [...]} or {"details": [...]})
        nested_error_list = None
        for key in ["errors", "error", "details", "issues", "validationErrors", "data"]:
            if key in error_data and isinstance(error_data[key], list):
                nested_error_list = error_data[key]
                break

        if nested_error_list:
            for err in nested_error_list:
                fname, ftype = extract_from_error_item(err)
                if fname:
                    discovered_fields[fname] = ftype
        
        # 2. Check if dictionary contains a nested errors dict (e.g., Laravel / ASP.NET RFC 7231: {"errors": {"username": ["..."]}})
        elif "errors" in error_data and isinstance(error_data["errors"], dict):
            for field, messages in error_data["errors"].items():
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

        # 3. Standard Django REST / direct key-value errors dict e.g. {"username": ["This field is required"]}
        else:
            for field, messages in error_data.items():
                if field in ["detail", "status", "message", "code", "title", "type", "statusCode"]:
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

    # Case C: Plain String / Traceback
    elif isinstance(error_data, str):
        unrecognized_matches = re.findall(r'Unrecognized field [\\"]*([a-zA-Z0-9_]+)[\\"]*', error_data)
        for field in unrecognized_matches:
            discovered_fields[field] = "string"

        spring_matches = re.findall(r"on field ['\"]([a-zA-Z0-9_]+)['\"]", error_data)
        for field in spring_matches:
            discovered_fields[field] = "string"

    return discovered_fields
