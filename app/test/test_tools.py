from app.tools.tavily_tools import tavily_search
from app.tools.time_tools import time_tool_fn
from app.tools.bing_rss_tool import fetch_rss_news
from app.tools.bing_rss_tool import bing_rss_tool
import os
from app.tools.legal_scan_tool import legiscan_tool



# Test tools
if __name__ == "__main__":
    print("=== Tavily Tool ===")
    # tavily_output = tavily_search("NYC rental assistance September 2025")
    # print(tavily_output.model_dump_json(indent=2))

    # print("=== Time Tool ===")
    # time_output = time_tool_fn()
    # print(time_output.model_dump_json(indent=2))

    # print("=== News Tool ===")
    # result = real_estate_news_updates()
    # print(result.output)

    # print("=== Google News RSS Tool ===")
    # rss_output = fetch_rss_news("tenant rights")  # pass a query string
    # result = bing_rss_tool.invoke({"query": "eviction moratorium"})
    # print(result.output)
    # print(rss_output.model_dump_json(indent=2))

    print("=== LegiScan Tool ===")
    # Test with a query
    result = legiscan_tool.invoke({"query": "tenant rights"})
    print(result.model_dump_json(indent=2))
    