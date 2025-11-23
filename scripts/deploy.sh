#!/bin/bash

###############################################################################
# AWS CloudCost Guardian - Deployment Script
# 
# Automates the deployment of Lambda functions and infrastructure.
###############################################################################

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}AWS CloudCost Guardian Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}Virtual environment not activated. Activating...${NC}"
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo -e "${RED}Error: Virtual environment not found. Run setup-env.sh first.${NC}"
        exit 1
    fi
fi

# Package Lambda functions
echo -e "${BLUE}Packaging Lambda functions...${NC}"

LAMBDA_DIRS=("cost_analyzer" "forecaster" "recommender" "notifier")
mkdir -p lambda_packages

for lambda_dir in "${LAMBDA_DIRS[@]}"; do
    echo "  Packaging $lambda_dir..."
    
    # Create temp directory
    TEMP_DIR="lambda_packages/${lambda_dir}_temp"
    rm -rf "$TEMP_DIR"
    mkdir -p "$TEMP_DIR"
    
    # Copy Lambda function
    cp "src/${lambda_dir}/lambda_function.py" "$TEMP_DIR/"
    
    # Install dependencies
    if [ -f "src/${lambda_dir}/requirements.txt" ]; then
        pip install -r "src/${lambda_dir}/requirements.txt" -t "$TEMP_DIR/" --quiet
    fi
    
    # Create zip package
    cd "$TEMP_DIR"
    zip -r "../${lambda_dir}.zip" . -q
    cd - > /dev/null
    
    # Cleanup
    rm -rf "$TEMP_DIR"
    
    echo -e "  ${GREEN}✓ ${lambda_dir}.zip created${NC}"
done

echo ""

# Deploy with Terraform
echo -e "${BLUE}Deploying infrastructure with Terraform...${NC}"

cd terraform

# Initialize Terraform
echo "  Initializing Terraform..."
terraform init -input=false

# Validate configuration
echo "  Validating configuration..."
terraform validate

# Plan deployment
echo "  Planning deployment..."
terraform plan -out=tfplan

# Ask for confirmation
echo ""
read -p "Do you want to apply these changes? (yes/no): " confirm

if [ "$confirm" == "yes" ]; then
    echo "  Applying changes..."
    terraform apply tfplan
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    
    # Show outputs
    echo "Infrastructure outputs:"
    terraform output
    
    echo ""
    echo "Next steps:"
    echo "  1. Configure EventBridge rules to trigger Lambda functions"
    echo "  2. Upload dashboard files to S3 bucket"
    echo "  3. Subscribe to SNS topic for notifications"
    echo ""
else
    echo -e "${YELLOW}Deployment cancelled${NC}"
    rm tfplan
fi

cd ..

echo -e "${GREEN}Done!${NC}"
