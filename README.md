# AWS CloudCost Guardian

> An intelligent AWS cost optimization platform that predicts budget overruns, generates actionable recommendations, and provides team-level cost attribution—all with a self-hosting cost of less than $3/month.

## 🎯 Problem Statement

Organizations struggle with unpredictable cloud costs:
- **40% of cloud spend is wasted** (Flexera State of Cloud Report)
- **Cost surprises discovered 30 days later** when invoices arrive
- **No actionable insights** - alerts without recommendations
- **Lack of accountability** - can't attribute costs to teams

CloudCost Guardian solves this by providing predictive, prescriptive, and actionable cost intelligence.

## ✨ Key Features

### 1. Predictive Cost Forecasting
- 30-day rolling forecast with 85%+ accuracy
- Budget overrun alerts **before** they happen
- Trend analysis across services and teams
- ML-powered predictions using historical patterns

### 2. Intelligent Recommendations
- Automated detection of right-sizing opportunities
- Savings Plan recommendations with ROI calculations
- Unused resource identification
- Priority scoring (HIGH/MEDIUM/LOW impact)
- Service-specific optimization strategies

### 3. Cost Attribution Dashboard
- Team-level cost breakdown
- Service-level drill-down
- Interactive visualizations with Chart.js
- Month-over-month comparisons
- Real-time cost tracking

### 4. Anomaly Detection
- Daily cost spike detection
- Service-specific anomaly identification
- Baseline comparison with historical patterns
- Automated alerting via SNS

## 🏗️ Architecture

```
[EventBridge Schedule] → [Cost Analyzer Lambda] → [Cost Explorer API]
                                ↓
                         [DynamoDB Tables]
                                ↓
                ┌───────────────┼───────────────┐
                ↓               ↓               ↓
          [Forecaster]    [Recommender]    [Notifier]
            Lambda           Lambda          Lambda
                ↓               ↓               ↓
                └───────────────┴───────────────┘
                                ↓
                          [SNS Topic] → Email
                                ↓
                  [S3 + CloudFront Dashboard]
```

### Component Breakdown

**Data Collection Layer:**
- **EventBridge Scheduler**: Triggers Lambda functions daily (00:00, 01:00, 02:00, 03:00 UTC)
- **Cost Analyzer Lambda**: Fetches cost data from AWS Cost Explorer API

**Storage Layer:**
- **DynamoDB Tables**: 
  - `cost-data`: Historical cost records
  - `cost-forecasts`: ML predictions
  - `cost-recommendations`: Optimization suggestions

**Processing Layer:**
- **Forecaster Lambda**: Generates 30-day predictions using scikit-learn
- **Recommender Lambda**: Analyzes patterns and creates actionable recommendations
- **Notifier Lambda**: Detects anomalies and sends threshold alerts

**Presentation Layer:**
- **S3 Static Website**: Interactive dashboard with Chart.js visualizations
- **CloudFront CDN**: Global content delivery (optional)
- **SNS**: Email/SMS notifications for critical alerts

## 📋 Prerequisites

- **Python**: 3.9 or higher
- **AWS CLI**: Configured with appropriate credentials
- **Terraform**: v1.0+ (for infrastructure deployment)
- **AWS Account**: With Cost Explorer API enabled
- **IAM Permissions**: Access to Lambda, DynamoDB, S3, SNS, Cost Explorer

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd cloudcost-guardian
```

### 2. Set Up Virtual Environment

```bash
# Run the setup script
chmod +x scripts/setup-env.sh
./scripts/setup-env.sh

# Activate the environment
source venv/bin/activate
```

### 3. Configure AWS Credentials

```bash
# Configure AWS CLI
aws configure

