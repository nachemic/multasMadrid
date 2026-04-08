from setuptools import setup, find_packages

setup(
    name="madridFines",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "pandas",
        "matplotlib",
        "numpy"
    ],
)