import io
import logging
import argparse
from typing import List, Dict, Any, Tuple
from ruamel.yaml import YAML
import re

yaml = YAML()
yaml.default_flow_style = False
yaml.preserve_quotes = True
yaml.indent(mapping=2, sequence=4, offset=2)
yaml.preserve_null = True
yaml.width = 4096
yaml.representer.add_representer(type(None), lambda self, data: self.represent_scalar('tag:yaml.org,2002:null', 'null'))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_hml_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse an HML file and return its contents as a list of YAML documents.
    """
    with open(file_path, 'r') as file:
        content = file.read()

    yaml_docs = content.split('---')
    parsed_docs = []

    for doc in yaml_docs:
        if doc.strip():
            parsed_doc = yaml.load(doc)
            if parsed_doc:
                parsed_docs.append(parsed_doc)

    return parsed_docs

def extract_scalar_types(connector_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Extract scalar types and their aggregate functions from connector data.
    """
    scalar_types = {}

    schema_data = connector_data.get('definition', {}).get('schema', {}).get('schema', {})
    scalar_types_data = schema_data.get('scalar_types', {})

    for scalar_type, type_data in scalar_types_data.items():
        aggregate_functions = type_data.get('aggregate_functions', {})

        scalar_types[scalar_type] = {
            'aggregate_functions': aggregate_functions
        }

    return scalar_types

def extract_scalar_representations(types_data: List[Dict[str, Any]], scalar_types: Dict[str, Dict[str, Any]]) -> Tuple[Dict[str, str], List[str]]:
    """
    Extract scalar representations from the types data and identify missing scalar types.
    """
    scalar_representations = {}
    existing_scalar_types = set()

    for doc in types_data:
        if doc.get('kind') == 'ScalarType':
            existing_scalar_types.add(doc.get('definition', {}).get('name'))
        elif doc.get('kind') == 'DataConnectorScalarRepresentation':
            scalar_type = doc.get('definition', {}).get('dataConnectorScalarType')
            representation = doc.get('definition', {}).get('representation')
            if scalar_type and representation:
                scalar_representations[scalar_type] = representation
                existing_scalar_types.add(representation)

    missing_scalar_types = [
        scalar_type for scalar_type in scalar_types.keys()
        if scalar_type not in existing_scalar_types and scalar_type not in scalar_representations
    ]

    return scalar_representations, missing_scalar_types

def get_return_type(func: str, scalar_type: str, func_data: Dict[str, Any], scalar_representations: Dict[str, str]) -> str:
    """
    Determine the correct return type for an aggregate function.
    """
    result_type = func_data['result_type'] or {}
    name = result_type['underlying_type']['name'] or ''

    if name in scalar_representations:
        return scalar_representations[name]
    else:
        ''

def generate_scalar_type_definitions(missing_scalar_types: List[str], connector_name: str) -> List[Dict[str, Any]]:
    """
    Generate ScalarType and DataConnectorScalarRepresentation definitions for missing scalar types.
    """
    new_definitions = []
    for scalar_type in missing_scalar_types:
        # Generate ScalarType definition
        scalar_type_def = {
            "kind": "ScalarType",
            "version": "v1",
            "definition": {
                "name": scalar_type.title(),
                "graphql": {
                    "typeName": f"{scalar_type.title()}"
                }
            }
        }
        new_definitions.append(scalar_type_def)

        # Generate DataConnectorScalarRepresentation definition
        representation_def = {
            "kind": "DataConnectorScalarRepresentation",
            "version": "v1",
            "definition": {
                "dataConnectorName": connector_name,
                "dataConnectorScalarType": scalar_type,
                "representation": scalar_type.title(),
                "graphql": {
                    "comparisonExpressionTypeName": f"{scalar_type.title()}ComparisonExp"
                }
            }
        }
        new_definitions.append(representation_def)

    return new_definitions

def generate_aggregate_expression(scalar_type: str, aggregate_functions: Dict[str, Any], connector_name: str, scalar_representations: Dict[str, str]) -> Dict[str, Any]:
    """
    Generate an AggregateExpression for a given scalar type.
    """
    # Use the representation from scalar_representations if available, otherwise use the original scalar_type
    aggregated_type = scalar_representations.get(scalar_type, scalar_type)
    aggregation_functions = []
    function_mappings = {}
    for func, func_data in aggregate_functions.items():
        if func != 'count':
            return_type = get_return_type(func, aggregated_type, func_data, scalar_representations)
            if return_type != '' and return_type != None:
                aggregation_functions.append({"name": func, "returnType": return_type})
                function_mappings.update({func: {"name": func}})

    expression = {
        "kind": "AggregateExpression",
        "version": "v1",
        "definition": {
            "name": f"{aggregated_type}_aggregate_exp",
            "operand": {
                "scalar": {
                    "aggregatedType": aggregated_type,
                    "aggregationFunctions": aggregation_functions,
                    "dataConnectorAggregationFunctionMapping": [
                        {
                            "dataConnectorName": connector_name,
                            "dataConnectorScalarType": scalar_type,
                            "functionMapping": function_mappings,
                        }
                    ]
                }
            },
            "graphql": {
                "selectTypeName": f"{aggregated_type}_aggregate_fields",
                "orderByInputTypeName": f"{aggregated_type}_aggregate_order_by",
                "aggregatePredicateInputTypeName": f"{aggregated_type}_array_aggregate_predicate_exp",
                "aggregateBoolExpInputTypeName": f"{aggregated_type}_aggregate_bool_exp",
                "aggregateSelectInputTypeName": f"{aggregated_type}_aggregate_select"
            }
        }
    }

    if 'count' in aggregate_functions:
        expression["definition"]["count"] = {"enable": True}
        expression["definition"]["countDistinct"] = {"enable": True}

    return expression

