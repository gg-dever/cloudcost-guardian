# Quick Reference - CloudCost Guardian

## 🚀 Quick Start Commands

```bash
# Setup (first time only)
./scripts/setup-env.sh

# Activate environment
source venv/bin/activate

# Deactivate environment
deactivate

# Install new package
pip install <package-name>
pip freeze > requirements.txt

# Run tests
pytest tests/
pytest tests/ --cov=src  # with coverage

# Format code
black src/ tests/ scripts/

# Deploy infrastructure
./scripts/deploy.sh

# Generate test data
python scripts/seed-data.py
```

## 📂 Key Files

| File | Purpose |
|------|---------|
| `.env` | Environment variables (create from `.env.example`) |
| `requirements.txt` | Python dependencies |
| `venv/` | Virtual environment (auto-generated) |
| `scripts/setup-env.sh` | Environment setup script |
| `scripts/deploy.sh` | Deployment automation |

## 🔧 Common Tasks

### Add New Python Package
```bash
source venv/bin/activate
pip install <package-name>
pip freeze > requirements.txt
```

### Add Lambda Dependency
```bash
# Edit specific Lambda requirements
nano src/cost_analyzer/requirements.txt
# Add package name and version
```

### Run Single Lambda Locally
```bash
cd src/cost_analyzer
python lambda_function.py
```

### Check Code Quality
```bash
flake8 src/
pylint src/
black --check src/
```

## 🐛 Troubleshooting

### Virtual Environment Not Found
```bash
# Recreate it
./scripts/setup-env.sh
```

### Module Not Found Error
```bash
# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt
```

### AWS Credentials Error
```bash
# Reconfigure AWS CLI
aws configure
# Or check .env file
```

### Permission Denied on Scripts
```bash
chmod +x scripts/*.sh
```

## 📋 Environment Variables (.env)

```bash
# Required
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012

# Optional
DAILY_COST_THRESHOLD=100
NOTIFICATION_EMAIL=you@example.com
```

## 🧪 Testing

```bash
# All tests
pytest

# Specific test
pytest tests/test_cost_analyzer.py

# With output
pytest -v

# With coverage
pytest --cov=src --cov-report=html
```

## 📦 Package Structure

```
src/
├── cost_analyzer/    # Fetches AWS costs
├── forecaster/       # ML predictions
├── recommender/      # Optimization tips
├── notifier/         # Alerts via SNS
└── dashboard/        # Web interface
```

## ⚠️ Important Notes

- **Never commit** `.env`, `*.csv`, or AWS credentials
- **Always activate** venv before development
- **Run tests** before committing changes
- **Format code** with black before commits
- **Update requirements.txt** after adding packages
