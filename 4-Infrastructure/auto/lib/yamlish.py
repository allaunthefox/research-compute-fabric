# Bridge module for YAML loading with multiple backend support.
# Uses PyYAML if available, falls back to syck (python3-syck on Debian).
# Exists so importing code can do: from auto.lib.yamlish import load_yaml
from .config import load_yaml
__all__ = ["load_yaml"]
