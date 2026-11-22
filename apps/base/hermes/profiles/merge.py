"""Print a profile's config: the base config with the profile's overlay on top.

Mappings merge key by key, and any other overlay value replaces the base one.
A list under mcp_servers picks those servers from the base, so a profile never
restates their tool filters.
"""

import sys

from ruamel.yaml import YAML


def merge(base, overlay):
    merged = dict(base)
    for key, value in overlay.items():
        if key == "mcp_servers" and isinstance(value, list):
            merged[key] = {name: base[key][name] for name in value}
        elif isinstance(value, dict) and isinstance(base.get(key), dict):
            merged[key] = merge(base[key], value)
        else:
            merged[key] = value
    return merged


yaml = YAML(typ="safe")
base, overlay = (yaml.load(open(path)) or {} for path in sys.argv[1:3])
yaml.dump(merge(base, overlay), sys.stdout)
