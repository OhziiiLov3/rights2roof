# Import the necessary modules for LangChain tool structure and schema definitions
from langchain_core.tools import StructuredTool
from app.models.schemas import ToolOutput
from googlenews import GoogleNews
import json
import functools


# Initialize the Google News client for recent real estate related updates (within the last month)
google_news_real_estate = GoogleNews(lang='en', period='1m')


# Decorator for error handling
def error_handling_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return ToolOutput(
                tool=func.__name__,
                input=kwargs if kwargs else (args[0] if args else {}),
                output=f"Error occurred during news search: {e}",
                step=f"Failed to perform news search for input"
            )
    return wrapper


# Define the search function to get broad real estate news and policy updates
@error_handling_decorator
def real_estate_news_updates(
    query: str = (
        "housing law OR eviction OR rent increase OR tenant rights OR landlord rights OR "
        "property market OR mortgages OR real estate investing OR zoning laws OR "
        "property taxes OR affordable housing OR home repairs OR landlord insurance"
    )
):
    
    # Clear previous search results
    google_news_real_estate.clear()

    # Perform search with the combined broad real estate query
    google_news_real_estate.search(query)
    results = google_news_real_estate.results()

    # Limit results to top 10 articles for practical output size
    limited_results = results[:10] if results else []

    articles = []
    for article in limited_results:
        articles.append({
            "title": article.get('title', 'No title'),
            "link": article.get('link', 'No link'),
            "source": article.get('media', 'Unknown source'),
            "published": article.get('date', 'No date')
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
        step=f"Retrieve recent news and policy updates on broad real estate topics"
    )


# Construct the LangChain StructuredTool object for broad real estate news updates
real_estate_news_tool = StructuredTool.from_function(
    func=real_estate_news_updates,
    name="real_estate_news_updates",
    description="Search recent Google News articles covering a broad range of real estate topics including housing laws, market trends, mortgages, zoning, and repairs."
)