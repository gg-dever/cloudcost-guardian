# Security Best Practices

## AWS Credentials Management

### ⚠️ NEVER commit credentials to Git

This project requires AWS credentials for deployment. Follow these practices:

### Storage Location
- **✅ Correct**: `~/.aws/keys/cloudcost-deployer_accessKeys.csv`
- **❌ Wrong**: Inside project directory

### File Permissions
```bash
chmod 600 ~/.aws/keys/cloudcost-deployer_accessKeys.csv
```

### Using AWS CLI
Recommended approach - configure credentials via AWS CLI:
```bash
aws configure --profile cloudcost
# Enter Access Key ID
# Enter Secret Access Key
# Default region: us-east-1
# Default output: json
```

Then reference the profile in Terraform:
```bash
export AWS_PROFILE=cloudcost
./scripts/setup.sh
```

### Key Rotation
Rotate IAM access keys every 90 days:
1. Create new access key in AWS IAM Console
2. Update `~/.aws/keys/` or run `aws configure --profile cloudcost`
3. Test new credentials
4. Deactivate old access key
5. Delete old access key after 24-48 hours

### If Credentials Are Compromised
1. Immediately rotate keys in AWS IAM Console
2. Review CloudTrail logs for unauthorized access
3. Check AWS Cost Explorer for unexpected charges
4. If committed to Git: Use `git-secrets` or BFG Repo-Cleaner to purge history

### Protected by .gitignore
The following patterns prevent credential leaks:
- `*.csv`
- `*.pem`
- `*.key`
- `cloudcost-deployer_accessKeys.csv`
- `credentials.json`
- `secrets.json`

## Security Scanning

This project uses:
- **TruffleHog**: Secret detection in CI/CD
- **Bandit**: Python security linting
- **GitHub Security Advisories**: Dependency vulnerability scanning

## Reporting Security Issues

Email: [Your security contact email]
Do not open public GitHub issues for security vulnerabilities.
