# list_ai_tools

[![Github Actions Status](https://github.com/github_username/list_ai_tools/workflows/Build/badge.svg)](https://github.com/github_username/list_ai_tools/actions/workflows/build.yml)

A Jupyter Server extension.

## Requirements

- Jupyter Server

## Install

To install the extension, execute:

```bash
pip install list_ai_tools
```

## Uninstall

To remove the extension, execute:

```bash
pip uninstall list_ai_tools
```

## Troubleshoot

If you are seeing the frontend extension, but it is not working, check
that the server extension is enabled:

```bash
jupyter server extension list
```

## Contributing

### Development install

```bash
# Clone the repo to your local environment
# Change directory to the list_ai_tools directory
# Install package in development mode - will automatically enable
# The server extension.
pip install -e .
```


You can watch the source directory and run your Jupyter Server-based application at the same time in different terminals to watch for changes in the extension's source and automatically rebuild the extension.  For example,
when running JupyterLab:

```bash
jupyter lab --autoreload
```

If your extension does not depend a particular frontend, you can run the
server directly:

```bash
jupyter server --autoreload
```

### Running Tests

Install dependencies:

```bash
pip install -e ".[test]"
```

To run the python tests, use:

```bash
pytest

# To test a specific file
pytest list_ai_tools/tests/test_handlers.py

# To run a specific test
pytest list_ai_tools/tests/test_handlers.py -k "test_get"
```

### Development uninstall

```bash
pip uninstall list_ai_tools
```

### Packaging the extension

See [RELEASE](RELEASE.md)
