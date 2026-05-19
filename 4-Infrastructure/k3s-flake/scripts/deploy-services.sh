#!/usr/bin/env bash
set -euo pipefail

###########################################################################
# deploy-services.sh
#
# Idempotent service deployer for the k3s unified topology.
# Called by the deploy-k3s-services systemd oneshot on the server node.
#
# Flow:
#   1. Wait for k3s cluster to be healthy
#   2. Create the K8s Secret for authentik from the sops-decrypted file
#   3. Apply all manifests via kubectl
#   4. k3s built-in Helm controller picks up the HelmChart CRD for authentik
###########################################################################

MANIFESTS_DIR="$(dirname "$0")/../manifests"

echo "[deploy] waiting for k3s cluster to be healthy..."
until kubectl cluster-info --request-timeout=5s >/dev/null 2>&1; do
  sleep 3
done
echo "[deploy] cluster is healthy"

echo "[deploy] ensuring services namespace exists..."
kubectl get namespace services >/dev/null 2>&1 || kubectl create namespace services

# Authentik secrets from sops-decrypted file.
# The file format is an env file:
#   secret-key=<value>
#   postgresql-password=<value>
if [ -n "${AUTHENTIK_SECRETS:-}" ] && [ -f "$AUTHENTIK_SECRETS" ]; then
  echo "[deploy] creating authentik-secrets from sops file..."
  kubectl delete secret --ignore-not-found -n services authentik-secrets
  kubectl create secret generic -n services authentik-secrets \
    --from-env-file="$AUTHENTIK_SECRETS"
fi

echo "[deploy] applying all service manifests..."
kubectl apply -k "$MANIFESTS_DIR"

echo "[deploy] done"
