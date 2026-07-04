import yaml
from pathlib import Path

rootPath = Path(__file__).parent.parent.parent.parent.parent / "file"

class ReadFile:
    name = "ReadFile"
    prompt = """ReadFile:
Read a file from file system, note that the path should ALWAYS start at the root of virtual file system
The path should always be relative path, i.e. it should always start with ./
format of such tool call:

type: "ReadFile"
data:
  name: "file name to read from"
  start: "a number, indicating the start line to read, leave null to read from start"
  end: "a number, indicating the end line to read, leave null to read to end; note that the end line will not be read, thus it's a segment [start, end)\""""
    
    def run(self, value):
        res = value["data"]
        name, start, end = res["name"], res.get("start", None), res.get("end", None)
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
        content = open(rootPath / name.lstrip("/\\"), encoding="UTF-8").read()
        lines = content.splitlines(keepends=True)
        if start is None: start = 0
        if end is None: end = len(lines)
        if start < 0 or end < start:
            return yaml.dump({
                "type": "Error",
                "data": f"Invalid range [{start}, {end})"
            })
        return yaml.dump({
            "type": "Result",
            "data": {
                "fromTool": "ReadFile",
                "content": '\n'.join(lines[start:end]),
                "start": start,
                "end": end
            }
        })
