import httpx

class ResearchProvider:
    def search(self, query: str) -> list[dict]:
        raise NotImplementedError

class DemoResearchProvider(ResearchProvider):
    def search(self, query: str):
        return [
            {"title":"Demo industry research","url":"https://example.com/demo-research",
             "summary":f"Illustrative research for {query}.","verified":False,"source_type":"demo"},
            {"title":"Demo competitor landscape","url":"https://example.com/demo-competitors",
             "summary":"Illustrative competitor positioning data; replace with a live provider in production.",
             "verified":False,"source_type":"demo"}
        ]

class WebResearchProvider(ResearchProvider):
    """Keyless web research using DuckDuckGo Instant Answer API.
    Falls back to clearly-labelled demo results if the network is unavailable.
    """
    endpoint = "https://api.duckduckgo.com/"

    def search(self, query: str):
        try:
            r = httpx.get(self.endpoint, params={"q":query, "format":"json", "no_html":1, "skip_disambig":1}, timeout=8)
            r.raise_for_status()
            data = r.json()
            results = []
            if data.get("AbstractText"):
                results.append({"title": data.get("Heading") or query,
                                 "url": data.get("AbstractURL") or "",
                                 "summary": data["AbstractText"],
                                 "verified": True, "source_type":"web"})
            for topic in data.get("RelatedTopics", [])[:5]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append({"title": topic.get("Text","")[:100],
                                    "url": topic.get("FirstURL",""),
                                    "summary": topic.get("Text",""),
                                    "verified": True, "source_type":"web"})
            if results:
                return results
        except Exception:
            pass
        return DemoResearchProvider().search(query)
