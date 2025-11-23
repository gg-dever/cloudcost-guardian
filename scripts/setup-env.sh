#!/bin/bash

###############################################################################
# AWS CloudCost Guardian - Virtual Environment Setup Script
# 
# This script sets up a Python virtual environment and installs all
# necessary dependencies for local development.
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
VENV_DIR="venv"
PYTHON_VERSION="3.9"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}AWS CloudCost Guardian Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_CMD=$(command -v python3)
CURRENT_VERSION=$($PYTHON_CMD --version | cut -d' ' -f2 | cut -d'.' -f1,2)

echo "Found Python version: $CURRENT_VERSION"

# Check if Python version is compatible (3.9+)
if [ "$(printf '%s\n' "3.9" "$CURRENT_VERSION" | sort -V | head -n1)" != "3.9" ]; then
    echo -e "${RED}Error: Python 3.9 or higher is required${NC}"
    exit 1
fi

# Create virtual environment
echo ""
echo -e "${YELLOW}Creating virtual environment...${NC}"
if [ -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Virtual environment already exists. Removing old one...${NC}"
    rm -rf "$VENV_DIR"
fi

$PYTHON_CMD -m venv "$VENV_DIR"
echo -e "${GREEN}✓ Virtual environment created${NC}"

# Activate virtual environment
echo ""
echo -e "${YELLOW}Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo ""
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip setuptools wheel

# Install root dependencies
echo ""
echo -e "${YELLOW}Installing root dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Root dependencies installed${NC}"
else
    echo -e "${RED}Warning: requirements.txt not found${NC}"
fi

# Install Lambda dependencies
echo ""
echo -e "${YELLOW}Installing Lambda function dependencies...${NC}"

LAMBDA_DIRS=("cost_analyzer" "forecaster" "recommender" "notifier")

for lambda_dir in "${LAMBDA_DIRS[@]}"; do
    REQ_FILE="src/${lambda_dir}/requirements.txt"
    if [ -f "$REQ_FILE" ]; then
        echo "  Installing dependencies for $lambda_dir..."
        pip install -r "$REQ_FILE" --quiet
        echo -e "  ${GREEN}✓ $lambda_dir dependencies installed${NC}"
    else
        echo -e "  ${YELLOW}⚠ No requirements.txt found for $lambda_dir${NC}"
    fi
done

# Create .env template if it doesn't exist
echo ""
echo -e "${YELLOW}Creating environment template...${NC}"
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# AWS Configuration
AWS_REGION=us-east-1
AWS_PROFILE=default

# DynamoDB Tables
DYNAMODB_TABLE=cost-data
COST_TABLE=cost-data
FORECAST_TABLE=cost-forecasts
RECOMMENDATIONS_TABLE=cost-recommendations

# SNS Configuration
SNS_TOPIC_ARN=

# Cost Thresholds
DAILY_COST_THRESHOLD=100

# S3 Configuration
DASHBOARD_BUCKET=cloudcost-guardian-dashboard
EOF
    echo -e "${GREEN}✓ Created .env template${NC}"
    echo -e "${YELLOW}  Please update .env with your AWS configuration${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Display summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "To activate the virtual environment, run:"
echo -e "  ${YELLOW}source venv/bin/activate${NC}"
echo ""
echo "To deactivate, run:"
echo -e "  ${YELLOW}deactivate${NC}"
echo ""
echo "Next steps:"
echo "  1. Update .env with your AWS credentials and configuration"
echo "  2. Configure AWS CLI: aws configure"
echo "  3. Review and customize Terraform configurations in terraform/"
echo "  4. Run tests: pytest tests/"
echo ""
echo -e "${GREEN}Happy coding!${NC}"
