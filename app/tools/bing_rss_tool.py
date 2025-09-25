import feedparser
from app.models.schemas import ToolOutput
from langchain_core.tools import StructuredTool

RSS_FEEDS = [
    "https://www.bing.com/news/search?q=california+tenant+rights&format=rss",
    "https://www.bing.com/news/search?q=california+eviction+moratorium&format=rss",
    "https://www.bing.com/news/search?q=california+rental+assistance+program&format=rss"
]

def fetch_rss_news(query: str) -> ToolOutput:
    results = []
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:  # top 5 per feed
            title = entry.get("title", "")
            link = entry.get("link", "")
            if query.lower() in title.lower():  
                results.append({"title": title, "link": link})

    return ToolOutput(
        tool="bing_rss_tool",
        input={"query": query},
        output=results,
        step="Fetch recent news from Bing News RSS feeds"
    )
# Create LangChain structured tool
bing_rss_tool = StructuredTool.from_function(
    func=fetch_rss_news,
    name="bing_rss_tool",
    description="Use this tool to fetch recent California tenant rights news, eviction moratorium updates, and rental assistance programs from Google News RSS feeds."
)
