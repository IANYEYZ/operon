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
            content = open(rootPath / name.lstrip("/\\")).read()
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
            print(rootPath / name.lstrip("/\\"))
            open(rootPath / name.lstrip("/\\"), typ).write(content)
            return yaml.dump({
                "type": "Result",
                "data": None
            })
        elif value["type"] == "Mkdir":
            res = value["data"]
            path = rootPath / res.lstrip("/\\")
            Path(path).mkdir(parents = True, exist_ok = True)
            return yaml.dump({
                "type": "Result",
                "data": None
            })
        elif value["type"] == "Ls":
            res = value["data"]
            path = rootPath / res.lstrip("/\\")
            return yaml.dump({
                "type": "Result",
                "data": [p.name for p in Path(path).iterdir()]
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
                if not res["name"] in self.tasks.keys():
                    return yaml.dump({
                        "type": "Error",
                        "data": "The task the plan want to hook to didn't exist; Check for typo or create it"
                    })
                self.tasks.pop(res["name"])
                return yaml.dump({
                    "type": "Result",
                    "data": None
                })
        elif value["type"] == "Plan":
            res = value["data"]
            if res["type"] == "Add":
                if not res["hook"] in self.tasks.keys():
                    return yaml.dump({
                        "type": "Error",
                        "data": "The task the plan want to hook to didn't exist; Check for typo or create it"
                    })
                self.tasks[res["hook"]]["plan"].append(res["content"])
                return yaml.dump({
                    "type": "Result",
                    "data": None
                })
            elif res["type"] == "View":
                if not res["hook"] in self.tasks.keys():
                    return yaml.dump({
                        "type": "Error",
                        "data": "The task the plan want to hook to didn't exist; Check for typo or create it"
                    })
                data = self.tasks[res["hook"]]["plan"]
                return yaml.dump({
                    "type": "Result",
                    "data": data
                })

toolServer = ToolServer()