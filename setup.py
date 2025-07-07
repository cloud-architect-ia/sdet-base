# setup.py

from setuptools import setup, find_packages

setup(
    name="sdet_base", 
    version="0.1.0",
    description="CLI Python para la prueba técnica SDET usando AWS",
    author="junior.millan",
    license="MIT",

    package_dir={"": "src"},
    packages=find_packages(where="src"),

    install_requires=[
        "click",
        "boto3",
        "python-dotenv",
    ],

    extras_require={
        "dev": [
            "pytest",
            "moto",
            "black",
            "isort",
            "flake8",
            "mypy",
        ],
    },

    entry_points={
        "console_scripts": [
            # "sdet_base = sdet_base.cli:main",
        ],
    },

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],

    python_requires=">=3.8",  
)
