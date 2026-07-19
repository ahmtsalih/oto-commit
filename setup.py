from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="oto-commit",
    version="0.1.2", 
    author="Ahmet Salih",
    description="Yapay Zeka Destekli Git Commit Asistanı",
    long_description=long_description,  
    long_description_content_type="text/markdown", 
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "typer[all]",
        "rich"
    ],
    entry_points={
        "console_scripts": [
            "oto-commit=oto_commit.cli:main", 
        ],
    },
)