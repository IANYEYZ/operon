"""
Load prompt
"""

from pathlib import Path
import json

srcPath = Path(__file__).parent
toolPath = srcPath / "prompt" / "tool"

def loadFromFile(pth):
    path = pth
    if path.is_file():
        return [open(path).read()]
    else:
        config = json.load(open(path / "config.json"))
        result = []
        for k in config.keys():
            result.extend(loadFromFile(pth / config.get(k).get("fileName")))
        return result

def loadPrompt(name):
    return open(f"{srcPath}/prompt/{name}").read()

def loadSystemPrompt():
    template = loadPrompt("SYSTEM_TEMPLATE")
    toolList = loadFromFile(toolPath)
    toolPrompt = ""
    for pos, i in enumerate(toolList):
        toolPrompt += f"{pos + 3}: {i}\n\n"
    template = template.replace(r"{{INSERT_TOOLS}}", toolPrompt)
    return template

print(loadSystemPrompt())