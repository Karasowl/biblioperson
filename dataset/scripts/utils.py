import logging
import json
from typing import Any, Optional, Dict, List
from pathlib import Path
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

def get_nested_value(data: Dict[str, Any], path: str, default: Optional[Any] = None) -> Optional[Any]:
    """
    Retrieves a value from a nested dictionary using a dot-separated path.
    Handles basic list indexing if specified in path (e.g., 'items[0].name').

    Args:
        data: The dictionary to navigate.
        path: A dot-separated string representing the path to the desired value.
              List indices can be specified like 'list_name[index]'.
        default: The value to return if the path is not found or an error occurs.

    Returns:
        The value at the specified path, or the default value.
    """
    if not isinstance(data, dict):
        return default
        
    keys = path.split('.')
    current_value = data
    
    for key_part in keys:
        if isinstance(current_value, dict):
            # Check for list index in key_part (e.g., "my_list[0]")
            if '[' in key_part and key_part.endswith(']'):
                list_key, index_str = key_part.split('[', 1)
                index_str = index_str[:-1] # Remove trailing ']'
                
                if not list_key in current_value:
                    logging.debug(f"List key '{list_key}' not found in current dict part of path '{path}'.")
                    return default
                
                list_val = current_value.get(list_key)
                if not isinstance(list_val, list):
                    logging.debug(f"Value for key '{list_key}' is not a list in path '{path}'.")
                    return default
                
                try:
                    index = int(index_str)
                    if 0 <= index < len(list_val):
                        current_value = list_val[index]
                    else:
                        logging.debug(f"Index {index} out of bounds for list '{list_key}' in path '{path}'.")
                        return default
                except ValueError:
                    logging.debug(f"Invalid index '{index_str}' for list '{list_key}' in path '{path}'.")
                    return default
            # Regular dictionary key
            elif key_part in current_value:
                current_value = current_value[key_part]
            else:
                logging.debug(f"Key '{key_part}' not found in current dict part of path '{path}'.")
                return default
        elif isinstance(current_value, list):
            # This case would typically be handled by the list index logic above.
            # If we reach here with a list and key_part is not an index, it's likely an error in path.
            logging.debug(f"Expected a dictionary to access key '{key_part}', but found a list in path '{path}'.")
            return default
        else:
            # Reached a non-dictionary, non-list value before exhausting the path
            logging.debug(f"Path traversal failed at key '{key_part}'; encountered non-dict/list value in path '{path}'.")
            return default
            
    return current_value

def clean_filename(filename: str) -> str:
    """
    Cleans a filename by removing or replacing invalid characters for most filesystems.
    This is a basic version; more robust cleaning might be needed depending on targets.
    """
    # Remove characters that are problematic in filenames on many OSes
    # (except path separators if they are part of a relative path passed by mistake)
    # For a simple filename (not path), we can be more aggressive.
    cleaned = re.sub(r'[\\/*?:"<>|]',"", filename)
    # Replace sequences of whitespace with a single underscore
    cleaned = re.sub(r'\s+', '_', cleaned)
    # Remove leading/trailing underscores/hyphens that might result
    cleaned = cleaned.strip('_-')
    return cleaned if cleaned else "unnamed_file"


def save_to_ndjson(data_list: List[Dict[str, Any]], output_file_path: str) -> None:
    """
    Saves a list of dictionaries to an NDJSON file.
    Each dictionary is written as a JSON object on a new line.
    """
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            for item in data_list:
                json.dump(item, f, ensure_ascii=False)
                f.write('\n')
        logging.info(f"Successfully saved {len(data_list)} items to NDJSON file: {output_file_path}")
    except IOError as e:
        logging.error(f"Error writing to NDJSON file {output_file_path}: {e}")
    except TypeError as e:
        logging.error(f"TypeError during NDJSON serialization (check data types): {e}")


if __name__ == '__main__':
    print("--- Testing get_nested_value ---")
    test_dict = {
        "name": "Test Item",
        "details": {
            "type": "A",
            "metadata": {
                "id": 123,
                "status": "active"
            }
        },
        "tags": ["tag1", "tag2", "tag3"],
        "items": [
            {"item_id": "i1", "value": 100},
            {"item_id": "i2", "value": 200, "sub_item": {"name": "SubI2"}}
        ]
    }

    print(f"Value for 'name': {get_nested_value(test_dict, 'name')}") # Expected: Test Item
    print(f"Value for 'details.metadata.id': {get_nested_value(test_dict, 'details.metadata.id')}") # Expected: 123
    print(f"Value for 'details.type': {get_nested_value(test_dict, 'details.type')}") # Expected: A
    print(f"Value for 'tags[1]': {get_nested_value(test_dict, 'tags[1]')}") # Expected: tag2
    print(f"Value for 'items[0].value': {get_nested_value(test_dict, 'items[0].value')}") # Expected: 100
    print(f"Value for 'items[1].sub_item.name': {get_nested_value(test_dict, 'items[1].sub_item.name')}") # Expected: SubI2
    print(f"Value for 'non.existent.path': {get_nested_value(test_dict, 'non.existent.path')}") # Expected: None
    print(f"Value for 'details.non_existent': {get_nested_value(test_dict, 'details.non_existent', default='Not Found')}") # Expected: Not Found
    print(f"Value for 'items[2].value' (out of bounds): {get_nested_value(test_dict, 'items[2].value')}") # Expected: None
    print(f"Value for 'items[foo]' (invalid index): {get_nested_value(test_dict, 'items[foo]')}") # Expected: None
    print(f"Value for 'name.non_dict_access': {get_nested_value(test_dict, 'name.non_dict_access')}") # Expected: None

    print("\n--- Testing clean_filename ---")
    filenames_to_test = [
        "My Document: Final Version?.docx",
        "file/with/slashes.txt", # Slashes might be an issue if not part of actual path
        " leading and trailing spaces ",
        "file*with<bad>chars|pipe.pdf",
        "  multiple   spaces  here  "
    ]
    for fn in filenames_to_test:
        print(f"Original: '{fn}' -> Cleaned: '{clean_filename(fn)}'")

    print("\n--- Testing save_to_ndjson ---")
    sample_data_for_ndjson = [
        {"id": 1, "name": "Alice", "city": "Wonderland"},
        {"id": 2, "name": "Bob", "occupation": "Builder"},
        {"id": 3, "name": "Charlie", "hobbies": ["chess", "cycling"], "meta":{"source":"test"}}
    ]
    ndjson_test_path = "test_output.ndjson"
    save_to_ndjson(sample_data_for_ndjson, ndjson_test_path)
    # Verificar manualmente el contenido de test_output.ndjson
    print(f"Sample NDJSON saved to {ndjson_test_path}. Please verify its content.")
    # os.remove(ndjson_test_path) # Opcional: limpiar archivo de prueba

