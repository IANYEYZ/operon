import yaml
import requests
import base64

def is_text_response(content_type: str) -> bool:
    TEXT_TYPES = (
        "text/",
        "application/json",
        "application/javascript",
        "application/xml",
    )
    if not content_type:
        return False
    content_type = content_type.lower()
    return any(
        content_type.startswith(t)
        for t in TEXT_TYPES
    )

class Fetch:
    name = "Fetch"
    prompt = """Fetch
Fetch a web page

type: "Fetch"
data:
  url: "the url you want to fetch"
  method: "GET or POST or PATCH"
  headers:
    User-Agent: "Operon/0.1"
  params:
    ...
  body:
    ...
  body: null
  timeout: 10"""
    
    def run(self, value):
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
                        "fromTool": "Fetch",
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
