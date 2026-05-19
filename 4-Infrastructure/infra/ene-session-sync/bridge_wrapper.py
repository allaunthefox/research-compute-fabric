#!/usr/bin/env python3
"""Bridge wrapper — called by the Rust sync daemon to invoke Python infra surfaces.

Usage: python3 bridge_wrapper.py <infra_dir>
Reads JSON request from stdin, writes JSON response to stdout.

Request format:
  {"module": "ene_rds_wiki_layer", "payload": {"op": "recent", "limit": 5}}

Response format:
  {"ok": true, "data": {...}}  or  {"ok": false, "error": "..."}
"""

import inspect
import json
import os
import sys


def find_target_class(mod):
    """Find the first class in a module that has a handle_request method."""
    for _, obj in inspect.getmembers(mod, inspect.isclass):
        if hasattr(obj, "handle_request") and callable(getattr(obj, "handle_request", None)):
            return obj
    return None


def main():
    infra_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    sys.path.insert(0, infra_dir)
    os.chdir(infra_dir)

    req = json.load(sys.stdin)
    module_name = req.get("module", "")
    payload = req.get("payload", {})

    if not module_name:
        json.dump({"ok": False, "error": "missing 'module' field"}, sys.stdout)
        return

    try:
        mod = __import__(module_name, fromlist=[""])
    except Exception as e:
        json.dump({"ok": False, "error": f"import failed: {e}"}, sys.stdout)
        return

    target_class = find_target_class(mod)
    if target_class is None:
        # Fallback: try calling a module-level handle_request
        if hasattr(mod, "handle_request") and callable(mod.handle_request):
            try:
                result = mod.handle_request(payload)
                json.dump({"ok": True, "data": result}, sys.stdout)
            except Exception as e:
                json.dump({"ok": False, "error": f"handle_request error: {e}"}, sys.stdout)
            return
        json.dump(
            {"ok": False, "error": f"No class with handle_request in {module_name}"},
            sys.stdout,
        )
        return

    try:
        instance = target_class()
        result = instance.handle_request(payload)
        json.dump({"ok": True, "data": result}, sys.stdout)
    except Exception as e:
        json.dump({"ok": False, "error": f"handle_request error: {e}"}, sys.stdout)


if __name__ == "__main__":
    main()
