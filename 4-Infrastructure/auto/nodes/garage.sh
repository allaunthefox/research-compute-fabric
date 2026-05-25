#!/bin/bash
# garage.sh — Garage cluster status probe
# Output: JSON with node list and health counts.

GARAGE_BIN=""
for p in /usr/local/bin/garage /run/current-system/sw/bin/garage /usr/bin/garage; do
    if [ -x "$p" ]; then
        GARAGE_BIN="$p"
        break
    fi
done

if [ -z "$GARAGE_BIN" ]; then
    echo '{"garage_reachable":false,"error":"garage binary not found"}'
    exit 0
fi

status_output=$("$GARAGE_BIN" -c /etc/garage/garage.toml status 2>/dev/null || true)
if [ -z "$status_output" ]; then
    echo '{"garage_reachable":false,"error":"garage status command failed or timed out"}'
    exit 0
fi

healthy=0
failed=0
nodes_json="["
section=""

while IFS= read -r line; do
    cleaned=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    [ -z "$cleaned" ] && continue

    if echo "$cleaned" | grep -q '^==== HEALTHY'; then
        section="healthy"
        continue
    elif echo "$cleaned" | grep -q '^==== FAILED'; then
        section="failed"
        continue
    fi

    # Skip header row
    if echo "$cleaned" | grep -q '^ID '; then
        continue
    fi

    # Data rows: ID is a 16-byte hex string
    if echo "$cleaned" | grep -qE '^[0-9a-f]{16} '; then
        if [ "$section" = "healthy" ]; then
            healthy=$((healthy + 1))
        elif [ "$section" = "failed" ]; then
            failed=$((failed + 1))
        fi

        id=$(echo "$cleaned" | awk '{print $1}')
        hostname=$(echo "$cleaned" | awk '{print $2}')
        addr=$(echo "$cleaned" | awk '{print $3}')
        zone=$(echo "$cleaned" | awk '{print $5}')

        # Capacity and DataAvail: fields 6+7 and 8+9+10
        capacity=$(echo "$cleaned" | awk '{print $6, $7}')
        data_avail=$(echo "$cleaned" | awk '{for(i=8;i<=NF;i++) printf "%s%s", $i, (i<NF?" ":"")}')

        [ "$nodes_json" != "[" ] && nodes_json+=","
        nodes_json+="{\"id\":\"$id\",\"hostname\":\"$hostname\",\"address\":\"$addr\",\"zone\":\"$zone\",\"capacity\":\"$capacity\",\"data_avail\":\"$data_avail\"}"
    fi
done <<< "$status_output"

nodes_json+="]"

printf '{"garage_reachable":true,"healthy_nodes":%s,"failed_nodes":%s,"nodes":%s}\n' \
    "$healthy" "$failed" "$nodes_json"
