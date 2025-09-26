import os
from dotenv import load_dotenv
from newsapi import NewsApiClient
import json
from app.models.schemas import ToolOutput
from langchain_core.tools import StructuredTool
import functools

load_dotenv()  # Initialize loading of variables from .env before use

# Retrieve the NewsAPI key from environment variables
api_key = os.getenv('NEWSAPI_KEY')

# Raise an error if API key is not found
if not api_key:
    raise ValueError(
        "NEWSAPI_KEY environment variable not set. Please set your NewsAPI key."
    )

# Initialize NewsApiClient with the API key
newsapi = NewsApiClient(api_key=api_key)

# Decorator to handle errors during API calls gracefully


def error_handling_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)  # Call decorated function
        except Exception as e:
            # Return a ToolOutput object with error message if API call fails
            return ToolOutput(
                tool=func.__name__,
                input=kwargs if kwargs else (args[0] if args else {}),
                output=f"Error occurred during news API fetch: {e}",
                step=f"Failed to perform news fetch for input"
            )
    return wrapper


# Main function to get recent real estate news articles using NewsAPI
@error_handling_decorator
def real_estate_news_updates(
    query: str = (
        "housing law OR eviction OR rent increase OR housing rights OR tenant rights OR landlord rights OR "
        "property market OR mortgages OR real estate investing OR zoning laws OR "
        "property taxes OR affordable housing OR home repairs OR landlord insurance"
    )
):
    # Fetch news articles matching the query with language and sorting options
    response = newsapi.get_everything(
        q=query,
        language='en',
        sort_by='relevancy',
        page_size=10,
    )

    articles = []
    # Process each article to extract relevant information
    for article in response.get('articles', []):
        articles.append({
            "title": article.get('title', 'No title'),
            "link": article.get('url', 'No link'),
            "source": article.get('source', {}).get('name', 'Unknown source'),
            "published": article.get('publishedAt', 'No date')
        })

    # Create a formatted string of articles for easier reading
    formatted_output = "\n".join(
        [f"{a['title']} ({a['source']} - {a['published']}): {a['link']}" for a in articles]
    )

    # Return results wrapped in a ToolOutput object (used for integration with LangChain)
    return ToolOutput(
        tool="real_estate_news_updates",
        input={"query": query},
        output=json.dumps({
            "articles": articles,
            "formatted": formatted_output
        }, indent=2),
        step="Retrieve recent news and policy updates on broad real estate topics"
    )


# Create a StructuredTool instance for integration with LangChain workflows
real_estate_news_tool = StructuredTool.from_function(
    func=real_estate_news_updates,
    name="real_estate_news_updates",
    description="Search recent NewsAPI articles covering a broad range of real estate topics including housing laws, market trends, mortgages, zoning, and repairs."
)


# If run as a script, execute the function with default query and print output
if __name__ == "__main__":
    result = real_estate_news_updates()
    print(result.output)
