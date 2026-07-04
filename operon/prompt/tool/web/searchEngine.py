import yaml
import requests
import urllib.parse
from bs4 import BeautifulSoup

class SearchEngine:
    name = "SearchEngine"
    prompt = """SearchEngine
Search the web for websites, using duckduckgo search search engine

type: "SearchEngine"
data:
  query: "what you want to search"
  max_results: 5"""
    
    def run(self, value):
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
                    "fromTool": "SearchEngine",
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
