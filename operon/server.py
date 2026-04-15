"""
Tool Server
Handle tool calls
"""

import yaml
from pathlib import Path
import subprocess
import json

rootPath = Path(__file__).parent.parent / "file"
srcPath = Path(__file__).parent

class ToolServer:
    def __init__(self):
        self.tasks = json.loads(open(srcPath / "task.json").read())
    def __call__(self, value):
        if value["type"] == "Calculator":
            return yaml.dump({
                "type": "Result",
                "data": eval(value["data"])
            })
        elif value["type"] == "ReadFile":
            res = value["data"]
            name, start, end = res["name"], res["start"], res["end"]
            content = open(rootPath / name).read()
            lines = content.splitlines(keepends=True)
            if start is None: start = 0
            if end is None: end = len(lines)
            return yaml.dump({
                "type": "Result",
                "data": '\n'.join(lines[start:end])
            })
        elif value["type"] == "WriteFile":
            res = value["data"]
            name, content, typ = res["name"], res["content"], res["type"]
            open(rootPath / name, typ).write(content)
            return yaml.dump({
                "type": "Result",
                "data": None
            })
        elif value["type"] == "Shell":
            res = value["data"]
            val = subprocess.run(res, cwd=rootPath, shell=True, capture_output=True, text=True).stdout
            return yaml.dump({
                "type": "Result",
                "data": val
            })
        elif value["type"] == "Task":
            res = value["data"]
            if res["type"] == "Add":
                self.tasks[res["name"]] = {"content": res["content"], "plan": []}
                return yaml.dump({
                    "type": "Result",
                    "data": None
                })
            elif res["type"] == "View":
                data = {}
                for p, i in enumerate(self.tasks.keys()):
                    data["task" + str(p)] = self.tasks[i]["content"]
                return yaml.dump({
                    "type": "Result",
                    "data": data
                })
            elif res["type"] == "Tick":
                self.tasks.pop(res["name"])
                return yaml.dump({
                    "type": "Result",
                    "data": None
                })
        elif value["type"] == "Plan":
            res = value["data"]
            if res["type"] == "Add":
                self.tasks[res["hook"]]["plan"].append(res["content"])
                return yaml.dump({
                    "type": "Result",
                    "data": None
                })
            elif res["type"] == "View":
                data = self.tasks[res["hook"]]["plan"]
                return yaml.dump({
                    "type": "Result",
                    "data": data
                })

toolServer = ToolServer()