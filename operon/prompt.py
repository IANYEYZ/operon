"""
Load prompt
"""

from pathlib import Path
import json
import importlib.util
import inspect

srcPath = Path(__file__).parent
toolPath = srcPath / "prompt" / "tool"
skillPath = srcPath / "prompt" / "skill"

def loadFromFile(pth):
    path = pth
    if path.is_file():
        if path.suffix == ".py":
            # print(path)
            spec = importlib.util.spec_from_file_location(path.stem, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            classes = [
                cls
                for _, cls in inspect.getmembers(module, inspect.isclass)
                if cls.__module__ == module.__name__
            ]
            cls = classes[0]
            return cls.prompt
        return [open(path).read()]
    else:
        config = json.load(open(path / "config.json"))
        result = []
        for k in config.keys():
            result.extend(loadFromFile(pth / config.get(k).get("fileName")))
        return result

def loadPrompt(name):
    return open(f"{srcPath}/prompt/{name}", encoding = "utf-8").read()

def loadSystemPrompt():
    template = loadPrompt("SYSTEM_TEMPLATE")
    toolList = loadFromFile(toolPath)
    skillList = loadFromFile(skillPath)
    toolPrompt = ""
    for pos, i in enumerate(toolList):
        toolPrompt += f"{pos + 5}: {i}\n\n"
    skillPrompt = ""
    for i in skillList:
        skillPrompt += f"{i}\n"
    template = template.replace(r"{{INSERT_TOOLS}}", toolPrompt).replace(r"{{INSERT_SKILLS}}", skillPrompt)
    return template

def loadBranchSystemPrompt():
    template = loadPrompt("BRANCH_SYSTEM_TEMPLATE")
    toolList = loadFromFile(toolPath)
    skillList = loadFromFile(skillPath)
    toolPrompt = ""
    for pos, i in enumerate(toolList):
        toolPrompt += f"{pos + 3}: {i}\n\n"
    skillPrompt = ""
    for i in skillList:
        skillPrompt += f"{i}\n"
    template = template.replace(r"{{INSERT_TOOLS}}", toolPrompt).replace(r"{{INSERT_SKILLS}}", skillPrompt)
    return template