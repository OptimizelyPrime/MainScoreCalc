from setuptools import setup, find_packages

setup(
    name="maintainability-analyzer",
    version="0.1",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "libclang",
        "javalang",
        "tree-sitter>=0.23",
        "tree-sitter-c-sharp>=0.23",
    ],
    include_package_data=True,
    package_data={
        "maintainability_analyzer": ["copilot_instructions.txt"],
    },
    # CLI functionality removed
)
