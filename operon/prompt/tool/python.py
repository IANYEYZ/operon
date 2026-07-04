import yaml
import subprocess
import sys
import tempfile
from pathlib import Path

rootPath = Path(__file__).parent.parent.parent.parent / "file"

class Python:
    name = "Python"
    prompt = """Python:
Run a piece of Python code, designed for quick calculation and fact checking. It's only designed to run short scripts. For longer scripts, consider save them in a file and use Shell tool to run them manually
Note that this code will be ran at the root of your file system(which is not the real file system, so remember to use ./xxx/yyy-ish relative path, instead of absolute ones)
format of such tool call:

type: "Python"
data:
  code: "code to execute"

The standard output will be returned"""
    
    def run(self, value):
        code = value["data"]["code"]
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, dir=rootPath, encoding="utf-8") as tmp:
            tmp.write(code)
            tmp.flush()
            tmp_path = tmp.name
        try:
            completed = subprocess.run(
                [sys.executable, tmp_path],
                cwd=rootPath,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=10,
                stdin=subprocess.DEVNULL,
            )
            if completed.returncode != 0:
                return yaml.dump({
                    "type": "Error",
                    "data": {
                        "error": {
                            "type": "PythonError",
                            "returncode": completed.returncode,
                            "stdout": completed.stdout,
                            "stderr": completed.stderr,
                        }
                    }
                })
            return yaml.dump({
                "type": "Result",
                "data": {
                    "fromTool": "Python",
                    "returncode": completed.returncode,
                    "stdout": completed.stdout,
                    "stderr": completed.stderr,
                }
            })
        except subprocess.TimeoutExpired as e:
            return yaml.dump({
                "type": "Error",
                "data": {
                    "error": {
                        "type": "Timeout",
                        "message": "Python code timed out",
                        "stdout": e.stdout,
                        "stderr": e.stderr,
                    }
                }
            })
        except Exception as e:
            return yaml.dump({
                "type": "Error",
                "data": {
                    "error": {
                        "type": type(e).__name__,
                        "message": str(e),
                    }
                }
            })
        finally:
            try:
                Path(tmp_path).unlink()
            except Exception:
                pass
