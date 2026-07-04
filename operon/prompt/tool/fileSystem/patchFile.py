import yaml
from pathlib import Path

rootPath = Path(__file__).parent.parent.parent.parent.parent / "file"

class PatchFile:
    name = "PatchFile"
    prompt = """patchFile:
edit a section of a file(i.e. change all [start, end) lines to a new content, zero-indexed)
The path should always be relative path, i.e. it should always start with ./
The exact thing happening:
every line(say it's the i-th line, zero-indexed), if start <= i < end, it'll be deleted
then, content will be inserted before the start-th line(the start-th line now is the end-th line originally)

type: "PatchFile"
data:
  name: "file name to patch"
  start: 10 # A number, indicating the start line of the content that will be replaced
  end: 20 # A number, indicating the end line of the content that will be replaced
  content: "The new content\""""
    
    def run(self, value):
        res = value["data"]
        name, start, end, content = res["name"], res["start"], res["end"], res["content"]
        pth = rootPath / name.lstrip("/\\")
        if not pth.exists():
            return yaml.dump({
                "type": "Error",
                "data": f"File {name} doesn't exist"
            })
        if not (rootPath / name.lstrip("/\\")).is_file():
            return yaml.dump({
                "type": "Error",
                "data": f"{name} is not a file"
            })
        if start < 0 or end < start:
            return yaml.dump({
                "type": "Error",
                "data": f"Invalid range [{start}, {end})"
            })
        lines = pth.read_text(
            encoding="utf-8"
        ).splitlines(keepends=True)
        if start > len(lines):
            return yaml.dump({
                "type": "Error",
                "data": "start exceeds file length"
            })
        replacement = content.splitlines(
            keepends=True
        )
        new_lines = (
            lines[:start] + replacement + lines[end:]
        )
        pth.write_text(
            "".join(new_lines),
            encoding="utf-8"
        )
        return yaml.dump({
            "type": "Result",
            "data": None
        })
