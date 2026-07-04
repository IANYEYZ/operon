import yaml
import shutil
from pathlib import Path

rootPath = Path(__file__).parent.parent.parent.parent.parent / "file"

class Move:
    name = "Move"
    prompt = """Move:
Move a file to another location, if the new location doesn't exist yet, it'll be created
The path for src and dest should always be relative path, i.e. it should always start with ./
format of such tool call:

type: "Move"
data:
  src: "path/to/src/file.txt"
  dest: "path/to/dest/file.txt"

The response for this call will be a type none result"""
    
    def run(self, value):
        res = value["data"]
        src = res["src"]
        dest = res["dest"]
        root = rootPath.resolve()
        if not isinstance(src, str) or not src.strip():
            return yaml.dump({
                "type": "Error",
                "data": "src must be a non-empty string"
            })
        if not isinstance(dest, str) or not dest.strip():
            return yaml.dump({
                "type": "Error",
                "data": "dest must be a non-empty string"
            })
        src_path = (root / src.lstrip("/\\")).resolve()
        dest_path = (root / dest.lstrip("/\\")).resolve()
        try:
            src_path.relative_to(root)
        except ValueError:
            return yaml.dump({
                "type": "Error",
                "data": "Source path escapes rootPath"
            })
        try:
            dest_path.relative_to(root)
        except ValueError:
            return yaml.dump({
                "type": "Error",
                "data": "Destination path escapes rootPath"
            })
        if src_path == root:
            return yaml.dump({
                "type": "Error",
                "data": "Cannot move rootPath"
            })
        if src_path == dest_path:
            return yaml.dump({
                "type": "Error",
                "data": "Source and destination are the same"
            })
        if not src_path.exists():
            return yaml.dump({
                "type": "Error",
                "data": f"Source {src} does not exist"
            })
        if dest_path.exists():
            return yaml.dump({
                "type": "Error",
                "data": f"Destination {dest} already exists"
            })
        if src_path.is_dir():
            try:
                dest_path.relative_to(src_path)
                return yaml.dump({
                    "type": "Error",
                    "data": "Cannot move a directory into itself"
                })
            except ValueError:
                pass
        try:
            dest_path.parent.mkdir(
                parents=True,
                exist_ok=True
            )
            shutil.move(
                str(src_path),
                str(dest_path)
            )
            return yaml.dump({
                "type": "Result",
                "data": None
            })
        except Exception as e:
            return yaml.dump({
                "type": "Error",
                "data": str(e)
            })
