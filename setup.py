from setuptools import setup, find_packages

setup(
    name="list_ai_tools",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,  # include files in MANIFEST.in or found by setuptools
    install_requires=[
        "jupyter-server>=2.0.0",
        "jsonschema",
    ],
    data_files=[
        (
            "etc/jupyter/jupyter_server_config.d",
            ["jupyter-config/jupyter_server_config.d/list_ai_tools.json"],
        )
    ],
    entry_points={},
    zip_safe=False,
)
