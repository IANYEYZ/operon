"""
Tool Server
Handle tool calls
"""

import yaml
from pathlib import Path

srcPath = Path(__file__).parent.parent / "file"

class ToolServer:
    def __init__(self):
        pass
    def __call__(self, value):
        if value["type"] == "Calculator":
            return yaml.dump({
                "type": "Result",
                "data": eval(value["data"])
            })
        elif value["type"] == "ReadFile":
            res = value["data"]
            name, start, end = res.name, res.start, res.end
            content = open(name).read()
            lines = content.splitlines(keepends=True)
            if start is None: start = 0
            if end is None: end = len(lines)
            return ''.join(lines[start:end])