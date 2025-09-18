import os
from newsapi import NewsApiClient
import json
from app.models.schemas import ToolOutput
from langchain_core.tools import StructuredTool
import functools

# Read API key from environment variable
api_key = os.getenv('NEWSAPI_KEY')

if not api_key:
    raise ValueError(
        "NEWSAPI_KEY environment variable not set. Please set your NewsAPI key.")

newsapi = NewsApiClient(api_key=api_key)


def error_handling_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return ToolOutput(
                tool=func.__name__,
                input=kwargs if kwargs else (args[0] if args else {}),
                output=f"Error occurred during news API fetch: {e}",
                step=f"Failed to perform news fetch for input"
            )
    return wrapper


@error_handling_decorator
def real_estate_news_updates(
    query: str = (
        "housing law OR eviction OR rent increase OR tenant rights OR landlord rights OR "
        "property market OR mortgages OR real estate investing OR zoning laws OR "
        "property taxes OR affordable housing OR home repairs OR landlord insurance"
    )
):
    response = newsapi.get_everything(
        q=query,
        language='en',
        sort_by='relevancy',
        page_size=10,
    )

    articles = []
    for article in response.get('articles', []):
        articles.append({
            "title": article.get('title', 'No title'),
            "link": article.get('url', 'No link'),
            "source": article.get('source', {}).get('name', 'Unknown source'),
            "published": article.get('publishedAt', 'No date')
        })

    formatted_output = "\n".join(
        [f"{a['title']} ({a['source']} - {a['published']}): {a['link']}" for a in articles]
    )

    return ToolOutput(
        tool="real_estate_news_updates",
        input={"query": query},
        output=json.dumps({
            "articles": articles,
            "formatted": formatted_output
        }, indent=2),
        step="Retrieve recent news and policy updates on broad real estate topics"
    )


real_estate_news_tool = StructuredTool.from_function(
    func=real_estate_news_updates,
    name="real_estate_news_updates",
    description="Search recent NewsAPI articles covering a broad range of real estate topics including housing laws, market trends, mortgages, zoning, and repairs."
)

if __name__ == "__main__":
    result = real_estate_news_updates()
    print(result.output)
