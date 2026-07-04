import yaml
from pathlib import Path

rootPath = Path(__file__).parent.parent.parent.parent.parent / "file"

class Ls:
    name = "Ls"
    prompt = """Ls:
List all the files and directories in the directory provided
The path should always be relative path, i.e. it should always start with ./
format of such tool call:

type: "Ls"
data: "path of the directory to list files and directories\""""
    
    def run(self, value):
        res = value["data"]
        if not isinstance(res, str):
            return yaml.dump({
                "type": "Error",
                "data": "data entry of Ls should be a string, indicating the path"
            })
        path = rootPath / res.lstrip("/\\")
        return yaml.dump({
            "type": "Result",
            "data": {
                "fromTool": "Ls",
                "value": [p.name for p in Path(path).iterdir()]
            }
        })
