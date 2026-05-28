"""
Load prompt
"""

from pathlib import Path
import json

srcPath = Path(__file__).parent
toolPath = srcPath / "prompt" / "tool"
skillPath = srcPath / "prompt" / "skill"

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
    skillList = loadFromFile(skillPath)
    toolPrompt = ""
    for pos, i in enumerate(toolList):
        toolPrompt += f"{pos + 4}: {i}\n\n"
    skillPrompt = ""
    for i in skillList:
        skillPrompt += f"{i}\n"
    template = template.replace(r"{{INSERT_TOOLS}}", toolPrompt).replace(r"{{INSERT_SKILLS}}", skillPrompt)
    return template

# print(loadSystemPrompt())