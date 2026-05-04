#!/bin/bash
# DAG Build Logger
# Runs lake build with step-by-step logging, UUID, and timestamp tracking

set -e

REPO_ROOT="/home/allaun/Documents/Research Stack"
BUILD_LOG_DIR="$REPO_ROOT/out/build_logs"
BUILD_DAG_DIR="$REPO_ROOT/out/build_dag"

BUILD_ID=$(uuidgen)
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
LOG_FILE="${BUILD_LOG_DIR}/lake_build_$(date +%Y%m%d)_${BUILD_ID}.log"
DAG_FILE="${BUILD_DAG_DIR}/build_dag_$(date +%Y%m%d)_${BUILD_ID}.json"

mkdir -p "$BUILD_LOG_DIR" "$BUILD_DAG_DIR"

# Initialize DAG structure
cat > "$DAG_FILE" << EOF
{
  "build_id": "$BUILD_ID",
  "timestamp": "$TIMESTAMP",
  "commit": "$(git rev-parse HEAD)",
  "steps": []
}
EOF

# Function to log a step to both log file and DAG
log_step() {
    local step_id=$(uuidgen)
    local step_timestamp=$(date -u +"%Y-%M-%dT%H:%M:%SZ")
    local description="$1"
    local command="$2"
    
    # Log to file
    echo "[$step_timestamp] [${step_id:0:8}] $description" >> "$LOG_FILE"
    echo "Command: $command" >> "$LOG_FILE"
    
    # Append to DAG
    # Read current DAG, append step, write back
    local temp_dag=$(mktemp)
    jq --arg step_id "$step_id" \
       --arg step_timestamp "$step_timestamp" \
       --arg description "$description" \
       --arg command "$command" \
       '.steps += [{
         "step_id": $step_id,
         "timestamp": $step_timestamp,
         "description": $description,
         "command": $command
       }]' "$DAG_FILE" > "$temp_dag"
    mv "$temp_dag" "$DAG_FILE"
}

# Step 1: Initialize build environment
cd "$REPO_ROOT/tools/lean/Semantics" || exit 1
log_step "Initialize build environment" "cd \"$REPO_ROOT/tools/lean/Semantics\" && pwd"

# Step 2: Run lake build
log_step "Run lake build" "lake build"
lake build >> "$LOG_FILE" 2>&1

# Step 3: Capture build result
log_step "Capture build result" "echo 'Build completed'"

# Finalize DAG
jq --arg final_timestamp "$(date -u +"%Y-%M-%dT%H:%M:%SZ")" \
   --arg status "completed" \
   '. + {"final_timestamp": $final_timestamp, "status": $status}' "$DAG_FILE" > "${DAG_FILE}.tmp" && mv "${DAG_FILE}.tmp" "$DAG_FILE"

echo "Build log: $LOG_FILE"
echo "Build DAG: $DAG_FILE"
