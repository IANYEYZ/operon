import yaml
from pathlib import Path

rootPath = Path(__file__).parent.parent.parent.parent.parent / "file"

class Mkdir:
    name = "Mkdir"
    prompt = """Mkdir:
Create a new directory
The path should always be relative path, i.e. it should always start with ./
format of such tool call:

type: "Mkdir"
data: "path of the new directory"

The response for this call will be a type none result"""
    
    def run(self, value):
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
