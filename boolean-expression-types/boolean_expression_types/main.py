import os
import argparse
from typing import Dict, Any, List, Tuple
import re
import logging
import json
from ruamel.yaml import YAML
import io
import traceback
import sys

yaml = YAML()
yaml.default_flow_style = False
yaml.preserve_quotes = True
yaml.indent(mapping=2, sequence=4, offset=2)
yaml.preserve_null = True
yaml.width = 4096
yaml.representer.add_representer(type(None), lambda self, data: self.represent_scalar('tag:yaml.org,2002:null', 'null'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_error_with_line_number(error_message):
    exc_type, exc_value, exc_traceback = sys.exc_info()
    line_number = traceback.extract_tb(exc_traceback)[-1][1]
    logger.error(f"{error_message} (Line {line_number})")

def read_all_hml_files(directory: str) -> Dict[str, str]:
    hml_files = {}
    for root, dirs, files in os.walk(directory):
        # Skip node_modules directories
        if 'node_modules' in dirs:
            dirs.remove('node_modules')
        for filename in files:
            if filename.endswith('.hml') or filename.endswith('.yaml') or filename.endswith('.yml'):
                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, 'r') as file:
                        hml_files[file_path] = file.read()
                except Exception as e:
                    logger.warning(f"Error reading file {file_path}: {str(e)}")
    return hml_files

def parse_hml_content(content: str, filename: str) -> List[Dict[str, Any]]:
    try:
        return list(yaml.load_all(content))
    except Exception as e:
        # Provide more context in the error message
        snippet = '\n'.join(content.split('\n')[:5])  # First 5 lines of the file
        raise ValueError(f"Error parsing YAML in file {filename}:\n{str(e)}\nFile snippet:\n{snippet}")

def normalize_name(name: str) -> str:
    # Remove any non-alphanumeric characters and convert to lowercase
    normalized = re.sub(r'[^a-zA-Z0-9]', '', name).lower()
    return normalized

def cap(string):
    if string is None:
        return ""
    elif len(string) == 0:
        return ""
    else:
        return string[0].upper() + string[1:]

def capitalize_object_type_name(name: str) -> str:
    # Split the name by underscores or spaces, capitalize each part, and join
    return ''.join(cap(word) for word in re.split(r'[_\s]', name))

def sanitize_name(name: str) -> str:
    # Remove any non-alphanumeric characters
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '', name)
    # Ensure the name starts with a letter or underscore
    if sanitized and not sanitized[0].isalpha() and sanitized[0] != '_':
        sanitized = '_' + sanitized
    # If the name is empty after sanitization, use a default name
    return sanitized if sanitized else '_Unknown'

def process_hml_file(content: str, boolean_exp_types: List[Dict[str, Any]]) -> str:
    # Split the content into documents while preserving original separators
    documents = []
    separators = []
    current_doc = ""
    for line in content.splitlines(True):  # Keep the newlines
        if line.strip() == "---":
            if current_doc:
                documents.append(yaml.load(current_doc))
                separators.append(line)
                current_doc = ""
        else:
            current_doc += line
    if current_doc:
        documents.append(yaml.load(current_doc))

    # Process the documents
    processed_documents = []
    for doc in documents:
        if doc.get('kind') == 'ObjectBooleanExpressionType':
            continue  # Skip this document
        elif doc.get('kind') == 'Model':
            update_model_filter_expression_type(doc, boolean_exp_types)
        processed_documents.append(doc)

    # Reconstruct the content with original separators
    output = io.StringIO()
    output.write('---\n')  # Add starting separator
    for i, doc in enumerate(processed_documents):
        if i > 0:
            output.write(separators[i-1])
        yaml.dump(doc, output)

    return output.getvalue()

