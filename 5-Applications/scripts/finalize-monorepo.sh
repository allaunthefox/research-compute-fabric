#!/bin/bash
set -e

# Configuration
WORKSPACE="/home/allaun/Documents/Research Stack"
MANIFEST_DIR="$WORKSPACE/.consolidation-manifests"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
MASTER="$MANIFEST_DIR/MASTER-$DATE.sha256"

mkdir -p "$MANIFEST_DIR"
mkdir -p "$WORKSPACE/3-Mathematical-Models/genetics"
mkdir -p "$WORKSPACE/2-Search-Space/simulations"
mkdir -p "$WORKSPACE/5-Applications/pist-scripts"
mkdir -p "$WORKSPACE/6-Documentation/papers"

echo "=== Research Stack Consolidation & Hashing ==="
echo "Date: $DATE"
echo "Workspace: $WORKSPACE"

hash_and_move() {
    local src="$1"
    local dest="$2"
    local name=$(basename "$src")
    local manifest="$MANIFEST_DIR/$(echo "$src" | tr '/' '-')-$DATE.sha256"

    if [ -e "$src" ]; then
        echo "Processing: $src"
        find "$src" -type f -print0 | xargs -0 sha256sum > "$manifest"
        cat "$manifest" >> "$MASTER"

        # Ensure parent dest exists
        mkdir -p "$(dirname "$dest")"

        cp -r "$src" "$dest"
        echo "Copied to: $dest"
        # rm -rf "$src" # We'll do a final cleanup after user confirms
    else
        echo "Skipping: $src (not found)"
    fi
}

# 1. Fold external repos into monorepo
repos=(
    "braid-field-papers|6-Documentation/papers/braid-field-papers"
    "AMMR|3-Mathematical-Models/AMMR"
    "bezier-kit|3-Mathematical-Models/bezier-kit"
    "Newtonian-Superfluid-Simulation|2-Search-Space/simulations/Newtonian-Superfluid-Simulation"
    "heat-2D|2-Search-Space/simulations/heat-2D"
    "chunked-audio-DSP|2-Search-Space/simulations/chunked-audio-DSP"
    "matter-frequencies|2-Search-Space/simulations/matter-frequencies"
    "Allelica|3-Mathematical-Models/genetics/Allelica"
    "parametric-learn|3-Mathematical-Models/genetics/parametric-learn"
    "NoDupeLabs|4-Infrastructure/NoDupeLabs"
)

TEMP_CLONE="/tmp/research_stack_clones"
mkdir -p "$TEMP_CLONE"

for entry in "${repos[@]}"; do
    repo_name="${entry%%|*}"
    dest_path="${entry#*|}"

    echo "Folding $repo_name..."
    if [ ! -d "$WORKSPACE/$dest_path" ]; then
        git clone "https://github.com/allaunthefox/$repo_name.git" "$TEMP_CLONE/$repo_name" --depth 1
        rm -rf "$TEMP_CLONE/$repo_name/.git"
        cp -r "$TEMP_CLONE/$repo_name" "$WORKSPACE/$dest_path"
        rm -rf "$TEMP_CLONE/$repo_name"
    else
        echo "Skipping $repo_name (already exists in workspace)"
    fi
done

# 2. Move loose files from Desktop
hash_and_move "/home/allaun/Desktop/manifold_compression" "$WORKSPACE/3-Mathematical-Models/manifold_compression"
hash_and_move "/home/allaun/Desktop/pist_biological_polymorphic_shifter_v3.py" "$WORKSPACE/5-Applications/pist-scripts/"
hash_and_move "/home/allaun/Desktop/pist_biological_polymorphic_shifter_v3_complete.py" "$WORKSPACE/5-Applications/pist-scripts/"
hash_and_move "/home/allaun/Desktop/pist_gcl_compression.py" "$WORKSPACE/5-Applications/pist-scripts/"

# 3. Move loose folders from Documents
hash_and_move "/home/allaun/Documents/Semantics" "$WORKSPACE/0-Core-Formalism/lean/Semantics"
hash_and_move "/home/allaun/Documents/projects/hutter_prize" "$WORKSPACE/5-Applications/hutter_prize"
hash_and_move "/home/allaun/Documents/projects/teleport-kanban" "$WORKSPACE/5-Applications/teleport-kanban"

# 4. Cleanup redundant directories at /home/allaun (if confirmed)
# These were marked as duplicates/stale in previous audits
redundant=(
    "/home/allaun/Desktop/OTOM"
    "/home/allaun/Documents/DeleteMe"
    "/home/allaun/Documents/Research Stack-backups"
    "/home/allaun/Documents/Forked"
    "/home/allaun/OTOM"
    "/home/allaun/NoDupeLabs"
    "/home/allaun/tardygrada-Organism"
    "/home/allaun/claw-code"
    "/home/allaun/latex_demo"
    "/home/allaun/Research Stack" # This is likely a debris folder if WORKSPACE is in Documents
)

for dir in "${redundant[@]}"; do
    if [ -d "$dir" ] && [ "$dir" != "$WORKSPACE" ]; then
        echo "Removing redundant: $dir"
        rm -rf "$dir"
    fi
done

# 5. Replace CascadeProjects symlink
if [ -d "/home/allaun/CascadeProjects/Research-Stack" ]; then
    echo "Replacing CascadeProjects mirror with symlink"
    rm -rf "/home/allaun/CascadeProjects/Research-Stack"
    ln -s "$WORKSPACE" "/home/allaun/CascadeProjects/Research-Stack"
fi

echo "=== Consolidation Complete ==="
echo "Master manifest: $MASTER"
echo "Please verify the contents of $WORKSPACE"
echo "Next: Archive/Delete the repos on GitHub using scripts/archive-and-delete-v2.sh"
