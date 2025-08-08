from setuptools import setup, find_packages

setup(
    name="maintainability-analyzer",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "libclang",
        "javalang",
    ],
)
