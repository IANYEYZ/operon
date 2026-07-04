import yaml
from pathlib import Path

rootPath = Path(__file__).parent.parent.parent.parent.parent / "file"

class WriteFile:
    name = "WriteFile"
    prompt = """WriteFile:
Write a file to file system, note that the path should ALWAYS start at the root of virtual file system
The path should always be relative path, i.e. it should always start with ./
format of such tool call:

type: "WriteFile"
data:
  name: "file name to write to"
  content: "content to write"
  type: "a single character, either w or a; if w, the content will overwrite whatever previously is inside; if a, the content will append to what's previous inside that file"

The response for this call will be a type none result"""
    
    def run(self, value):
        res = value["data"]
        if res.get("name", None) == None:
            return yaml.dump({
                "type": "Error",
                "data": "parameter `name` is missing from this WriteFile tool call"
            })
        if res.get("content", None) == None:
            return yaml.dump({
                "type": "Error",
                "data": "parameter `content` is missing from this WriteFile tool call"
            })
        if res.get("type", None) == None:
            return yaml.dump({
                "type": "Error",
                "data": "parameter `type` is missing from this WriteFile tool call"
            })
        name, content, typ = res["name"], res["content"], res["type"]
        print(rootPath / name.lstrip("/\\"))
        (rootPath / name.lstrip("/\\")).parent.mkdir(parents=True, exist_ok=True)
        open(rootPath / name.lstrip("/\\"), typ, encoding="UTF-8").write(content)
        return yaml.dump({
            "type": "Result",
            "data": None
        })
