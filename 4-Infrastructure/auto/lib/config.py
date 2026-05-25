#!/usr/bin/env python3
"""Configuration loader for infra_controller. Parses YAML, resolves paths."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any


CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def load_yaml(path: Path) -> dict[str, Any]:
    """Load YAML file, supporting both PyYAML and syck."""
    try:
        import yaml
        with open(path) as fh:
            return yaml.safe_load(fh) or {}
    except ImportError:
        pass
    # pyyaml not available? try syck (python3-syck on Debian)
    try:
        import syck
        return syck.load(open(path, 'rb').read()) or {}
    except ImportError:
        raise ImportError("No YAML library available. Install python3-pyyaml or python3-syck")


def resolve_env_vars(data: dict) -> dict:
    """Recursively resolve ${VAR} in string values."""
    if isinstance(data, dict):
        return {k: resolve_env_vars(v) for k, v in data.items()}
    if isinstance(data, list):
        return [resolve_env_vars(v) for v in data]
    if isinstance(data, str) and "${" in data:
        import re
        def _repl(m):
            return os.environ.get(m.group(1), "")
        return re.sub(r'\$\{([^}]+)\}', _repl, data)
    return data


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load and process the main config file."""
    if path is None:
        path = CONFIG_DIR / "nodes.yaml"
    raw = load_yaml(path)
    config = resolve_env_vars(raw)

    # Flatten nodes dict for convenience
    node_entries = config.get("nodes", {})
    flat_nodes = {}
    for name, cfg in node_entries.items():
        flat_nodes[name] = {
            "ip": cfg["tailscale_ip"],
            "ssh_target": cfg.get("ssh_target", f"root@{cfg['tailscale_ip']}"),
            "roles": cfg.get("roles", []),
            "probes": cfg.get("probes", ["system"]),
            "optional": cfg.get("optional", False),
        }
    config["nodes"] = flat_nodes
    return config