def update_model_filter_expression_type(model: Dict[str, Any], boolean_exp_types: Dict[str, Any]):
    model_type = model.get('definition', {}).get('objectType')
    if model_type:
        for bet in boolean_exp_types:
            if bet['definition']['operand'].get('object', {}).get('type') == model_type:
                model['definition']['filterExpressionType'] = bet['definition']['name']
                break

def extract_types(parsed_files: Dict[str, List[Dict[str, Any]]]) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], str]:
    object_types = {}
    scalar_representations = {}
    data_connector_links = {}
    subgraph_name = None

    for filename, documents in parsed_files.items():
        for doc in documents:
            kind = doc.get('kind')
            if kind == 'ObjectType':
                try:
                    name = doc['definition']['name']
                    object_types[normalize_name(name)] = doc['definition']
                except KeyError as e:
                    logger.debug(f"Problematic document: {doc}")
            elif kind == 'Connector':
                subgraph_name = doc['definition'].get('subgraph')
            elif kind == 'DataConnectorScalarRepresentation':
                try:
                    definition = doc['definition']
                    data_connector_scalar_type = definition.get('dataConnectorScalarType')
                    representation = definition.get('representation')
                    if data_connector_scalar_type and representation:
                        scalar_representations[data_connector_scalar_type] = definition
                    else:
                        logger.debug(f"Problematic document: {doc}")
                except KeyError as e:
                    logger.debug(f"Problematic document: {doc}")
            elif kind == 'DataConnectorLink':
                try:
                    schema = doc['definition']['schema']['schema']
                    data_connector_links[filename] = schema
                    logger.debug(f"DataConnectorLink structure: {schema}")
                except KeyError as e:
                    logger.debug(f"Problematic document: {doc}")

    return object_types, scalar_representations, data_connector_links, subgraph_name

def find_matching_object_type(object_types, normalized_name): 
    for ot, ot_info in object_types.items():
        if normalize_name(ot) == normalized_name:
            return ot
        else:
            None

def match_object_types(object_types: Dict[str, Any], data_connector_links: Dict[str, Any]) -> Dict[str, Any]:
    matched_types = {}
    for dcl_filename, dcl_schema in data_connector_links.items():
        object_types_list = dcl_schema.get('object_types', [])
        
        for obj_type in object_types_list:
            if isinstance(obj_type, str):
                obj_type_name = obj_type
            elif isinstance(obj_type, dict) and 'name' in obj_type:
                obj_type_name = obj_type['name']
            else:
                logger.warning(f"Unexpected object type format in {dcl_filename}: {obj_type}")
                continue
            
            normalized_name = normalize_name(obj_type_name)
            matching_object_type = find_matching_object_type(object_types, normalized_name)
            
            if matching_object_type:
                if normalized_name not in matched_types:
                    matched_types[normalized_name] = {
                        'object_type': object_types[matching_object_type],
                        'dcl_type': obj_type,
                        'dcl_filename': dcl_filename
                    }
            else:
                logger.warning(f"No matching ObjectType found for: {obj_type_name}")
    
    return matched_types

def generate_scalar_boolean_expression_type(scalar_name: str, scalar_info: Dict[str, Any], dcl_scalar_type: Dict[str, Any], subgraph_name: str) -> Dict[str, Any]:
    comparison_operators = [
        {'name': op, 'argumentType': f"{sanitize_name(scalar_info['representation'])}!"}
        for op in dcl_scalar_type.get('comparison_operators', [])
    ]
    
    sanitized_scalar_name = sanitize_name(scalar_name)
    
    return {
        'kind': 'BooleanExpressionType',
        'version': 'v1',
        'definition': {
            'name': f"{sanitized_scalar_name}BoolExp",
            'operand': {
                'scalar': {
                    'type': sanitize_name(scalar_info['representation']),
                    'comparisonOperators': comparison_operators,
                    'dataConnectorOperatorMapping': [
                        {
                            'dataConnectorName': scalar_info.get('dataConnectorName', 'unknown'),
                            'dataConnectorScalarType': sanitized_scalar_name,
                            'operatorMapping': {}
                        }
                    ]
                }
            },
            'logicalOperators': {'enable': True},
            'isNull': {'enable': True},
            'graphql': {'typeName': f"{cap(subgraph_name)}_{sanitized_scalar_name}BoolExp"}
        }
    }

