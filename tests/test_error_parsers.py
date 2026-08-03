import json
import os
import sys

# Add parent directory to path so we can import parsers
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from parsers.error_parser import parse_framework_error

def run_tests():
    fixtures_path = os.path.join(os.path.dirname(__file__), '..', 'parsers', 'error_schemas.json')
    with open(fixtures_path, 'r') as f:
        schemas = json.load(f)

    print("==================================================")
    print(" BYAKUGAN ERROR PARSER SUITE - VERIFICATION ")
    print("==================================================\n")

    passed = 0
    total = len(schemas)

    for framework, payload in schemas.items():
        parsed = parse_framework_error(payload)
        if len(parsed) > 0:
            print(f"[PASS] {framework.upper()}: Discovered fields -> {list(parsed.keys())}")
            passed += 1
        else:
            print(f"[FAIL] {framework.upper()}: Failed to extract fields from payload!")

    print(f"\nResult: {passed}/{total} framework error formats parsed successfully!")

if __name__ == '__main__':
    run_tests()
