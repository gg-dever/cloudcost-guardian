#!/bin/bash
# CloudCost Guardian - Reconfigure Settings
# Update configuration without full redeployment

set -e

echo "═══════════════════════════════════════════════"
echo "  CloudCost Guardian - Update Configuration"
echo "═══════════════════════════════════════════════"
echo ""

cd terraform

if [ ! -f "terraform.tfvars" ]; then
    echo "❌ No existing configuration found."
    echo "   Run ./scripts/setup.sh first to deploy."
    exit 1
fi

echo "Current configuration:"
echo "────────────────────────────────────────────────"
cat terraform.tfvars
echo ""
echo "────────────────────────────────────────────────"
echo ""

# Ask what to update
echo "What would you like to update?"
echo "  1) Alert email address"
echo "  2) Daily cost threshold"
echo "  3) AWS region"
echo "  4) Analysis schedule"
echo "  5) View current values only (no changes)"
echo ""

read -p "Enter choice (1-5): " choice

case $choice in
    1)
        read -p "Enter new email for cost alerts: " new_email
        while [[ ! "$new_email" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; do
            echo "❌ Invalid email format"
            read -p "Enter new email for cost alerts: " new_email
        done
        
        # Update terraform.tfvars
        sed -i '' "s/alert_email[[:space:]]*=.*/alert_email            = \"$new_email\"/" terraform.tfvars
        echo "✓ Email updated to: $new_email"
        NEEDS_APPLY=true
        ;;
    
    2)
        read -p "Enter new daily cost threshold (e.g., 100, 250, 500): " new_threshold
        while ! [[ "$new_threshold" =~ ^[0-9]+$ ]]; do
            echo "❌ Please enter a valid number"
            read -p "Enter new daily cost threshold: " new_threshold
        done
        
        sed -i '' "s/cost_threshold_percent[[:space:]]*=.*/cost_threshold_percent = $new_threshold/" terraform.tfvars
        echo "✓ Cost threshold updated to: \$$new_threshold"
        NEEDS_APPLY=true
        ;;
    
    3)
        read -p "Enter new AWS region (e.g., us-east-1, us-west-2): " new_region
        sed -i '' "s/aws_region[[:space:]]*=.*/aws_region  = \"$new_region\"/" terraform.tfvars
        echo "✓ Region updated to: $new_region"
        echo "⚠️  Note: This will recreate all resources in the new region"
        NEEDS_APPLY=true
        ;;
    
    4)
        echo ""
        echo "Schedule format: cron(minute hour day month ? year)"
        echo "Examples:"
        echo "  Daily 8 AM UTC:    cron(0 8 * * ? *)"
        echo "  Daily 6 PM UTC:    cron(0 18 * * ? *)"
        echo "  Every 12 hours:    cron(0 */12 * * ? *)"
        echo ""
        read -p "Enter new schedule: " new_schedule
        
        sed -i '' "s|analysis_schedule[[:space:]]*=.*|analysis_schedule = \"$new_schedule\"|" terraform.tfvars
        echo "✓ Schedule updated to: $new_schedule"
        NEEDS_APPLY=true
        ;;
    
    5)
        echo "✓ No changes made"
        exit 0
        ;;
    
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "Updated configuration:"
echo "────────────────────────────────────────────────"
cat terraform.tfvars
echo "────────────────────────────────────────────────"
echo ""

if [ "$NEEDS_APPLY" = true ]; then
    read -p "Apply changes to AWS infrastructure? (yes/no): " confirm
    
    if [[ "$confirm" == "yes" ]]; then
        echo ""
        echo "🚀 Applying configuration changes..."
        terraform apply -auto-approve
        
        echo ""
        echo "═══════════════════════════════════════════════"
        echo "  ✅ Configuration Updated Successfully!"
        echo "═══════════════════════════════════════════════"
        
        if [[ $choice == 1 ]]; then
            echo ""
            echo "📧 IMPORTANT: Check your new email address"
            echo "   You'll receive an SNS subscription confirmation."
            echo "   Click the link to activate alerts at the new address."
        fi
    else
        echo "❌ Changes saved to terraform.tfvars but not applied"
        echo "   Run 'cd terraform && terraform apply' when ready"
    fi
fi

echo ""
