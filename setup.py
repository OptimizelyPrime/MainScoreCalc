from setuptools import setup, find_packages

setup(
    name="maintainability-analyzer",
    version="0.1",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "libclang",
        "javalang",
    ],
    entry_points={
        "console_scripts": [
            "maintainability-analyzer=maintainability_analyzer.cli:main",
        ],
    },
)
