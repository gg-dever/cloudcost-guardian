"""
AWS CloudCost Guardian Package Configuration
"""

from setuptools import setup, find_packages

setup(
    name="cloudcost-guardian",
    version="0.1.0",
    description="AWS Cost Monitoring and Optimization Platform",
    author="Your Name",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "boto3>=1.28.0",
        "botocore>=1.31.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "scikit-learn>=1.3.0",
        "python-dateutil>=2.8.2",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.11.0",
            "moto>=4.2.0",
            "black>=23.7.0",
            "flake8>=6.1.0",
            "pylint>=2.17.0",
            "mypy>=1.5.0",
        ]
    },
)
