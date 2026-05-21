"""
Tool Server
Handle tool calls
"""

import yaml
from pathlib import Path
import json
import requests
import base64

rootPath = Path(__file__).parent.parent / "file"
srcPath = Path(__file__).parent

TEXT_TYPES = (
    "text/",
    "application/json",
    "application/javascript",
    "application/xml",
)


def is_text_response(content_type: str) -> bool:
    if not content_type:
        return False

    content_type = content_type.lower()

    return any(
        content_type.startswith(t)
        for t in TEXT_TYPES
    )

class ToolServer:
    def __init__(self):
        self.tasks = json.loads(open(srcPath / "task.json").read())
        self.scratchPad = ""
    def __call__(self, value):
        if value["type"] == "Python":
            result = {}
            exec(value["data"]["code"], {}, result)
            return yaml.dump({
                "type": "Result",
                "data": result[value["result"]]
            })
        elif value["type"] == "ReadFile":
            res = value["data"]
            name, start, end = res["name"], res["start"], res["end"]
            if not (rootPath / name.lstrip("/\\")).exists():
                return yaml.dump({
                    "type": "Error",
                    "data": f"File {name} doesn't exist"
                })
            if not (rootPath / name.lstrip("/\\")).is_file():
                return yaml.dump({
                    "type": "Error",
                    "data": f"{name} is not a file"
                })
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
            if not (rootPath / name.lstrip("/\\")).exists():
                return yaml.dump({
                    "type": "Error",
                    "data": f"File {name} doesn't exist"
                })
            if not (rootPath / name.lstrip("/\\")).is_file():
                return yaml.dump({
                    "type": "Error",
                    "data": f"{name} is not a file"
                })
            open(rootPath / name.lstrip("/\\"), typ).write(content)
            return yaml.dump({
                "type": "Result",
                "data": None
            })
        elif value["type"] == "Mkdir":
            res = value["data"]
            if not isinstance(res, str):
                return yaml.dump({
                    "type": "Error",
                    "data": "data entry of Mkdir should be a string, indicating the path"
                })
            path = rootPath / res.lstrip("/\\")
            Path(path).mkdir(parents = True, exist_ok = True)
            return yaml.dump({
                "type": "Result",
                "data": None
            })
        elif value["type"] == "Ls":
            res = value["data"]
            if not isinstance(res, str):
                return yaml.dump({
                    "type": "Error",
                    "data": "data entry of Ls should be a string, indicating the path"
                })
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
        elif value["type"] == "Memory":
            res = value["data"]
            if res["type"] == "Add":
                name, content = res["name"], res["content"]
                open(srcPath.parent / "memory" / name, "w").write(content)
            elif res["type"] == "View":
                name = res["name"]
                if name == None:
                    return yaml.dump({
                        "type": "Result",
                        "data": [p.name for p in Path(srcPath.parent / "memory").iterdir()]
                    })
                else:
                    if not (srcPath.parent / "memory" / name).exists():
                        return yaml.dump({
                            "type": "Error",
                            "data": f"Memory {name} doesn't exist"
                        })
                    return yaml.dump({
                        "type": "Result",
                        "data": open(srcPath.parent / "memory" / name, "r").read()
                    })
        elif value["type"] == "ScratchPad":
            append = value["data"]["append"]
            self.scratchPad += append
            return yaml.dump({
                "type": "Result",
                "data": self.scratchPad
            })
        elif value["type"] == "Fetch":
            try:
                data = value["data"]
                response = requests.request(
                    method=data.get("method", "GET"),
                    url=data["url"],
                    headers=data.get("headers"),
                    params=data.get("params"),
                    data=data.get("body"),
                    timeout=data.get("timeout", 10),
                    allow_redirects=True,
                )

                result = {
                    "type": "Result",
                    "data": {
                        "response": {
                            "status_code": response.status_code,
                            "reason": response.reason,
                            "url": response.url,
                            "headers": dict(response.headers),
                        }
                    }
                }
                content_type = response.headers.get("Content-Type", "")

                if is_text_response(content_type):
                    result["data"]["response"]["text"] = response.text

                else:
                    result["data"]["response"]["content_base64"] = (
                        base64.b64encode(response.content)
                        .decode("utf-8")
                    )

                return yaml.dump(result)
            except requests.Timeout:
                return yaml.dump({
                    "type": "Error",
                    "data": {
                        "error": {
                            "type": "Timeout",
                            "message": "Request timed out",
                        }
                    }
                })
            except requests.RequestException as e:
                return yaml.dump({
                    "type": "Error",
                    "data": {
                        "error": {
                            "type": type(e).__name__,
                            "message": str(e),
                        }
                    }
                })

toolServer = ToolServer()