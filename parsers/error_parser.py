import json
import re

def parse_framework_error(error_response, get_response_data=None):
    """
    Extracts required schema field names and inferred data types from validation error outputs.
    Includes smart cross-reference matching against GET baseline response structures.
    
    Supported Frameworks & Error Schemas:
    1. FastAPI / Pydantic (Python)
    2. Django REST Framework & Flask-RESTful (Python)
    3. Express / Zod / Joi (Node.js / TypeScript)
    4. NestJS Class-Validator (TypeScript)
    5. PHP / Laravel & Symfony Validation (PHP)
    6. ASP.NET Core RFC 7231 ProblemDetails (C#)
    7. Ruby on Rails ActiveModel (Ruby)
    8. Go / Gin Validator (Golang)
    9. Java Spring Boot / Jackson (Java)
    10. GraphQL Validation & OpenAPI Error Schemas
    11. Custom REST JSON Wrappers & Generic Error Arrays
    
    :param error_response: Raw response string or decoded JSON from target API
    :param get_response_data: Optional GET response dictionary/list for smart field cross-referencing
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

        # Zod / Joi / OpenAPI schema: {"path": ["username"]} or {"path": ".body.email"}
        elif "path" in err:
            path_val = err["path"]
            if isinstance(path_val, list) and len(path_val) > 0:
                field_name = str(path_val[-1])
            elif isinstance(path_val, str):
                parts = [p for p in path_val.split('.') if p and p != "body"]
                if parts:
                    field_name = parts[-1]
            
            expected = str(err.get("expected", "")).lower()
            if expected in ["number", "integer", "float"]:
                inferred_type = "number"
            elif expected in ["boolean", "bool"]:
                inferred_type = "boolean"

        # Symfony schema: {"propertyPath": "username"}
        elif "propertyPath" in err:
            field_name = str(err["propertyPath"])

        # Rails / Custom / Go / Spring schema: {"field": "username"}, {"attribute": "username"}, {"param": "username"}
        else:
            for key in ["field", "attribute", "param", "name", "property"]:
                if key in err:
                    field_name = str(err[key])
                    break

            msg = str(err.get("message") or err.get("msg") or err.get("reason") or err.get("defaultMessage") or err.get("title") or "").lower()
            if any(t in msg for t in ["integer", "number", "float"]):
                inferred_type = "number"
            elif any(t in msg for t in ["boolean", "bool"]):
                inferred_type = "boolean"

        return field_name, inferred_type

    # Case A: Top-level List of errors (Pydantic, Zod, NestJS message arrays)
    if isinstance(error_data, list):
        for err in error_data:
            if isinstance(err, str):
                for match in re.findall(r'([a-zA-Z0-9_]+)\s+(?:must|should|is|required)', err, re.IGNORECASE):
                    discovered_fields[match] = "string"
            else:
                fname, ftype = extract_from_error_item(err)
                if fname:
                    discovered_fields[fname] = ftype

    # Case B: Top-level Dictionary
    elif isinstance(error_data, dict):
        # NestJS class-validator style: {"message": ["username must be a string"]}
        STOP_WORDS = {"and", "or", "is", "the", "a", "an", "be", "must", "should", "not", "specified", "required"}
        if "message" in error_data and isinstance(error_data["message"], list):
            for msg in error_data["message"]:
                if isinstance(msg, str):
                    matches = re.findall(r'([a-zA-Z0-9_]+)\s+(?:must|should|is|required)', msg, re.IGNORECASE)
                    for match in matches:
                        if match.lower() not in STOP_WORDS:
                            discovered_fields[match] = "string"

        # 2. Check for GraphQL errors e.g. {"errors": [{"message": "...at \"input.username\"..."}]}
        if "errors" in error_data and isinstance(error_data["errors"], list):
            for err in error_data["errors"]:
                if isinstance(err, dict) and "message" in err:
                    msg = err["message"]
                    # Extract GraphQL path e.g. at "input.username"
                    gql_matches = re.findall(r'at\s+["\']([a-zA-Z0-9_.]+)\b', msg)
                    for gql_path in gql_matches:
                        parts = gql_path.split('.')
                        discovered_fields[parts[-1]] = "string"

        # 3. Check if dictionary contains a nested errors array (e.g. {"errors": [...]}, {"violations": [...]})
        nested_error_list = None
        for key in ["errors", "error", "details", "violations", "issues", "validationErrors", "data"]:
            if key in error_data and isinstance(error_data[key], list):
                nested_error_list = error_data[key]
                break

        if nested_error_list:
            for err in nested_error_list:
                fname, ftype = extract_from_error_item(err)
                if fname:
                    discovered_fields[fname] = ftype

        # 4. Check if dictionary contains a nested errors dict (Laravel / ASP.NET: {"errors": {"username": ["..."]}})
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

        # 5. Standard Django REST / Flask-RESTful direct key-value errors dict e.g. {"message": {"username": "..."}}
        elif "message" in error_data and isinstance(error_data["message"], dict):
            for field in error_data["message"].keys():
                discovered_fields[str(field)] = "string"
        else:
            for field, messages in error_data.items():
                if field in ["detail", "status", "message", "code", "title", "type", "statusCode", "error"]:
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

    # -------------------------------------------------------------------------
    # SMART FEATURE: GET Baseline Cross-Referencing Engine
    # If error text mentions a field name that also exists in the GET baseline,
    # match it automatically regardless of how unusual the error wrapper is!
    # -------------------------------------------------------------------------
    if get_response_data and isinstance(get_response_data, dict):
        raw_error_str = str(error_response).lower()
        for get_key in get_response_data.keys():
            if get_key.lower() not in {"id", "uuid", "_id", "created_at", "updated_at", "v", "__v"}:
                pattern = r'\b' + re.escape(get_key.lower()) + r'\b'
                if re.search(pattern, raw_error_str):
                    if get_key not in discovered_fields:
                        val = get_response_data[get_key]
                        if isinstance(val, bool):
                            inferred_type = "boolean"
                        elif isinstance(val, (int, float)):
                            inferred_type = "number"
                        else:
                            inferred_type = "string"
                        discovered_fields[get_key] = inferred_type

    return discovered_fields
