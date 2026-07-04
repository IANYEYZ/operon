import time
import yaml
class Sleep:
    name = "Sleep"
    prompt = """Sleep:
Pause running for a determined time, useful to wait for branches to finish

type: "Sleep"
data: 1000 # in milliseconds"""
    def run(self, value):
        duration = value["data"]
        try:
            duration = float(duration)
            if duration < 0:
                raise ValueError("Duration must be non-negative")
        except ValueError:
            return yaml.dump({
                "type": "Error",
                "data": "`duration` must be a non-negative number"
            })
        time.sleep(duration / 1000.0)
        return yaml.dump({
            "type": "Result",
            "data": None
        })