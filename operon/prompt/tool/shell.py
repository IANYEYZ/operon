import yaml
import subprocess
import os
from pathlib import Path

rootPath = Path(__file__).parent.parent.parent.parent / "file"

class Shell:
    name = "Shell"
    prompt = """Shell:
Run one or many shell commands
Note that change on cwd or env vairables won't be saved across multiple Shell runs
Note that make sure the command you run will stop, don't run command that will never stop on its own(starting a server, for example, will not stop on its own). In short, this is only for short commands, not something like starting a server

type: "Shell"
data:
  command: "Shell command to run"
  cwd: "Current working directory of this specific shell run, note that this is not optional"""
    
    def run(self, value):
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
        creationflags = 0
        start_new_session = False
        if os.name == "nt":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            start_new_session = True
        try:
            completed = subprocess.run(
                command,
                cwd=pth,
                shell=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                stdin=subprocess.DEVNULL,
                creationflags=creationflags,
                start_new_session=start_new_session,
            )
            return yaml.dump({
                "type": "Result",
                "data": {
                    "fromTool": "Shell",
                    "returncode": completed.returncode,
                    "stdout": completed.stdout,
                    "stderr": completed.stderr,
                    "cwd": str(pth),
                }
            })
        except subprocess.TimeoutExpired as e:
            return yaml.dump({
                "type": "Error",
                "data": {
                    "error": {
                        "type": "Timeout",
                        "message": "Shell command timed out",
                        "stdout": e.stdout,
                        "stderr": e.stderr,
                    }
                }
            })
        except Exception as e:
            return yaml.dump({
                "type": "Error",
                "data": str(e)
            })
