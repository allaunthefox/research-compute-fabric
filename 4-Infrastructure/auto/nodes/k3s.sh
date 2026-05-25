#!/bin/bash
# k3s.sh — k3s pod and service status probe (runs on nixos-laptop)
# Output: JSON with pod and service states. No Python dependency — pure bash + kubectl JSON.
# kubectl always outputs JSON when -o json is used, so we pipe it through our filtering.

for kcfg in "${KUBECONFIG:-}" /etc/rancher/k3s/k3s.yaml ~/.kube/config; do
    if [ -f "$kcfg" ]; then
        export KUBECONFIG="$kcfg"
        break
    fi
done

if ! command -v kubectl &>/dev/null; then
    echo '{"k3s_installed":false,"error":"kubectl not found"}'
    exit 0
fi

# Build pod list using the JSON from kubectl, parsed with awk
pods_raw=$(kubectl get pods -n services -o json 2>/dev/null || echo '{"items":[]}')

# Extract pod names, phases, and ready counts using grep/sed on formatted output
# kubectl get pods -n services -o wide is more reliable than parsing JSON in bash
pods_formatted=$(kubectl get pods -n services --no-headers -o wide 2>/dev/null || true)

total_pods=0
running_pods=0
pods_json="["
first=true

while IFS= read -r line; do
    [ -z "$line" ] && continue

    # Parse columns: NAME READY STATUS RESTARTS AGE IP NODE NOMINATED_READINESS_GATES
    name=$(echo "$line" | awk '{print $1}')
    ready=$(echo "$line" | awk '{print $2}')
    status=$(echo "$line" | awk '{print $3}')

    total_pods=$((total_pods + 1))
    if [ "$status" = "Running" ]; then
        running_pods=$((running_pods + 1))
    fi

    $first && first=false || pods_json+=","
    pods_json+="{\"name\":\"$name\",\"phase\":\"$status\",\"ready\":\"$ready\"}"
done <<< "$pods_formatted"

pods_json+="]"

# Services
svcs_formatted=$(kubectl get svc -n services --no-headers -o wide 2>/dev/null || true)
svcs_json="["
first=true

while IFS= read -r line; do
    [ -z "$line" ] && continue
    name=$(echo "$line" | awk '{print $1}')
    ports=$(echo "$line" | awk '{print $6}')

    $first && first=false || svcs_json+=","
    svcs_json+="{\"name\":\"$name\",\"ports\":\"$ports\"}"
done <<< "$svcs_formatted"

svcs_json+="]"

printf '{"k3s_installed":true,"total_pods":%s,"running_pods":%s,"pods":%s,"services":%s}\n' \
    "$total_pods" "$running_pods" "$pods_json" "$svcs_json"
