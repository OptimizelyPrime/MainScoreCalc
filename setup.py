from pathlib import Path
from setuptools import find_packages, setup

BASE_DIR = Path(__file__).parent
README_PATH = BASE_DIR / "README.md"
REQUIREMENTS_PATH = BASE_DIR / "requirements.txt"

long_description = README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else ""

def parse_requirements(path: Path):
    if not path.exists():
        return []

    requirements = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        requirements.append(line)
    return requirements

setup(
    name="maintainability-score-analyzer",
    version="0.1.0",
    description="Analyze source files to compute maintainability metrics such as the Maintainability Index.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=parse_requirements(REQUIREMENTS_PATH),
    python_requires=">=3.9",
    include_package_data=True,
    package_data={
        "maintainability_score_analyzer": ["copilot_instructions.txt"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords=[
        "maintainability",
        "metrics",
        "static analysis",
    ],
    url="https://example.com/maintainability-score-analyzer",
)
