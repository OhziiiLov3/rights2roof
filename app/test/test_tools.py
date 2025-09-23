from app.tools.tavily_tools import tavily_search
from app.tools.time_tools import time_tool_fn
from app.tools.google_news_tool import real_estate_news_updates


# Test tools
if __name__ == "__main__":
    print("=== Tavily Tool ===")
    tavily_output = tavily_search("NYC rental assistance September 2025")
    print(tavily_output.model_dump_json(indent=2))

    print("=== Time Tool ===")
    time_output = time_tool_fn()
    print(time_output.model_dump_json(indent=2))

    print("=== News Tool ===")
    result = real_estate_news_updates()
    print(result.output)
