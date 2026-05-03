#!/bin/bash

# ==============================================================================
# The Civic Navigator - GCP Cloud Run Deployment Script
# ==============================================================================
# This script deploys both the Next.js Frontend and the FastAPI Backend to
# Google Cloud Run, automatically injecting enterprise secrets via Secret Manager.
# ==============================================================================

# Variables
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
SERVICE_ACCOUNT_NAME="civic-navigator-backend"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Ensure the user is logged in and project is set
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: No GCP project set. Please run 'gcloud config set project [YOUR_PROJECT_ID]'"
    exit 1
fi

echo "🚀 Starting Deployment for The Civic Navigator to Project: $PROJECT_ID"

# ------------------------------------------------------------------------------
# 1. IAM & Service Account Setup (Run once per project)
# ------------------------------------------------------------------------------
echo "🔒 Checking for existing Service Account..."
if ! gcloud iam service-accounts describe "$SERVICE_ACCOUNT_EMAIL" --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo "Creating Service Account: $SERVICE_ACCOUNT_NAME..."
    gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
        --display-name="The Civic Navigator Cloud Run Identity"
    
    # Grant Secret Manager Access
    echo "Granting Secret Manager Access to Service Account..."
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
        --role="roles/secretmanager.secretAccessor"
else
    echo "✅ Service Account already exists."
fi

# ------------------------------------------------------------------------------
# 2. Deploy Backend (Python FastAPI)
# ------------------------------------------------------------------------------
echo "🐍 Deploying FastAPI Backend to Cloud Run..."
gcloud run deploy civic-navigator-backend \
    --source ./backend \
    --region "$REGION" \
    --service-account "$SERVICE_ACCOUNT_EMAIL" \
    --allow-unauthenticated \
    --set-secrets="GEMINI_API_KEY=gemini-api-key:latest,CIVIC_INFO_API_KEY=civic-info-api-key:latest,WALLET_ISSUER_ID=wallet-issuer-id:latest,WALLET_CLASS_ID=wallet-class-id:latest"

# Get backend URL
BACKEND_URL=$(gcloud run services describe civic-navigator-backend --region "$REGION" --format 'value(status.url)')
echo "✅ Backend Deployed: $BACKEND_URL"

# ------------------------------------------------------------------------------
# 3. Deploy Frontend (Next.js)
# ------------------------------------------------------------------------------
echo "⚛️  Deploying Next.js Frontend to Cloud Run..."
gcloud run deploy civic-navigator-frontend \
    --source ./frontend \
    --region "$REGION" \
    --service-account "$SERVICE_ACCOUNT_EMAIL" \
    --allow-unauthenticated \
    --set-env-vars="BACKEND_URL=$BACKEND_URL" \
    --set-secrets="NEXTAUTH_SECRET=nextauth-secret:latest,GOOGLE_CLIENT_ID=google-oauth-client-id:latest,GOOGLE_CLIENT_SECRET=google-oauth-client-secret:latest"

FRONTEND_URL=$(gcloud run services describe civic-navigator-frontend --region "$REGION" --format 'value(status.url)')
echo "✅ Frontend Deployed: $FRONTEND_URL"

# ------------------------------------------------------------------------------
# 4. Post-Deployment Sync (Connect Backend to Frontend for CORS)
# ------------------------------------------------------------------------------
echo "🔐 Securing Backend CORS with Frontend URL..."
gcloud run services update civic-navigator-backend \
    --region "$REGION" \
    --set-env-vars="FRONTEND_URL=$FRONTEND_URL"

echo "🎉 Deployment Complete!"