def generate_object_boolean_expression_type(object_name: str, object_info: Dict[str, Any], scalar_bool_exps: Dict[str, Any], object_bool_exps: Dict[str, Any], all_object_types: Dict[str, Any], subgraph_name: str) -> Dict[str, Any]:
    comparable_fields = []
    capitalized_name = sanitize_name(object_info['object_type'].get('name', capitalize_object_type_name(object_name)))

    for field in object_info['object_type'].get('fields', []):
        field_name = field['name']
        field_type = field['type']
        capitalized_field_type = sanitize_name(capitalize_object_type_name(field_type))
        lowercased_string = field_type.lower()
        cleaned_field_type = re.sub(r'[^a-z0-9]', '', lowercased_string)

        # Skip the iteration if field_type is an array type (nested array filtering is not supported)
        if field_type.startswith('[') and field_type.endswith(']'):
            continue

        # Check if the field type is a scalar type with a boolean expression
        if cleaned_field_type in scalar_bool_exps:
            comparable_fields.append({
                'fieldName': field_name,
                'booleanExpressionType': f"{capitalized_field_type.lower()}BoolExp"
            })
        # Check if the field type is another ObjectType
        elif capitalized_field_type in object_bool_exps or f"{capitalized_field_type}BoolExp" in object_bool_exps:
            comparable_fields.append({
                'fieldName': field_name,
                'booleanExpressionType': f"{capitalized_field_type}BoolExp"
            })
        # Check if the field type exists in all_object_types
        elif normalize_name(field_type) in all_object_types:
            comparable_fields.append({
                'fieldName': field_name,
                'booleanExpressionType': f"{capitalized_field_type}BoolExp"
            })

    return {
        'kind': 'BooleanExpressionType',
        'version': 'v1',
        'definition': {
            'name': f"{capitalized_name}BoolExp",
            'operand': {
                'object': {
                    'type': capitalized_name,
                    'comparableFields': comparable_fields,
                    'comparableRelationships': []
                }
            },
            'logicalOperators': {'enable': True},
            'isNull': {'enable': True},
            'graphql': {'typeName': f"{cap(subgraph_name)}_{capitalized_name}BoolExp"}
        }
    }

def generate_boolean_expression_types(matched_object_types: Dict[str, Any], scalar_representations: Dict[str, Any], data_connector_links: Dict[str, Any], subgraph_name: str) -> List[Dict[str, Any]]:
    boolean_exp_types = []
    scalar_bool_exps = {}
    object_bool_exps = {}

    # Generate BooleanExpressionTypes for scalars
    for scalar_name, scalar_info in scalar_representations.items():
        for dcl_filename, dcl_schema in data_connector_links.items():
            for dcl_scalar_type in dcl_schema.get('scalar_types', []):
                if isinstance(dcl_scalar_type, dict) and dcl_scalar_type.get('name') == scalar_info['dataConnectorScalarType']:
                    dcl_scalar_type_info = dcl_schema.get('scalar_types').get(scalar_info['dataConnectorScalarType'])
                    new_type = generate_scalar_boolean_expression_type(scalar_name, scalar_info, dcl_scalar_type_info, subgraph_name)
                    boolean_exp_types.append(new_type)
                    scalar_bool_exps[scalar_name] = new_type
                    break
                elif isinstance(dcl_scalar_type, str) and dcl_scalar_type == scalar_info['dataConnectorScalarType']:
                    dcl_scalar_type_info = dcl_schema.get('scalar_types').get(scalar_info['dataConnectorScalarType'])
                    new_type = generate_scalar_boolean_expression_type(scalar_name, scalar_info, dcl_scalar_type_info, subgraph_name)
                    boolean_exp_types.append(new_type)
                    scalar_bool_exps[scalar_name] = new_type
                    break

    # First pass: Generate basic BooleanExpressionTypes for objects
    for object_name, object_info in matched_object_types.items():
        new_type = generate_object_boolean_expression_type(object_name, object_info, scalar_bool_exps, object_bool_exps, matched_object_types, subgraph_name)
        boolean_exp_types.append(new_type)
        object_bool_exps[capitalize_object_type_name(object_name)] = new_type

    # Second pass: Update ObjectType BooleanExpressionTypes with complete comparableFields
    for object_name, object_info in matched_object_types.items():
        updated_type = generate_object_boolean_expression_type(object_name, object_info, scalar_bool_exps, object_bool_exps, matched_object_types, subgraph_name)
        # Replace the old version with the updated one
        for i, bet in enumerate(boolean_exp_types):
            if bet['definition']['name'] == updated_type['definition']['name']:
                boolean_exp_types[i] = updated_type
                break

    return boolean_exp_types

