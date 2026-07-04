import yaml
import re
from pathlib import Path

rootPath = Path(__file__).parent.parent.parent.parent.parent / "file"

class SearchInFiles:
    name = "SearchInFiles"
    prompt = """SearchInFiles:
search for text or regex patterns inside files under a directory(similar to grep)
The path should always be relative path, i.e. it should always start with ./

Binary files and very large files may be automatically skipped

type: "SearchInFiles"
data:
  path: "path of the directory or file to search in"
  query: "text or regex pattern to search for"
  regex: false # Whether query should be treated as regex
  caseSensitive: false # Whether search should be case sensitive
  include: ["*.py", "*.md"] # Optional glob patterns of files to include
  exclude: ["node_modules/*", ".git/*"] # Optional glob patterns of files to exclude
  context: 0 # Number of surrounding lines(before and after) to include
  maxResults: 50 # Maximum number of matches to return

The result of this call will be in the following format:

type: "Result"
data:
  truncated: false # Whether maxResults limit was reached
  matches:
    - file: "/project/main.py"
      line: 12 # Zero indexed line number
      column: 5 # Zero indexed column number
      content: "    # TODO: handle timeout"

      before: # Only exists when context > 0
        - line: 11
          content: "def fetch(url):"

      after: # Only exists when context > 0
        - line: 13
          content: "    return response.text\""""
    
    def run(self, value):
        res = value["data"]
        path = res["path"]
        query = res["query"]
        use_regex = res.get("regex", False)
        case_sensitive = res.get("caseSensitive", False)
        include = res.get("include", ["*"])
        exclude = res.get("exclude", [])
        context = res.get("context", 0)
        max_results = res.get("maxResults", 50)
        base = rootPath.resolve()
        target = (base / path.lstrip("/\\")).resolve()
        if not str(target).startswith(str(base)):
            return yaml.dump({
                "type": "Error",
                "data": "Path escapes rootPath"
            })
        if not target.exists():
            return yaml.dump({
                "type": "Error",
                "data": f"Path {path} doesn't exist"
            })
        if context < 0:
            return yaml.dump({
                "type": "Error",
                "data": "context must be >= 0"
            })
        if max_results <= 0:
            return yaml.dump({
                "type": "Error",
                "data": "maxResults must be > 0"
            })
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            if use_regex:
                pattern = re.compile(query, flags)
            else:
                pattern = re.compile(re.escape(query), flags)
        except re.error as e:
            return yaml.dump({
                "type": "Error",
                "data": f"Invalid regex: {e}"
            })
        MAX_FILE_SIZE = 2 * 1024 * 1024
        def is_excluded(file: Path) -> bool:
            rel = file.relative_to(base).as_posix()
            return any(file.match(pat) or rel.startswith(pat.rstrip("/")) or Path(rel).match(pat) for pat in exclude)
        def is_included(file: Path) -> bool:
            rel = file.relative_to(base).as_posix()
            return any(file.match(pat) or Path(rel).match(pat) for pat in include)
        def looks_binary(file: Path) -> bool:
            try:
                chunk = file.read_bytes()[:4096]
                return b"\x00" in chunk
            except Exception:
                return True
        if target.is_file():
            files = [target]
        else:
            files = [p for p in target.rglob("*") if p.is_file()]
        matches = []
        truncated = False
        for file in files:
            if not is_included(file): continue
            if is_excluded(file): continue
            try:
                if file.stat().st_size > MAX_FILE_SIZE: continue
            except OSError: continue
            if looks_binary(file): continue
            try:
                lines = file.read_text(
                    encoding="utf-8",
                    errors="replace"
                ).splitlines()
            except Exception:
                continue
            for line_no, line in enumerate(lines):
                for m in pattern.finditer(line):
                    item = {
                        "file": "/" + file.relative_to(base).as_posix(),
                        "line": line_no,
                        "column": m.start(),
                        "content": line,
                    }
                    if context > 0:
                        before_start = max(0, line_no - context)
                        after_end = min(len(lines), line_no + context + 1)
                        item["before"] = [{
                                "line": i,
                                "content": lines[i],
                            }
                            for i in range(before_start, line_no)
                        ]
                        item["after"] = [{
                                "line": i,
                                "content": lines[i],
                            }
                            for i in range(line_no + 1, after_end)
                        ]
                    matches.append(item)
                    if len(matches) >= max_results:
                        truncated = True
                        return yaml.dump({
                            "type": "Result",
                            "data": {
                                "fromTool": "SearchInFiles",
                                "truncated": truncated,
                                "matches": matches,
                            }
                        })
        return yaml.dump({
            "type": "Result",
            "data": {
                "fromTool": "SearchInFiles",
                "truncated": truncated,
                "matches": matches,
            }
        })
