# Main Folder for testing files and 

## Quick Setup for Testing

### Installation of pytest and current status of openhivenpy

```bash
coverage run -m pytest
```

Installing inside the main dir of the project the current state of the module so it can be used for testing:
```bash
python -m pip install -e .
```

## Running with Coverage

### Install `coverage.py` for coverage testing

```bash
python3 -m pip install coverage
```

### Coverage Testing

Using coverage the standard unit-testing will be modified and watched to see what code-paths are not tested 
and might need to be included as well. It will return a regular report but create a new `.coverage` file

```bash
coverage run -m pytest -q --token=token
```

### Creating a coverage badge

Creating a coverage badge for the testing can be easily done using:

```bash
coverage-badge -o coverage.svg
```