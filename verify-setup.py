#!/usr/bin/env python3
"""
CloudCost Guardian - Setup Verification Script

Run this script to verify your environment is configured correctly.
"""

import sys
import os
from pathlib import Path


def check_python_version():
    """Check Python version."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        return True, f"✓ Python {version.major}.{version.minor}.{version.micro}"
    return False, f"✗ Python {version.major}.{version.minor}.{version.micro} (3.9+ required)"


def check_virtual_env():
    """Check if running in virtual environment."""
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    if in_venv:
        return True, f"✓ Virtual environment active: {sys.prefix}"
    return False, "✗ Not in virtual environment (run: source venv/bin/activate)"


def check_required_packages():
    """Check if required packages are installed."""
    required = ['boto3', 'pandas', 'numpy', 'pytest', 'black']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if not missing:
        return True, f"✓ All required packages installed"
    return False, f"✗ Missing packages: {', '.join(missing)}"


def check_file_structure():
    """Check if all required files exist."""
    root = Path(__file__).parent
    
    required_files = [
        '.gitignore',
        '.env.example',
        'requirements.txt',
        'setup.py',
        'README.md',
        'scripts/setup-env.sh',
        'scripts/deploy.sh',
        'scripts/seed-data.py',
    ]
    
    required_dirs = [
        'src/cost_analyzer',
        'src/forecaster',
        'src/recommender',
        'src/notifier',
        'src/dashboard',
        'tests',
        'terraform',
        'docs',
    ]
    
    missing_files = []
    missing_dirs = []
    
    for file in required_files:
        if not (root / file).exists():
            missing_files.append(file)
    
    for directory in required_dirs:
        if not (root / directory).is_dir():
            missing_dirs.append(directory)
    
    if not missing_files and not missing_dirs:
        return True, "✓ All required files and directories present"
    
    msg = []
    if missing_files:
        msg.append(f"Missing files: {', '.join(missing_files)}")
    if missing_dirs:
        msg.append(f"Missing directories: {', '.join(missing_dirs)}")
    
    return False, "✗ " + "; ".join(msg)


def check_lambda_functions():
    """Check if Lambda functions have required files."""
    root = Path(__file__).parent
    lambdas = ['cost_analyzer', 'forecaster', 'recommender', 'notifier']
    
    issues = []
    for lambda_name in lambdas:
        lambda_dir = root / 'src' / lambda_name
        
        if not (lambda_dir / 'lambda_function.py').exists():
            issues.append(f"{lambda_name}: missing lambda_function.py")
        
        if not (lambda_dir / 'requirements.txt').exists():
            issues.append(f"{lambda_name}: missing requirements.txt")
    
    if not issues:
        return True, "✓ All Lambda functions properly configured"
    
    return False, "✗ " + "; ".join(issues)


def check_env_file():
    """Check if .env file exists."""
    root = Path(__file__).parent
    
    if (root / '.env').exists():
        return True, "✓ .env file configured"
    return False, "⚠ .env file not found (copy from .env.example)"


def check_aws_credentials():
    """Check if AWS credentials are configured."""
    aws_config = Path.home() / '.aws' / 'credentials'
    
    if aws_config.exists():
        return True, "✓ AWS credentials configured"
    return False, "⚠ AWS credentials not found (run: aws configure)"


def main():
    """Run all checks."""
    print("=" * 60)
    print("CloudCost Guardian - Environment Verification")
    print("=" * 60)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Virtual Environment", check_virtual_env),
        ("Required Packages", check_required_packages),
        ("File Structure", check_file_structure),
        ("Lambda Functions", check_lambda_functions),
        ("Environment File", check_env_file),
        ("AWS Credentials", check_aws_credentials),
    ]
    
    results = []
    
    for name, check_func in checks:
        passed, message = check_func()
        results.append(passed)
        
        status = "✓" if passed else "✗"
        print(f"{name:.<40} {message}")
    
    print()
    print("=" * 60)
    
    if all(results[:5]):  # Critical checks
        print("✓ Setup is COMPLETE and ready to use!")
        print()
        print("Next steps:")
        print("  1. Configure .env file (if not done)")
        print("  2. Set up AWS credentials (if not done)")
        print("  3. Run: pytest tests/")
        print("  4. Start development!")
        return 0
    else:
        print("✗ Setup is INCOMPLETE - please fix the issues above")
        print()
        print("To fix:")
        print("  1. Run: ./scripts/setup-env.sh")
        print("  2. Activate venv: source venv/bin/activate")
        print("  3. Run this script again")
        return 1


if __name__ == '__main__':
    sys.exit(main())
