# AWS CloudCost Guardian

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![AWS](https://img.shields.io/badge/AWS-Lambda%20%7C%20DynamoDB-orange.svg)](https://aws.amazon.com/)
[![Terraform](https://img.shields.io/badge/Terraform-1.0+-purple.svg)](https://www.terraform.io/)
[![Docker](https://img.shields.io/badge/Docker-Supported-2496ED.svg?logo=docker)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Try Demo](https://img.shields.io/badge/Try%20Demo-Docker-2496ED?logo=docker&logoColor=white)](#-option-1-docker-demo-recommended-for-portfolio)
[![Deploy AWS](https://img.shields.io/badge/Deploy-AWS-FF9900?logo=amazonaws&logoColor=white)](#-option-2-full-aws-deploy)

> An intelligent AWS cost optimization platform that predicts budget overruns, generates actionable recommendations, and provides team-level cost attribution—all with a self-hosting cost of less than $3/month.

**🎯 Portfolio Project** | [View Portfolio Details](PORTFOLIO.md) | [LinkedIn Post Template](LINKEDIN_POST.md) | **[Try It Yourself →](#-quick-deployment-options)**

---

## � Portfolio Documentation

**For Recruiters & Hiring Managers:**
- 📄 [**Project Showcase**](PROJECT_SHOWCASE.md) - Quick overview with metrics and business value
- 🎨 [**Architecture Diagrams**](ARCHITECTURE_DIAGRAMS.md) - Visual system design with Mermaid diagrams
- 💼 [**Portfolio Details**](PORTFOLIO.md) - Complete technical deep-dive and talking points

**For Technical Interviews:**
- 🎤 [**Interview Prep Guide**](INTERVIEW_PREP.md) - Common questions with prepared answers
- 🏗️ [**Architecture Diagrams**](ARCHITECTURE_DIAGRAMS.md) - System design for whiteboard discussions
- 📖 [**Data Model**](docs/data-model.md) - DynamoDB schema design and rationale

**For LinkedIn/Social Media:**
- 📱 [**LinkedIn Post Templates**](LINKEDIN_POST.md) - 4 ready-to-use post options + carousel ideas
- 🎨 [**Architecture Diagrams**](ARCHITECTURE_DIAGRAMS.md) - Screenshot-ready visuals

**Technical Documentation:**
- 🔧 [**Operations Runbook**](docs/OPERATIONS.md) - Daily operations and troubleshooting
- 🔒 [**Security Best Practices**](docs/SECURITY.md) - Credential management and security
- 🤝 [**Contributing Guide**](CONTRIBUTING.md) - Git workflow and development standards

---

## �📊 Project Metrics

| Metric | Value |
|--------|-------|
| **Lines of Code** | 2,800+ (production) |
| **Test Coverage** | 100% on critical paths |
| **Documentation** | 1,500+ lines |
| **Operating Cost** | <$3/month |
| **Potential Savings** | $10K-$100K annually |
| **Deployment Time** | <5 minutes |

---

## ⚡ Try It Now

**Want to see it in action?** Try it yourself in 5 minutes:

```bash
# Docker Demo (No AWS account needed)
git clone https://github.com/YOUR_USERNAME/cloudcost-guardian.git
cd cloudcost-guardian
docker-compose up -d
sleep 30 && open http://localhost:8080
```

**Or deploy to your AWS account:**

```bash
# Full AWS deployment (<$3/month)
git clone https://github.com/YOUR_USERNAME/cloudcost-guardian.git
cd cloudcost-guardian
chmod +x scripts/quick-deploy.sh
./scripts/quick-deploy.sh
```

📖 **Detailed guides:** [Docker Demo](DOCKER_DEMO.md) | [All Deployment Options](#-quick-deployment-options)

---

## 🎯 Problem Statement

Organizations struggle with unpredictable cloud costs:
- **40% of cloud spend is wasted** (Flexera State of Cloud Report)
- **Cost surprises discovered 30 days later** when invoices arrive
- **No actionable insights** - alerts without recommendations
- **Lack of accountability** - can't attribute costs to teams

CloudCost Guardian solves this by providing predictive, prescriptive, and actionable cost intelligence.

## ✨ Key Features

### 1. Predictive Cost Forecasting
- 30-day rolling forecast using **AWS Cost Explorer native API**
- Production-grade predictions from AWS's ensemble models
- Budget overrun alerts **before** they happen
- Handles seasonality, trends, and usage patterns automatically

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
- **EventBridge Scheduler**: Triggers cost analyzer Lambda daily (08:00 UTC)
- **Cost Analyzer Lambda**: Fetches cost data from AWS Cost Explorer API

**Storage Layer:**
- **DynamoDB Tables**:
  - `cost_history`: Historical cost records and forecast predictions
  - `cost_anomalies`: Detected cost spikes and anomalies
  - `cost_recommendations`: Optimization suggestions

**Processing Layer:**
- **Forecaster Lambda**: Generates 30-day predictions using AWS Cost Explorer GetCostForecast API
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

---

## 🚀 Quick Deployment Options

### 🐳 Option 1: Docker Demo (Recommended for Portfolio)

Run the entire system locally with **zero AWS costs** - perfect for interviews and demonstrations!

```bash
# Ensure Docker Desktop is running, then:
docker-compose up -d

# Wait 30 seconds for initialization
sleep 30

# View dashboard
open http://localhost:8080

# Query data
docker exec cloudcost-localstack \
  awslocal dynamodb scan --table-name cost_history --max-items 5
```

**What you get:**
- ✅ All 4 Lambda functions running locally
- ✅ LocalStack emulating AWS services
- ✅ Web dashboard with sample data
- ✅ Live demo capability for interviews
- ✅ **Showcases Docker + DevOps skills**

**📖 Complete guide:** [DOCKER_DEMO.md](DOCKER_DEMO.md)

---

### ⚡ Option 2: Full AWS Deploy

Deploy to real AWS in under 10 minutes:

```bash
git clone https://github.com/YOUR_USERNAME/cloudcost-guardian.git
cd cloudcost-guardian
chmod +x scripts/quick-deploy.sh
./scripts/quick-deploy.sh
```

The script will:
- ✅ Check prerequisites
- ✅ Setup Python environment
- ✅ Configure email notifications (optional)
- ✅ Deploy all infrastructure
- ✅ Test all Lambda functions
- ✅ Provide deployment summary

**Cost:** ~$1-3/month | **📖 Detailed guide:** [DEMO_DEPLOYMENT.md](DEMO_DEPLOYMENT.md)

---

### 🎥 Option 3: Video or Screenshot Demo

Can't deploy to AWS or Docker? Create a video walkthrough or use sample data:
- **Video Demo Guide**: [DEMO_DEPLOYMENT.md](DEMO_DEPLOYMENT.md#option-2-video-demo)
- **Screenshot Demo**: [DEMO_DEPLOYMENT.md](DEMO_DEPLOYMENT.md#option-3-screenshots--documentation)
- **Interactive Dashboard**: [DEMO_DEPLOYMENT.md](DEMO_DEPLOYMENT.md#option-4-interactive-demo-website)

---

### 📤 Option 4: Push to GitHub

Share your portfolio project publicly:
- **Setup Guide**: [GITHUB_SETUP.md](GITHUB_SETUP.md)
- Includes: Repository configuration, topics, pinning, LinkedIn integration

---

## 🚀 Manual Deployment (Step-by-Step)

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

### 4. Configure Email Notifications (Optional)

```bash
# Copy the example tfvars file
cd terraform
cp terraform.tfvars.example terraform.tfvars

# Edit with your email address
nano terraform.tfvars
# Set: alert_email = "your-email@example.com"
```

### 5. Deploy Infrastructure

```bash
cd terraform
terraform init
terraform plan
terraform apply

# If you configured email, check your inbox and confirm the SNS subscription
```

### 6. Verify Deployment

```bash
# Test all Lambda functions
aws lambda invoke --function-name cloudcost-guardian-dev-cost-analyzer /tmp/test.json
aws lambda invoke --function-name cloudcost-guardian-dev-forecaster /tmp/test.json
aws lambda invoke --function-name cloudcost-guardian-dev-recommender /tmp/test.json
aws lambda invoke --function-name cloudcost-guardian-dev-notifier /tmp/test.json

# Check DynamoDB tables
aws dynamodb list-tables
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
- **Purpose**: Generates 30-day cost forecasts using AWS Cost Explorer API
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

- AWS Cost Explorer API (including GetCostForecast)
- Terraform AWS Provider
- Chart.js for visualizations
- AWS SDK for Python (Boto3)

## 📧 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check the `docs/` folder for detailed documentation
- Review Architecture Decision Records in `docs/adrs/`

---

**Built with ❤️ for AWS cost optimization**