def write_aggregate_expressions(scalar_types: Dict[str, Dict[str, Any]], scalar_representations: Dict[str, str], connector_name: str, output_file: str) -> None:
    """
    Write AggregateExpressions to the output file.
    """
    valid_scalar_types = [
        scalar_type for scalar_type, data in scalar_types.items()
        if scalar_type in scalar_representations and data['aggregate_functions']
    ]

    with open(output_file, 'w') as f:
        f.write('---\n')
        for index, scalar_type in enumerate(valid_scalar_types, start=1):
            data = scalar_types[scalar_type]
            expression = generate_aggregate_expression(
                scalar_type, 
                data['aggregate_functions'],
                connector_name,
                scalar_representations
            )
            yaml.dump(expression, f)

            # Add separator only if it's not the last item
            if index < len(valid_scalar_types):
                f.write('\n---\n')

            # Log the scalar type and its aggregate functions
            logging.info(f"[{index}] Added aggregate functions for scalar type: {scalar_type}")
            logging.info(f"[{index}] Aggregate functions: {', '.join(data['aggregate_functions'].keys())}")

    # Log skipped scalar types
    for index, (scalar_type, data) in enumerate(scalar_types.items(), start=1):
        if scalar_type not in scalar_representations or not data['aggregate_functions']:
            logging.info(f"[{index}] Skipped scalar type: {scalar_type} (no representation or aggregate functions)")

def generate_model_aggregate_expression(model_name: str, object_type: Dict[str, Any], scalar_types: Dict[str, Dict[str, Any]], scalar_representations: Dict[str, str]) -> Dict[str, Any]:
    """
    Generate an AggregateExpression for a given Model.
    """
    aggregatable_fields = []
    for field in object_type['fields']:
        field_name = field['name']
        field_type = field['type'].replace('!', '')
        if isinstance(field_type, dict):
            field_type = field_type.get('type', '')
        if next(
            (
                key for key in scalar_types
                if key.lower() == field_type.lower() and scalar_types.get(key, {}).get('aggregate_functions')
            ), None
        ):
            aggregatable_fields.append({
                "fieldName": field_name,
                "aggregateExpression": f"{field_type}_aggregate_exp"
            })

    expression = {
        "kind": "AggregateExpression",
        "version": "v1",
        "definition": {
            "name": f"{model_name}_aggregate_exp",
            "operand": {
                "object": {
                    "aggregatedType": model_name,
                    "aggregatableFields": aggregatable_fields
                }
            },
            "graphql": {
                "selectTypeName": f"{model_name}_aggregate_fields"
            },
            "description": f"Aggregate over {model_name}"
        }
    }
    return expression

def update_data_connector_link_types(file_path: str, new_definitions: List[Dict[str, Any]]) -> None:
    """
    Update the data connector link types file with new scalar type definitions.
    """
    existing_docs = parse_hml_file(file_path)

    with open(file_path, 'w') as f:
        f.write('---\n')
        for i, doc in enumerate(existing_docs + new_definitions):
            if i > 0:
                f.write('\n---\n')
            yaml.dump(doc, f)

    logging.info(f"Updated data connector link types file: {file_path}")
    for def_type in set(d['kind'] for d in new_definitions):
        count = sum(1 for d in new_definitions if d['kind'] == def_type)
        logging.info(f"Added {count} new {def_type} definitions")

def update_graphql_config(file_path: str):
    """
    Update the GraphQL config file by adding the aggregate section if it doesn't exist.
    """
    documents = parse_hml_file(file_path)
    updated = False

    for doc in documents:
        if doc.get('kind') == 'GraphqlConfig':
            definition = doc.get('definition', {})
            query = definition.get('query', {})

            if 'aggregate' not in query:
                query['aggregate'] = {
                    "filterInputFieldName": "filter_input",
                    "countFieldName": "_count",
                    "countDistinctFieldName": "_count_distinct"
                }
                updated = True

            definition['query'] = query
            doc['definition'] = definition

    if updated:
        with open(file_path, 'w') as f:
            yaml.dump_all(documents, f)
        logging.info(f"Updated GraphQL config file: {file_path}")
    else:
        logging.info(f"No updates needed for GraphQL config file: {file_path}")

