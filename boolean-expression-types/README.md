# Boolean Expression Generator

This Python script processes HML (Hasura Metadata Language) files to generate BooleanExpressionTypes for a Hasura project. It analyzes ObjectTypes, ScalarRepresentations, and DataConnectorLinks to create appropriate Boolean expression types for filtering in GraphQL queries.

## Features

- Reads and parses HML files from a specified project directory
- Extracts ObjectTypes, ScalarRepresentations, and DataConnectorLinks
- Generates BooleanExpressionTypes for both scalar and object types
- Updates existing HML files with new filterExpressionType fields
- Creates a new HML file containing all generated BooleanExpressionTypes

## Prerequisites

- Python 3.8 or higher
- Poetry (for dependency management)
- PyInstaller (for creating a standalone executable)

## Installation

1. Clone this repository
2. Navigate to the project directory
3. Install dependencies using Poetry:

```
poetry install
```

## Usage

Run the script using the following command:

```
poetry run boolean-expression-types --project-path /path/to/your/project --output-file /path/to/output/boolean_expression_types.hml
```

Arguments:
- `--project-path`: Path to the directory containing your Hasura project's HML files
- `--output-file`: Path where the new HML file containing BooleanExpressionTypes will be saved

## How it works

1. The script walks through the specified project directory and reads all HML files (excluding those in `node_modules`).
2. It parses the HML content, extracting ObjectTypes, ScalarRepresentations, and DataConnectorLinks.
3. The script matches ObjectTypes with their corresponding DataConnectorLinks.
4. It generates BooleanExpressionTypes for both scalar and object types based on the extracted information.
5. Existing HML files are updated with new `filterExpressionType` fields where applicable.
6. A new HML file is created containing all the generated BooleanExpressionTypes.

## Generating a Standalone Executable

To create a standalone executable of the Boolean Expression Types Generator, you can use the provided `package_script.py`. This script uses PyInstaller to package the application into a single executable file.

Follow these steps to generate the binary:

1. Ensure you have PyInstaller installed. If not, install it using Poetry:

```
poetry add --dev pyinstaller
```

2. Run the packaging script:

```
poetry run python package_script.py
```

3. Once the script completes, you'll find the generated executable in the `dist` directory. The file will be named `boolean-generator` (or `boolean-generator.exe` on Windows).

4. You can now run the executable directly without needing Python or any dependencies installed:

```
./dist/boolean-generator --project-path /path/to/your/project --output-file /path/to/output/boolean_expression_types.hml
```

Note: The generated executable is platform-specific. If you need to distribute the application for different operating systems, you'll need to run the packaging script on each target platform.

## Logging

The script provides detailed logging information, including:
- Number of HML files processed
- Number of ObjectTypes, ScalarRepresentations, and generated BooleanExpressionTypes
- Any errors or warnings encountered during processing

## Error Handling

The script includes error handling to catch and report issues such as:
- Problems reading or parsing HML files
- Mismatches between ObjectTypes and DataConnectorLinks
- Unexpected data structures in the HML files

If an error occurs, check the console output for detailed information about the nature and location of the error.

## Contributing

Contributions to improve the script are welcome. Please submit a pull request or open an issue to discuss proposed changes.
