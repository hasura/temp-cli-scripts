import PyInstaller.__main__
import os
import sys

# Get the path to the virtual environment created by Poetry
venv_path = os.popen('poetry env info --path').read().strip()

# Add the project root to Python path
sys.path.append(os.getcwd())

# Specify the path to the main script
main_script = 'boolean_expression_types/main.py'

if not os.path.exists(main_script):
    raise FileNotFoundError(f"Could not find the main Python script at {main_script}")

print(f"Using {main_script} as the main script.")

PyInstaller.__main__.run([
    main_script,
    '--onefile',
    '--name=boolean-generator',
    f'--paths={venv_path}/lib/python3.12/site-packages',
    '--add-data=boolean_expression_types:boolean_expression_types',
    '--hidden-import=ruamel.yaml',
    '--hidden-import=ruamel.yaml.constructor',
    '--hidden-import=ruamel.yaml.representer',
    '--hidden-import=ruamel.yaml.resolver',
])
