#!/bin/bash
# Quick start script for ODCS Helm Chart deployment

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
RELEASE_NAME="${1:-odcs}"
NAMESPACE="${2:-odcs}"
CHART_PATH="./helm"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   ODCS Helm Chart Quick Start${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Release Name:${NC} $RELEASE_NAME"
echo -e "${YELLOW}Namespace:${NC} $NAMESPACE"
echo ""

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command -v helm &> /dev/null; then
    echo -e "${YELLOW}❌ Helm not found. Please install Helm 3.0+${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Helm found${NC}"

if ! command -v kubectl &> /dev/null; then
    echo -e "${YELLOW}❌ kubectl not found. Please install kubectl${NC}"
    exit 1
fi
echo -e "${GREEN}✓ kubectl found${NC}"

# Check if cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${YELLOW}❌ No Kubernetes cluster accessible${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Kubernetes cluster accessible${NC}"

echo ""

# Create namespace
echo -e "${BLUE}Creating namespace...${NC}"
if kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f - > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Namespace '$NAMESPACE' ready${NC}"
else
    echo -e "${YELLOW}⚠ Namespace '$NAMESPACE' already exists${NC}"
fi

echo ""

# Lint the chart
echo -e "${BLUE}Linting Helm chart...${NC}"
if helm lint "$CHART_PATH" > /dev/null; then
    echo -e "${GREEN}✓ Chart lint passed${NC}"
else
    echo -e "${YELLOW}❌ Chart lint failed${NC}"
    exit 1
fi

echo ""

# Check if release already exists
echo -e "${BLUE}Checking if release already exists...${NC}"
if helm list -n "$NAMESPACE" | grep -q "$RELEASE_NAME"; then
    echo -e "${YELLOW}Release '$RELEASE_NAME' already exists in namespace '$NAMESPACE'${NC}"
    read -p "Do you want to upgrade? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Upgrading release...${NC}"
        helm upgrade "$RELEASE_NAME" "$CHART_PATH" -n "$NAMESPACE"
    else
        echo "Cancelled."
        exit 0
    fi
else
    echo -e "${BLUE}Installing new release...${NC}"
    helm install "$RELEASE_NAME" "$CHART_PATH" -n "$NAMESPACE"
fi

echo ""
echo -e "${GREEN}✓ Deployment complete!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo ""
echo "1. Wait for pods to be ready:"
echo "   ${YELLOW}kubectl get pods -n $NAMESPACE -w${NC}"
echo ""
echo "2. Port-forward to access services:"
echo "   ${YELLOW}kubectl port-forward -n $NAMESPACE svc/$RELEASE_NAME-swagger 8080:8080${NC}"
echo "   ${YELLOW}kubectl port-forward -n $NAMESPACE svc/$RELEASE_NAME-postgrest 3000:3000${NC}"
echo ""
echo "3. Access the services:"
echo "   ${YELLOW}Swagger UI: http://localhost:8080${NC}"
echo "   ${YELLOW}PostgREST API: http://localhost:3000${NC}"
echo ""
echo "4. Test the API:"
echo "   ${YELLOW}curl http://localhost:3000/personen${NC}"
echo ""
echo -e "${BLUE}For more information, see helm/README.md${NC}"
echo ""

