from setuptools import setup, find_packages

setup(
    name="dotenv-manager",
    version="1.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.1.7",
        "pyyaml>=6.0",
        "packaging>=23.0",
        "psutil>=5.9.0",
        "pydantic>=2.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0",
        "colorama>=0.4.6",
    ],
    entry_points={
        "console_scripts": [
            "dotenv=src.cli:main",
        ],
    },
)