# --------------------------------------------------------------------------- #
#                        GENERIC RULE EVALUATOR (JSON)                        #
# --------------------------------------------------------------------------- #

OPS = {
    "eq":  lambda a, b: a == b,
    "neq": lambda a, b: a != b,
    "contains": lambda a, b: isinstance(a, str) and b in a,
    "not_contains": lambda a, b: isinstance(a, str) and b not in a,
    "exists": lambda a, b: a is not None,
    "not_exists": lambda a, b: a is None,
    "regex": lambda a, b: isinstance(a, str) and re.search(b, a) is not None,
    "gte": lambda a, b: (a is not None) and (a >= b),
    "lte": lambda a, b: (a is not None) and (a <= b),
}

def _rule_passes(actual: Any, rule: Dict[str, Any]) -> bool:
    """
    Return **True** if *actual* satisfies *rule*.
    rule := {path, op, value}
    """
    op_fn = OPS.get(rule.get("op", "eq"), OPS["eq"])
    return op_fn(actual, rule.get("value"))

# --------------------------------------------------------------------------- #
#                  FILTER & EXTRACT FROM A JSON/NDJSON OBJECT                 #
# --------------------------------------------------------------------------- #

def filter_and_extract_from_json_object(
    json_object: Dict[str, Any],
    text_property_paths: List[str],
    filter_rules: Optional[List[Dict[str, Any]]] = None,
    pointer_path: Optional[str] = None,
    date_path: Optional[str] = None,
    min_text_length: Optional[int] = None,
    max_text_length: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """
    Apply *filter_rules* and extract text/pointer/date from one JSON object.

    Returns **None** if the object is filtered out; otherwise a dict with:
        { "text", "pointer", "date_candidate", "raw_data" }
    """
    # 1) apply include / exclude rules
    if filter_rules:
        for rule in filter_rules:
            actual_val = get_nested_value(json_object, rule.get("path"))
            passed     = _rule_passes(actual_val, rule)
            if rule.get("exclude", False):   # exclude when rule passes
                if passed:
                    logger.debug(f"JSON object filtered out by EXCLUDE rule: {rule} (actual: {actual_val})")
                    return None
            else:                            # include rule
                if not passed:
                    logger.debug(f"JSON object filtered out by INCLUDE rule: {rule} (actual: {actual_val})")
                    return None

    # 2) find text (first path that yields non‑empty string)
    extracted_text: Optional[str] = None
    for p in text_property_paths:
        candidate = get_nested_value(json_object, p)
        if isinstance(candidate, str) and candidate.strip():
            extracted_text = candidate.strip()
            break
        # if candidate is list/dict, concatenate all strings inside
        if isinstance(candidate, (list, dict)):
            temp: List[str] = []
            def _dig(x):
                if isinstance(x, str):
                    temp.append(x.strip())
                elif isinstance(x, list):
                    for y in x: _dig(y)
                elif isinstance(x, dict):
                    for y in x.values(): _dig(y)
            _dig(candidate)
            if temp:
                extracted_text = "\\n\\n".join(filter(None, temp))
                break

    if not extracted_text:
        logger.debug("No text content found in JSON object after checking all paths.")
        return None

    # 3) apply length filters
    text_length = len(extracted_text)
    
    if min_text_length is not None and text_length < min_text_length:
        logger.debug(f"JSON object filtered out: text too short ({text_length} < {min_text_length})")
        return None
        
    if max_text_length is not None and text_length > max_text_length:
        logger.debug(f"JSON object filtered out: text too long ({text_length} > {max_text_length})")
        return None

    pointer = str(get_nested_value(json_object, pointer_path)) if pointer_path else None
    date_candidate = get_nested_value(json_object, date_path) if date_path else None

    logger.debug(f"JSON object passed filters. Extracted text: {'Yes' if extracted_text else 'No'}, Pointer: {pointer}, Date Candidate: {date_candidate}")
    return {
        "text": extracted_text,
        "pointer": pointer,
        "date_candidate": date_candidate,
        "raw_data": json_object,
    }