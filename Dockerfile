# Multi-stage Dockerfile for CloudCost Guardian Lambda Functions
# Optimized for AWS Lambda runtime environment

FROM public.ecr.aws/lambda/python:3.11 AS base

# Install system dependencies
RUN yum install -y \
    gcc \
    python3-devel \
    && yum clean all

# Set working directory
WORKDIR /var/task

# Copy shared layer first (for better caching)
COPY lambda_layer/python/shared/ /var/task/shared/

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Lambda function code
# Default to cost_analyzer (override with docker build --build-arg)
ARG LAMBDA_FUNCTION=cost_analyzer
COPY src/${LAMBDA_FUNCTION}/ /var/task/

# Set Lambda handler
CMD ["lambda_${LAMBDA_FUNCTION}.lambda_handler"]


# ============================================================
# Individual Lambda Stage - Cost Analyzer
# ============================================================
FROM base AS cost-analyzer
COPY src/cost_analyzer/ /var/task/
COPY src/cost_analyzer/requirements.txt /var/task/function-requirements.txt
RUN pip install --no-cache-dir -r /var/task/function-requirements.txt
CMD ["lambda_cost_analyzer.lambda_handler"]


# ============================================================
# Individual Lambda Stage - Forecaster
# ============================================================
FROM base AS forecaster
COPY src/forecaster/ /var/task/
COPY src/forecaster/requirements.txt /var/task/function-requirements.txt
RUN pip install --no-cache-dir -r /var/task/function-requirements.txt
CMD ["lambda_forecaster.lambda_handler"]


# ============================================================
# Individual Lambda Stage - Recommender
# ============================================================
FROM base AS recommender
COPY src/recommender/ /var/task/
COPY src/recommender/requirements.txt /var/task/function-requirements.txt
RUN pip install --no-cache-dir -r /var/task/function-requirements.txt
CMD ["lambda_recommender.lambda_handler"]


# ============================================================
# Individual Lambda Stage - Notifier
# ============================================================
FROM base AS notifier
COPY src/notifier/ /var/task/
COPY src/notifier/requirements.txt /var/task/function-requirements.txt
RUN pip install --no-cache-dir -r /var/task/function-requirements.txt
CMD ["lambda_notifier.lambda_handler"]


# ============================================================
# Local Testing Stage with Additional Tools
# ============================================================
FROM base AS local-testing

# Install testing dependencies
COPY requirements.txt /var/task/requirements-dev.txt
RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    moto \
    awscli \
    boto3-stubs[essential]

# Copy all Lambda functions for local testing
COPY src/ /var/task/src/
COPY tests/ /var/task/tests/

# Set up environment for local testing
ENV PYTHONPATH=/var/task:/var/task/src
ENV AWS_DEFAULT_REGION=us-east-1

# Use bash as default for interactive testing
CMD ["/bin/bash"]