def write_new_hml_file(new_boolean_expression_types: List[Dict[str, Any]], output_file: str):
    with open(output_file, 'w') as file:
        file.write('---\n')  # Add starting separator
        for i, bet in enumerate(new_boolean_expression_types):
            yaml.dump(bet, file)
            if i < len(new_boolean_expression_types) - 1:  # Don't add extra newline after the last object
                file.write('\n---\n')  # Add document separator

def main():
    parser = argparse.ArgumentParser(description="Process HML files and generate BooleanExpressionTypes.")
    parser.add_argument("--project-path", required=True, help="Path to the project directory containing HML files")
    parser.add_argument("--output-file", required=True, help="Path to the output file for new BooleanExpressionTypes")
    args = parser.parse_args()

    logger.info(f"Starting HML processing for project path: {args.project_path}")

    try:
        hml_files = read_all_hml_files(args.project_path)
        logger.info(f"Found {len(hml_files)} HML files (excluding node_modules)")

        parsed_files = {}
        for filename, content in hml_files.items():
            try:
                parsed_files[filename] = parse_hml_content(content, filename)
            except ValueError as e:
                logger.error(str(e))
                return

        logger.info(f"Parsed {sum(len(docs) for docs in parsed_files.values())} documents from HML files")
        
        object_types, scalar_representations, data_connector_links, subgraph_name = extract_types(parsed_files)
        matched_object_types = match_object_types(object_types, data_connector_links)
        logger.info(f"Matched {len(matched_object_types)} ObjectTypes with DataConnectorLinks")
        
        new_boolean_expression_types = generate_boolean_expression_types(matched_object_types, scalar_representations, data_connector_links, subgraph_name)
        
        logger.info(f"Total HML files processed: {len(hml_files)}")
        logger.info(f"Total ObjectTypes: {len(object_types)}")
        logger.info(f"Total DataConnectorScalarRepresentations: {len(scalar_representations)}")
        logger.info(f"Total BooleanExpressionTypes generated: {len(new_boolean_expression_types)}")

        # Process each HML file
        just_hml_files = {k: v for k, v in hml_files.items() if k.endswith('.hml')}
        for filename, content in just_hml_files.items():
            try:
                processed_content = process_hml_file(content, new_boolean_expression_types)
                with open(filename, 'w') as file:
                    file.write(processed_content)
                logger.info(f"Processed and updated: {filename}")
            except Exception as e:
                logger.error(f"Error processing file {filename}: {str(e)}")

        write_new_hml_file(new_boolean_expression_types, args.output_file)
        logger.info(f"New BooleanExpressionTypes written to {args.output_file}")

    except Exception as e:
        log_error_with_line_number(f"An error occurred: {str(e)}")
        import traceback
        logger.debug(f"Stack trace: {traceback.format_exc()}")

if __name__ == "__main__":
    main()
