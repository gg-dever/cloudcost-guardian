# Contributing to CloudCost Guardian

Thank you for your interest in contributing! This document outlines my development workflow and guidelines.

## 🌿 Branch Strategy

I follow a **Git Flow** branching model for organized development:

### Main Branches

- **`master`** (Production)
  - Always stable and deployable
  - Tagged with version numbers (v1.0.0, v1.1.0, etc.)
  - Only accepts merges from `develop` via pull requests
  - Protected branch - requires review before merge

- **`develop`** (Development) - **Default Branch**
  - Integration branch for features
  - Should be relatively stable
  - All feature branches merge here first
  - Tested before merging to `master`

### Supporting Branches

- **`feature/*`** - New features or enhancements
  - Branch from: `develop`
  - Merge back to: `develop`
  - Naming: `feature/descriptive-name`
  - Examples:
    - `feature/infrastructure` - Terraform and AWS setup
    - `feature/lambda-functions` - Lambda development
    - `feature/dashboard` - Frontend dashboard work
    - `feature/aws-native-forecast` - API integrations

- **`bugfix/*`** - Bug fixes
  - Branch from: `develop`
  - Merge back to: `develop`
  - Naming: `bugfix/issue-description`
  - Example: `bugfix/forecaster-memory-leak`

- **`hotfix/*`** - Critical production fixes
  - Branch from: `master`
  - Merge back to: `master` AND `develop`
  - Naming: `hotfix/critical-issue`
  - Example: `hotfix/cost-analyzer-crash`

- **`release/*`** - Release preparation
  - Branch from: `develop`
  - Merge back to: `master` and `develop`
  - Naming: `release/v1.x.x`
  - Example: `release/v1.2.0`

## 🔄 Development Workflow

### 1. Starting New Work

```bash
# Make sure you're on develop
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/your-feature-name

# Make your changes
# ... code, test, commit ...

# Push to GitHub
git push -u origin feature/your-feature-name
```

### 2. Making Changes

```bash
# Make small, focused commits
git add src/forecaster/lambda_function.py
git commit -m "feat(forecaster): add retry logic for API calls"

# Push regularly
git push origin feature/your-feature-name
```

### 3. Opening Pull Request

1. Go to GitHub repository
2. Click "Pull Requests" → "New Pull Request"
3. Set base branch to `develop`
4. Fill out PR template with:
   - Description of changes
   - Related issues
   - Testing performed
   - Screenshots (if UI changes)

### 4. Code Review

- Address reviewer feedback
- Keep PR focused and small
- Ensure all tests pass
- Update documentation

### 5. Merging

```bash
# After PR approval, squash and merge via GitHub UI
# Then update your local branch
git checkout develop
git pull origin develop

# Delete merged feature branch
git branch -d feature/your-feature-name
git push origin --delete feature/your-feature-name
```

## 📝 Commit Message Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/):

### Format
```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

### Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation only
- **style**: Code style (formatting, missing semicolons)
- **refactor**: Code refactoring
- **perf**: Performance improvement
- **test**: Adding tests
- **chore**: Maintenance tasks
- **ci**: CI/CD changes

### Examples
```bash
feat(forecaster): integrate AWS Cost Explorer native API
fix(notifier): resolve duplicate anomaly entries
docs(readme): update deployment instructions
refactor(recommender): extract service analysis logic
test(cost-analyzer): add unit tests for date parsing
chore(deps): upgrade boto3 to v1.28.0
```

## 🧪 Testing Requirements

Before submitting PR:

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Test individual Lambda functions
aws lambda invoke --function-name cloudcost-guardian-dev-cost-analyzer /tmp/test.json
```

## 📋 Pull Request Checklist

- [ ] Code follows project style guidelines
- [ ] All tests pass locally
- [ ] Added/updated tests for changes
- [ ] Updated documentation (README, OPERATIONS.md)
- [ ] Commit messages follow convention
- [ ] No sensitive data (credentials, keys) in code
- [ ] Terraform changes validated with `terraform plan`
- [ ] Lambda functions tested in AWS environment

## 🎯 Code Style

### Python
- Follow PEP 8
- Use type hints where appropriate
- Maximum line length: 100 characters
- Docstrings for all functions

```python
def fetch_cost_data(start_date: str, end_date: str) -> dict:
    """
    Fetch cost data from AWS Cost Explorer API.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        dict: Cost data grouped by service
    """
    pass
```

### Terraform
- Use consistent formatting: `terraform fmt`
- Add comments for complex resources
- Use variables for configurable values
- Group resources logically

## 🚀 Release Process

### Creating a Release

1. **Prepare Release Branch**
```bash
git checkout develop
git pull origin develop
git checkout -b release/v1.2.0
```

2. **Update Version Numbers**
- Update `version.py` or equivalent
- Update CHANGELOG.md
- Update README if needed

3. **Test Release**
```bash
terraform plan
pytest tests/
```

4. **Merge to Master**
```bash
# Create PR: release/v1.2.0 → master
# After approval, merge and tag
git checkout master
git pull origin master
git tag -a v1.2.0 -m "Release version 1.2.0"
git push origin v1.2.0
```

5. **Merge Back to Develop**
```bash
git checkout develop
git merge master
git push origin develop
```

## 🐛 Reporting Issues

When reporting bugs, include:

1. **Description**: Clear summary of the issue
2. **Steps to Reproduce**: Numbered steps
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**: 
   - AWS region
   - Lambda runtime version
   - Python version
6. **Logs**: Relevant CloudWatch logs
7. **Screenshots**: If applicable

## 📞 Getting Help

- **Documentation**: Check `/docs` folder
- **Operations**: See `docs/OPERATIONS.md`
- **Issues**: Open GitHub issue with question label
- **Discussions**: Use GitHub Discussions for general questions

## 🏆 Recognition

Contributors will be recognized in:
- README.md Contributors section
- Release notes
- Project documentation

Thank you for contributing to CloudCost Guardian! 🎉
