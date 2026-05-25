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

MANIFESTS_DIR="/etc/nixos/k3s-flake/manifests"

echo "[deploy] waiting for k3s cluster to be healthy..."
until kubectl cluster-info --request-timeout=5s >/dev/null 2>&1; do
  sleep 3
done
echo "[deploy] cluster is healthy"

echo "[deploy] ensuring CoreDNS has one schedulable replica per main workload node..."
kubectl -n kube-system scale deployment/coredns --replicas=3

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

  secret_key=$(sed -n 's/^secret-key=//p' "$AUTHENTIK_SECRETS")
  postgresql_password=$(sed -n 's/^postgresql-password=//p' "$AUTHENTIK_SECRETS")
  if kubectl get secret -n services authentik-env >/dev/null 2>&1; then
    echo "[deploy] preserving existing authentik-env runtime secret"
  elif [ -n "$secret_key" ] && [ -n "$postgresql_password" ]; then
    echo "[deploy] creating authentik-env from sops file..."
    kubectl create secret generic -n services authentik-env \
      --from-literal=AUTHENTIK_SECRET_KEY="$secret_key" \
      --from-literal=AUTHENTIK_POSTGRESQL__PASSWORD="$postgresql_password" \
      --from-literal=AUTHENTIK_POSTGRESQL__HOST=authentik-postgresql \
      --from-literal=AUTHENTIK_POSTGRESQL__PORT=5432 \
      --from-literal=AUTHENTIK_POSTGRESQL__NAME=authentik \
      --from-literal=AUTHENTIK_POSTGRESQL__USER=authentik
  fi
fi

echo "[deploy] applying authentik HelmChart..."
kubectl apply -f "$MANIFESTS_DIR/authentik/helm-chart.yaml"

echo "[deploy] applying all service manifests..."
find "$MANIFESTS_DIR" -maxdepth 1 -type d | sort | while read -r dir; do
  name=$(basename "$dir")
  # Skip root dir and authentik (managed via HelmChart)
  [ "$dir" = "$MANIFESTS_DIR" ] && continue
  [ "$name" = "authentik" ] && continue
  if [ -f "$dir/kustomization.yaml" ] || [ -f "$dir/kustomization.yml" ]; then
    echo "[deploy]   applying $name (kustomize)..."
    kubectl apply -k "$dir"
  else
    echo "[deploy]   applying $name..."
    kubectl apply -f "$dir"
  fi
done

echo "[deploy] done"
