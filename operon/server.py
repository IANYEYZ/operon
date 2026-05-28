"""
Tool Server
Handle tool calls
"""

import yaml
from pathlib import Path
import json
import requests
import base64
from bs4 import BeautifulSoup
import shutil
import subprocess
import sys
import io
import contextlib
import re
import os
import urllib.parse

rootPath = Path(__file__).parent.parent / "file"
srcPath = Path(__file__).parent

TEXT_TYPES = (
    "text/",
    "application/json",
    "application/javascript",
    "application/xml",
)


def is_text_response(content_type: str) -> bool:
    if not content_type:
        return False
    content_type = content_type.lower()
    return any(
        content_type.startswith(t)
        for t in TEXT_TYPES
    )

class ToolServer:
    def __init__(self):
        self.tasks = json.loads(open(srcPath / "task.json").read())
        self.scratchPad = ""
    def __call__(self, value):
        if value["type"] == "Python":
            buffer = io.StringIO()
            curCwd = os.getcwd()
            try:
                os.chdir(rootPath)
                with contextlib.redirect_stdout(buffer):
                    exec(value["data"]["code"])
            finally:
                os.chdir(curCwd)
            return yaml.dump({
                "type": "Result",
                "data": repr(buffer.getvalue())
            })
        elif value["type"] == "Shell":
            res = value["data"]
            command = res["command"]
            cwd = res.get("cwd", ".")
            pth = rootPath / cwd.lstrip("/\\")
            if not pth.exists():
                return yaml.dump({
                    "type": "Error",
                    "data": f"cwd {cwd} doesn't exist"
                })
            if not pth.is_dir():
                return yaml.dump({
                    "type": "Error",
                    "data": f"cwd {cwd} is not a directory"
                })
            try:
                completed = subprocess.run(
                    command,
                    cwd=pth,
                    shell=True,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=30
                )
                return yaml.dump({
                    "type": "Result",
                    "data": {
                        "returncode": completed.returncode,
                        "stdout": completed.stdout,
                        "stderr": completed.stderr,
                        "cwd": str(pth),
                    }
                })
            except subprocess.TimeoutExpired:
                return yaml.dump({
                    "type": "Error",
                    "data": "Shell command timed out"
                })
            except Exception as e:
                return yaml.dump({
                    "type": "Error",
                    "data": str(e)
                })
        elif value["type"] == "ReadFile":
            res = value["data"]
            name, start, end = res["name"], res.get("start", None), res.get("end", None)
            if not (rootPath / name.lstrip("/\\")).exists():
                return yaml.dump({
                    "type": "Error",
                    "data": f"File {name} doesn't exist"
                })
            if not (rootPath / name.lstrip("/\\")).is_file():
                return yaml.dump({
                    "type": "Error",
                    "data": f"{name} is not a file"
                })
            content = open(rootPath / name.lstrip("/\\"), encoding="UTF-8").read()
            lines = content.splitlines(keepends=True)
            if start is None: start = 0
            if end is None: end = len(lines)
            return yaml.dump({
                "type": "Result",
                "data": '\n'.join(lines[start:end])
            })
        elif value["type"] == "WriteFile":
            res = value["data"]
            name, content, typ = res["name"], res["content"], res["type"]
            print(rootPath / name.lstrip("/\\"))
            (rootPath / name.lstrip("/\\")).parent.mkdir(parents=True, exist_ok=True)
            open(rootPath / name.lstrip("/\\"), typ, encoding="UTF-8").write(content)
            return yaml.dump({
                "type": "Result",
                "data": None
            })
        elif value["type"] == "PatchFile":
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
        elif value["type"] == "SearchInFiles":
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
                                    "truncated": truncated,
                                    "matches": matches,
                                }
                            })
            return yaml.dump({
                "type": "Result",
                "data": {
                    "truncated": truncated,
                    "matches": matches,
                }
            })
        elif value["type"] == "Mkdir":
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
        elif value["type"] == "Ls":
            res = value["data"]
            if not isinstance(res, str):
                return yaml.dump({
                    "type": "Error",
                    "data": "data entry of Ls should be a string, indicating the path"
                })
            path = rootPath / res.lstrip("/\\")
            return yaml.dump({
                "type": "Result",
                "data": [p.name for p in Path(path).iterdir()]
            })
        elif value["type"] == "Move":
            res = value["data"]
            src, dest = res["src"], res["dest"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(src, dest)
            return yaml.dump({
                "type": "Result",
                "data": None
            })
        elif value["type"] == "Task":
            res = value["data"]
            if res["type"] == "Add":
                self.tasks[res["name"]] = {"content": res["content"], "plan": []}
                return yaml.dump({
                    "type": "Result",
                    "data": None
                })
            elif res["type"] == "View":
                data = {}
                for p, i in enumerate(self.tasks.keys()):
                    data["task" + str(p)] = self.tasks[i]["content"]
                return yaml.dump({
                    "type": "Result",
                    "data": data
                })
            elif res["type"] == "Tick":
                if not res["name"] in self.tasks.keys():
                    return yaml.dump({
                        "type": "Error",
                        "data": "The task the plan want to hook to didn't exist; Check for typo or create it"
                    })
                self.tasks.pop(res["name"])
                return yaml.dump({
                    "type": "Result",
                    "data": None
                })
        elif value["type"] == "Plan":
            res = value["data"]
            if res["type"] == "Add":
                if not res["hook"] in self.tasks.keys():
                    return yaml.dump({
                        "type": "Error",
                        "data": "The task the plan want to hook to didn't exist; Check for typo or create it"
                    })
                self.tasks[res["hook"]]["plan"].append(res["content"])
                return yaml.dump({
                    "type": "Result",
                    "data": None
                })
            elif res["type"] == "View":
                if not res["hook"] in self.tasks.keys():
                    return yaml.dump({
                        "type": "Error",
                        "data": "The task the plan want to hook to didn't exist; Check for typo or create it"
                    })
                data = self.tasks[res["hook"]]["plan"]
                return yaml.dump({
                    "type": "Result",
                    "data": data
                })
        elif value["type"] == "Memory":
            res = value["data"]
            if res["type"] == "Add":
                name, content = res["name"], res["content"]
                open(srcPath.parent / "memory" / name, "w").write(content)
            elif res["type"] == "View":
                name = res["name"]
                if name == None:
                    return yaml.dump({
                        "type": "Result",
                        "data": [p.name for p in Path(srcPath.parent / "memory").iterdir()]
                    })
                else:
                    if not (srcPath.parent / "memory" / name).exists():
                        return yaml.dump({
                            "type": "Error",
                            "data": f"Memory {name} doesn't exist"
                        })
                    return yaml.dump({
                        "type": "Result",
                        "data": open(srcPath.parent / "memory" / name, "r").read()
                    })
        elif value["type"] == "ScratchPad":
            append = value["data"]["append"]
            self.scratchPad += append
            return yaml.dump({
                "type": "Result",
                "data": self.scratchPad
            })
        elif value["type"] == "Fetch":
            try:
                data = value["data"]
                response = requests.request(
                    method=data.get("method", "GET"),
                    url=data["url"],
                    headers=data.get("headers"),
                    params=data.get("params"),
                    data=data.get("body"),
                    timeout=data.get("timeout", 10),
                    allow_redirects=True,
                )

                result = {
                    "type": "Result",
                    "data": {
                        "response": {
                            "status_code": response.status_code,
                            "reason": response.reason,
                            "url": response.url,
                            "headers": dict(response.headers),
                        }
                    }
                }
                content_type = response.headers.get("Content-Type", "")

                if is_text_response(content_type):
                    result["data"]["response"]["text"] = response.text

                else:
                    result["data"]["response"]["content_base64"] = (
                        base64.b64encode(response.content)
                        .decode("utf-8")
                    )

                return yaml.dump(result)
            except requests.Timeout:
                return yaml.dump({
                    "type": "Error",
                    "data": {
                        "error": {
                            "type": "Timeout",
                            "message": "Request timed out",
                        }
                    }
                })
            except requests.RequestException as e:
                return yaml.dump({
                    "type": "Error",
                    "data": {
                        "error": {
                            "type": type(e).__name__,
                            "message": str(e),
                        }
                    }
                })
        elif value["type"] == "SearchEngine":
            try:
                query = value["data"]["query"]
                maxResults = value["data"].get("max_results", 10)
                if not isinstance(query, str) or not query.strip():
                    return yaml.dump({
                        "type": "Error",
                        "data": "query must be a non-empty string"
                    })
                if not isinstance(maxResults, int) or maxResults <= 0:
                    return yaml.dump({
                        "type": "Error",
                        "data": "max_results must be a positive integer"
                    })
                url = "https://html.duckduckgo.com/html/"
                params = {"q": query}
                headers = {
                    "User-Agent": "OperonAgent/0.1"
                }
                try:
                    resp = requests.post(
                        url,
                        data=params,
                        headers=headers,
                        timeout=15
                    )
                except requests.Timeout:
                    return yaml.dump({
                        "type": "Error",
                        "data": "Search request timed out"
                    })
                except requests.ConnectionError:
                    return yaml.dump({
                        "type": "Error",
                        "data": "Failed to connect to search engine"
                    })
                except requests.RequestException as e:
                    return yaml.dump({
                        "type": "Error",
                        "data": f"Request failed: {e}"
                    })
                if resp.status_code != 200:
                    return yaml.dump({
                        "type": "Error",
                        "data": f"HTTP {resp.status_code}"
                    })
                try:
                    soup = BeautifulSoup(resp.text, "html.parser")
                except Exception as e:
                    return yaml.dump({
                        "type": "Error",
                        "data": f"Failed to parse HTML: {e}"
                    })
                results = []
                for a in soup.select("a.result__a")[:maxResults]:
                    try:
                        title = a.get_text(strip=True)
                        link = a.get("href", "")
                        if not link:
                            continue
                        # DuckDuckGo redirect unwrap
                        if "uddg=" in link:
                            parsed = urllib.parse.urlparse(link)
                            qs = urllib.parse.parse_qs(parsed.query)
                            if "uddg" in qs:
                                link = urllib.parse.unquote(qs["uddg"][0])
                        snippet_text = ""
                        result_block = a.find_parent("div", class_="result")
                        if result_block:
                            snippet = result_block.select_one(".result__snippet")
                            if snippet:
                                snippet_text = snippet.get_text(strip=True)
                        results.append({
                            "title": title,
                            "snippet": snippet_text,
                            "url": link
                        })
                    except Exception:
                        continue
                return yaml.dump({
                    "type": "Result",
                    "data": {
                        "query": query,
                        "count": len(results),
                        "results": results
                    }
                })
            except KeyError as e:
                return yaml.dump({
                    "type": "Error",
                    "data": f"Missing field: {e}"
                })
            except Exception as e:
                return yaml.dump({
                    "type": "Error",
                    "data": str(e)
                })

toolServer = ToolServer()