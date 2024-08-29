# Aggregate Expression Generator

This Python script processes HML (Hasura Metadata Language) files and generates aggregate expressions for data models. It's designed to automate the creation and updating of various HML components, including scalar types, data connector representations, and aggregate expressions.

## Features

- Parses and processes Data Connector Link files
- Extracts scalar types and their aggregate functions
- Generates missing scalar type definitions
- Creates aggregate expressions for scalar types
- Updates model files with aggregate expressions
- Generates model-specific aggregate expressions
- Updates GraphQL configuration files

## Known issues

- Does not handle multiple connectors well

## Prerequisites

- Python 3.6+
- `ruamel.yaml` library

## Installation

1. Clone this repository or download the script.
2. Install the required library:

```bash
pip install ruamel.yaml
```

## Usage

Run the script from the command line with the following arguments:

```bash
poetry run aggregate-expression-types --data-connector-link <path_to_connector_file> \
               --data-connector-link-types <path_to_types_file> \
               --models <comma_separated_model_files> \
               --output-file <path_to_output_file> \
               --graphql-config <path_to_graphql_config_file>
```

### Arguments

- `--data-connector-link`: Path to the data connector link file (e.g., mong.hml)
- `--data-connector-link-types`: Path to the data connector link types file (e.g., mong-types.hml)
- `--models`: Comma-separated list of model files to process
- `--output-file`: Path to the output file for aggregate expressions
- `--graphql-config`: Path to the GraphQL config file

## What the Script Does

1. Parses the data connector link file to extract scalar types and their aggregate functions.
2. Analyzes the data connector link types file to identify existing scalar representations and missing scalar types.
3. Generates new scalar type definitions for any missing types.
4. Updates the data connector link types file with the new definitions.
5. Creates aggregate expressions for each scalar type and writes them to the output file.
6. Updates the GraphQL config file with aggregate-related configurations if needed.
7. Processes each model file to generate model-specific aggregate expressions and updates the model definitions.
8. Appends the model-specific aggregate expressions to the output file.

## Generating a Standalone Executable

To create a standalone executable of the HML File Processor and Aggregate Expression Generator, you can use the provided `package_script.py`. This script uses PyInstaller to package the application into a single executable file.

Follow these steps to generate the binary:

1. Ensure you have PyInstaller installed. If not, install it using Poetry:
   ```
   poetry add --dev pyinstaller
   ```

2. Run the packaging script:
   ```
   poetry run python package_script.py
   ```

3. Once the script completes, you'll find the generated executable in the `dist` directory. The file will be named `aggregate-generator` (or `aggregate-generator.exe` on Windows).

4. You can now run the executable directly without needing Python or any dependencies installed:
   ```
   ./dist/aggregate-generator --data-connector-link <path_to_connector_file> \
                              --data-connector-link-types <path_to_types_file> \
                              --models <comma_separated_model_files> \
                              --output-file <path_to_output_file> \
                              --graphql-config <path_to_graphql_config_file>
   ```

Note: The generated executable is platform-specific. If you need to distribute the application for different operating systems, you'll need to run the packaging script on each target platform.

## Output

The script generates or updates several files:

1. Updated data connector link types file with new scalar type definitions.
2. An output file containing aggregate expressions for scalar types and models.
3. Updated model files with new aggregate expression references and GraphQL configurations.
4. Updated GraphQL config file with aggregate-related settings.

## Logging

The script provides detailed logging information about its operations, including:

- Scalar types processed
- Aggregate functions added
- New definitions created
- File updates made

## Notes

- Ensure that you have write permissions for all the files you're updating.
- Back up your files before running the script, especially when processing production data.
- The script uses the `ruamel.yaml` library to preserve the format and comments in YAML files as much as possible.

## Contributing

Contributions to improve the script or extend its functionality are welcome. Please submit pull requests or open issues on the project's repository.