def process_model_files(model_files: List[str], scalar_types: Dict[str, Dict[str, Any]], scalar_representations: Dict[str, str], output_file: str) -> None:
    """
    Process model files, generate AggregateExpressions for each Model, and update Model definitions.
    """
    model_aggregate_expressions = []

    for model_file in model_files:
        with open(model_file, 'r') as f:
            content = f.read()

        documents = list(yaml.load_all(content))

        updated_documents = []
        model_updated = False
        object_types = {doc['definition']['name']: doc['definition'] for doc in documents if doc.get('kind') == 'ObjectType'}

        for doc in documents:
            if doc.get('kind') == 'Model':
                model_name = doc['definition']['name']
                object_type = object_types.get(model_name)

                if object_type:
                    # Generate AggregateExpression
                    aggregate_expression = generate_model_aggregate_expression(model_name, object_type, scalar_types, scalar_representations)
                    model_aggregate_expressions.append(aggregate_expression)

                    # Update Model definition only if new attributes don't exist
                    if 'aggregateExpression' not in doc['definition']:
                        doc['definition']['aggregateExpression'] = f"{model_name}_aggregate_exp"
                        model_updated = True

                    if 'graphql' not in doc['definition']:
                        doc['definition']['graphql'] = {}

                    graphql = doc['definition']['graphql']
                    if 'filterInputTypeName' not in graphql:
                        graphql['filterInputTypeName'] = f"{model_name}_filter_input"
                        model_updated = True

                    if 'aggregate' not in graphql:
                        graphql['aggregate'] = {
                            "queryRootField": f"{model_name.lower()}_aggregate"
                        }
                        model_updated = True
                else:
                    logging.warning(f"No matching ObjectType found for Model: {model_name}")

            updated_documents.append(doc)

        # Write updated documents back to file
        with open(model_file, 'w') as f:
            f.write('---\n')
            for i, doc in enumerate(updated_documents):
                if i > 0:
                    f.write('\n---\n')
                yaml.dump(doc, f)

        if model_updated:
            logging.info(f"Updated Model definition and generated AggregateExpression for model: {model_name}")
        else:
            logging.info(f"No updates needed for model: {model_name}")

    # Append model aggregate expressions to the output file
    with open(output_file, 'a') as f:
        for expression in model_aggregate_expressions:
            f.write('\n---\n')
            yaml.dump(expression, f)

def main():
    parser = argparse.ArgumentParser(description="Process HML files and generate aggregate expressions.")
    parser.add_argument('--data-connector-link', required=True, help="Path to the data connector link file (e.g., mong.hml)")
    parser.add_argument('--data-connector-link-types', required=True, help="Path to the data connector link types file (e.g., mong-types.hml)")
    parser.add_argument('--models', required=True, help="Comma-separated list of model files")
    parser.add_argument('--output-file', required=True, help="Path to the output file for aggregate expressions")
    parser.add_argument('--graphql-config', required=True, help="Path to the GraphQL config file")

    args = parser.parse_args()

    print(f"Processing with data connector link: {args.data_connector_link}")
    print(f"Data connector link types: {args.data_connector_link_types}")
    print(f"Models: {args.models}")
    print(f"Output file: {args.output_file}")
    print(f"GraphQL config: {args.graphql_config}")

    # Parse the connector file
    connector_documents = parse_hml_file(args.data_connector_link)

    # Find the DataConnectorLink document
    data_connector_link = next((doc for doc in connector_documents if doc.get('kind') == 'DataConnectorLink'), None)

    if not data_connector_link:
        logging.error("No DataConnectorLink found in the connector file")
        return

    # Extract scalar types and their aggregate functions
    scalar_types = extract_scalar_types(data_connector_link)

    # Parse the types file and extract scalar representations
    types_documents = parse_hml_file(args.data_connector_link_types)
    scalar_representations, missing_scalar_types = extract_scalar_representations(types_documents, scalar_types)

    # Get the connector name
    connector_name = data_connector_link.get('definition', {}).get('name', 'unknown')

    logging.info(f"Processing connector: {connector_name}")

    # Generate new scalar type definitions
    new_scalar_definitions = generate_scalar_type_definitions(missing_scalar_types, connector_name)

    # Update the data connector link types file
    update_data_connector_link_types(args.data_connector_link_types, new_scalar_definitions)

     # Combine existing and new DataConnectorScalarRepresentation definitions
    all_scalar_representations = scalar_representations.copy()
    for definition in new_scalar_definitions:
        if definition['kind'] == 'DataConnectorScalarRepresentation':
            scalar_type = definition['definition']['dataConnectorScalarType']
            representation = definition['definition']['representation']
            all_scalar_representations[scalar_type] = representation

    # Write the aggregate expressions to the output file
    write_aggregate_expressions(scalar_types, all_scalar_representations, connector_name, args.output_file)

    # Update the GraphQL config file
    update_graphql_config(args.graphql_config)

    # Process model files and generate AggregateExpressions for each Model
    model_files = args.models.split(',')
    process_model_files(model_files, scalar_types, all_scalar_representations, args.output_file)

if __name__ == "__main__":
    main()
