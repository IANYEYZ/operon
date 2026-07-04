"""
Tool Server
Handle tool calls
"""
import yaml
from pathlib import Path
import json
import importlib.util
import inspect

rootPath = Path(__file__).parent.parent / "file"
srcPath = Path(__file__).parent

class ToolServer:
    def __init__(self):
        self.tasks = json.loads(open(srcPath / "task.json").read())
        self.scratchPad = ""
        self.tools = {}
    def register(self, toolPath):
        toolPath = Path(toolPath)
        # print(toolPath)
        spec = importlib.util.spec_from_file_location(toolPath.stem, toolPath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        classes = [
            cls
            for _, cls in inspect.getmembers(module, inspect.isclass)
            if cls.__module__ == module.__name__
        ]
        cls = classes[0]
        instance = cls()
        self.tools[cls.name] = lambda value: instance.run(value)
    def __call__(self, value):
        if value.get("type") == None:
            return yaml.dump({
                "type": "Error",
                "data": "Missing `type` field in tool call"
            })
        if value["type"] == "Branch":
            from .branches import addBranch, branches
            if value["data"]["type"] == "Create":
                addBranch(value["data"]["goal"])
                return yaml.dump({
                    "type": "Result",
                    "data": None
                })
            else:
                print(branches)
                return yaml.dump({
                    "type": "Result",
                    "data": branches
                })
        else:
            if self.tools.get(value["type"]) != None:
                return self.tools[value["type"]](value)
            return yaml.dump({
                "type": "Error",
                "value": "Unknown tool call, did you miss spelled or accidently write the wrong call?"
            })

toolServer = ToolServer()

def loadFromConfig(toolServer: ToolServer, path: Path):
    if path.is_file():
        if path.suffix == ".py":
            toolServer.register(path)
    else:
        config = json.load(open(path / "config.json"))
        result = []
        for k in config.keys():
            loadFromConfig(toolServer, path / config.get(k).get("fileName"))
        return result