"""Setup configuration for the GradCafe analysis package."""

from setuptools import setup, find_packages

setup(
    name="gradcafe-analysis",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "flask",
        "psycopg",
        "python-dotenv",
        "beautifulsoup4",
    ],
)