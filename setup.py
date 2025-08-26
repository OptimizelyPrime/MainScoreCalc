from setuptools import setup, find_packages

setup(
    name="maintainability-score-analyzer",
    version="0.1",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "libclang",
        "javalang",
    ],
    include_package_data=True,
    package_data={
        "maintainability_score_analyzer": ["copilot_instructions.txt"],
    },
    # CLI functionality removed
)
