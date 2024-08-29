# HML File Processors and Generators

This project contains two Python scripts designed to process and generate HML (Hasura Metadata Language) files for Hasura projects. These tools automate the creation and updating of various HML components, enhancing your Hasura GraphQL API capabilities.

## Tools Included

1. **Aggregate Expression Generator**
2. **Boolean Expression Types Generator**

## Features

### Aggregate Expression Generator
- Processes Data Connector Link files
- Extracts and generates scalar types and their aggregate functions
- Creates and updates aggregate expressions for data models
- Updates GraphQL configuration files

### Boolean Expression Types Generator
- Generates BooleanExpressionTypes for filtering in GraphQL queries
- Analyzes ObjectTypes, ScalarRepresentations, and DataConnectorLinks
- Updates existing HML files with new filterExpressionType fields

## Prerequisites

- Python 3.8+
- Poetry (for dependency management)
- ruamel.yaml library

## Installation

1. Clone this repository
2. Navigate to the project directory
3. Install dependencies using Poetry:

```bash
poetry install
```

## Usage

### Aggregate Expression Generator

```bash
poetry run aggregate-expression-types --data-connector-link <path_to_connector_file> \
               --data-connector-link-types <path_to_types_file> \
               --models <comma_separated_model_files> \
               --output-file <path_to_output_file> \
               --graphql-config <path_to_graphql_config_file>
```

### Boolean Expression Types Generator

```bash
poetry run boolean-expression-types --project-path /path/to/your/project --output-file /path/to/output/boolean_expression_types.hml
```

## Generating Standalone Executables

Both tools can be packaged into standalone executables using PyInstaller. Use the provided `package_script.py` for each tool to create platform-specific binaries.

```bash
poetry run python package_script.py
```

The generated executables will be found in the `dist` directory.

## Output

Both scripts generate or update several HML files, including:
- Updated data connector link types
- New aggregate expressions and Boolean expression types
- Modified model files and GraphQL configurations

## Logging and Error Handling

Both scripts provide detailed logging information about their operations and include error handling to catch and report issues during processing.

## Known Issues

- The Aggregate Expression Generator does not handle multiple connectors well

## Contributing

Contributions to improve either script or extend their functionality are welcome. Please submit pull requests or open issues on the project's repository.

## Notes

- Ensure you have write permissions for all files you're updating
- Back up your files before running the scripts, especially when processing production data
- The scripts use the `ruamel.yaml` library to preserve the format and comments in YAML files as much as possible