# Update .env file with your settings
nano .env
```

### 4. Deploy Infrastructure

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### 5. Generate Test Data (Optional)

```bash
python scripts/seed-data.py
```

## 📁 Project Structure

```
cloudcost-guardian/
├── README.md                          # Project overview
├── .gitignore                         # Git exclusions
├── requirements.txt                   # Python dependencies
├── setup.py                          # Package configuration
├── runtime.txt                       # Python version
│
├── terraform/                        # Infrastructure as Code
│   ├── main.tf                      # Main configuration
│   ├── variables.tf                 # Input variables
│   ├── outputs.tf                   # Output values
│   └── modules/                     # Reusable modules
│       ├── lambda/                  # Lambda functions
│       ├── dynamodb/                # Database tables
│       ├── sns/                     # Notifications
│       └── s3/                      # Storage & hosting
│
├── src/                             # Application code
│   ├── cost_analyzer/               # Lambda: Fetch & analyze costs
│   │   ├── lambda_function.py
│   │   └── requirements.txt
│   ├── forecaster/                  # Lambda: Predict future costs
│   │   ├── lambda_function.py
│   │   └── requirements.txt
│   ├── recommender/                 # Lambda: Generate recommendations
│   │   ├── lambda_function.py
│   │   └── requirements.txt
│   ├── notifier/                    # Lambda: Send alerts
│   │   ├── lambda_function.py
│   │   └── requirements.txt
│   └── dashboard/                   # Static website
│       ├── index.html
│       ├── css/
│       ├── js/
│       └── data/
│
├── docs/                            # Documentation
│   ├── adrs/                        # Architecture decisions
│   ├── diagrams/                    # Architecture diagrams
│   ├── setup.md                     # Detailed setup guide
│   └── api-documentation.md         # API reference
│
├── tests/                           # Test files
│   ├── test_cost_analyzer.py
│   └── test_forecaster.py
│
└── scripts/                         # Utility scripts
    ├── setup-env.sh                 # Environment setup
    ├── deploy.sh                    # Deployment automation
    └── seed-data.py                 # Test data generator
```

## 🛠️ Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_cost_analyzer.py
```

### Code Quality

```bash
# Format code
black src/

# Lint code
flake8 src/
pylint src/

# Type checking
mypy src/
```

### Local Development

```bash
# Install in development mode
pip install -e ".[dev]"

# Run individual Lambda functions locally
python src/cost_analyzer/lambda_function.py
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_PROFILE=default

# DynamoDB Tables
DYNAMODB_TABLE=cost-data
COST_TABLE=cost-data
FORECAST_TABLE=cost-forecasts
RECOMMENDATIONS_TABLE=cost-recommendations

# SNS Configuration
SNS_TOPIC_ARN=arn:aws:sns:region:account:topic

# Cost Thresholds
DAILY_COST_THRESHOLD=100

# S3 Configuration
DASHBOARD_BUCKET=cloudcost-guardian-dashboard
```

### Terraform Variables

Update `terraform/variables.tf` or create `terraform.tfvars`:

```hcl
aws_region          = "us-east-1"
project_name        = "cloudcost-guardian"
cost_threshold      = 100
notification_email  = "your-email@example.com"
```

## 📊 Lambda Functions

### Cost Analyzer
- **Trigger**: EventBridge (daily at 00:00 UTC)
- **Purpose**: Fetches daily costs from Cost Explorer API
- **Output**: Stores data in DynamoDB

### Forecaster
- **Trigger**: EventBridge (daily at 01:00 UTC)
- **Purpose**: Generates 30-day cost forecasts using ML
- **Output**: Stores predictions in DynamoDB

### Recommender
- **Trigger**: EventBridge (daily at 02:00 UTC)
- **Purpose**: Analyzes costs and generates optimization recommendations
- **Output**: Stores recommendations in DynamoDB

### Notifier
- **Trigger**: EventBridge (daily at 03:00 UTC)
- **Purpose**: Checks thresholds and sends alerts
- **Output**: Sends SNS notifications

## 🚨 Alerts & Notifications

Configure SNS topic to receive alerts for:
- Daily cost threshold exceeded
- Unusual service cost spikes
- Forecast predictions above target
- Critical optimization opportunities

## 📈 Dashboard

Access your dashboard at: `http://your-bucket.s3-website-region.amazonaws.com`

Features:
- Real-time cost visualization
- Historical trend analysis
- Service-level breakdowns
- Forecast charts
- Recommendation cards

## 🔒 Security

- **Sensitive Files**: AWS credentials are gitignored
- **IAM Roles**: Lambda functions use least-privilege IAM roles
- **Encryption**: DynamoDB tables use encryption at rest
- **VPC**: Optional VPC deployment for enhanced security

⚠️ **Important**: Never commit `.csv` files, credentials, or `.tfstate` files to version control.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- AWS Cost Explorer API
- Terraform AWS Provider
- Chart.js for visualizations
- scikit-learn for ML forecasting

## 📧 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check the `docs/` folder for detailed documentation
- Review Architecture Decision Records in `docs/adrs/`

---

**Built with ❤️ for AWS cost optimization**


