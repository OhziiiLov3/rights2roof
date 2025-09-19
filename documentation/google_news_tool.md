# Real Estate News Tool – LangChain, NewsAPI & Slack Chatbot Integration  
### Documentation by Cecilia Kanne  


***  
## Table of Contents  
- [Real Estate News Tool](#real-estate-news-tool)  
  - [Step 1 – Import Packages](#step-1--import-packages)  
  - [Step 2 – Load Environment Variable and Initialize NewsAPI Client](#step-2--load-environment-variable-and-initialize-newsapi-client)  
  - [Step 3 – Define Real Estate News Search Function](#step-3--define-real-estate-news-search-function)  
  - [Step 4 – Wrap Function as StructuredTool](#step-4--wrap-function-as-structuredtool)  
  - [Step 5 – Example Usage](#step-5--example-usage)  
- [Slack Chatbot Integration](#slack-chatbot-integration)  
  - [Step 6 – Load Environment Variables for Slack and Initialize Client](#step-6--load-environment-variables-for-slack-and-initialize-client)  
  - [Step 7 – Define Async Slack Response Handler](#step-7--define-async-slack-response-handler)  
  - [Step 8 – Implement Slack Slash Command Endpoint](#step-8--implement-slack-slash-command-endpoint)  
  - [Step 9 – Run and Test](#step-9--run-and-test)  


***  


# Real Estate News Tool  


### Step 1 – Import Packages  
<details>  
<summary>📂 Code</summary>  


```python
import os  # for environment variable access
from newsapi import NewsApiClient  # official NewsAPI Python client
import json  # for JSON encoding/decoding
from app.models.schemas import ToolOutput  # custom structured output type
from langchain_core.tools import StructuredTool  # LangChain structured tool wrapper
import functools  # for error handling decorator
```


</details>  


**Explanation:**  
Imports packages necessary for API access, data serialization, LangChain tooling, and error handling.  


***  


### Step 2 – Load Environment Variable and Initialize NewsAPI Client  
<details>  
<summary>📂 Code</summary>  


```python
# Read NewsAPI key from environment variable securely
api_key = os.getenv('NEWSAPI_KEY')

# Raise error if API key not set to prevent silent failures
if not api_key:
    raise ValueError("NEWSAPI_KEY environment variable not set. Please set your NewsAPI key.")

# Initialize NewsAPI client with the API key
newsapi = NewsApiClient(api_key=api_key)
```


</details>  


**Explanation:**  
Secures the API key by loading from environment and initializes NewsAPI client for subsequent requests.  


***  


### Step 3 – Define Real Estate News Search Function  
<details>  
<summary>📂 Code</summary>  


```python
# Decorator to catch exceptions and return structured error info
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
                step="Failed to perform news fetch for input"
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
    # Fetch news articles matching the broad real estate query
    response = newsapi.get_everything(
        q=query,
        language='en',
        sort_by='relevancy',
        page_size=10,
    )

    articles = []
    for article in response.get('articles', []):
        # Extract key article details for output
        articles.append({
            "title": article.get('title', 'No title'),
            "link": article.get('url', 'No link'),
            "source": article.get('source', {}).get('name', 'Unknown source'),
            "published": article.get('publishedAt', 'No date')
        })

    # Format the collected articles into a readable string
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
```


</details>  


**Explanation:**  
Defines the search function querying NewsAPI with error handling and returns structured output with raw data and formatted string for display.  


***  


### Step 4 – Wrap Function as StructuredTool  
<details>  
<summary>📂 Code</summary>  


```python
# Wrap the search function in a LangChain tool for easy invocation in workflows
real_estate_news_tool = StructuredTool.from_function(
    func=real_estate_news_updates,
    name="real_estate_news_updates",
    description="Search recent NewsAPI articles covering a broad range of real estate topics including housing laws, market trends, mortgages, zoning, and repairs."
)
```


</details>  


**Explanation:**  
This prepares the function for use as an automated tool in LangChain's orchestration or agents.  


***  


### Step 5 – Example Usage  
<details>  
<summary>📂 Code</summary>  


```python
# Standalone test running the news search printing results
if __name__ == "__main__":
    result = real_estate_news_updates()
    print(result.output)
```


</details>  


**Explanation:**  
Runs the tool directly to verify function and output format outside of chatbot context.  


***  


# Slack Chatbot Integration  


### Step 6 – Load Environment Variables for Slack and Initialize Client  
<details>  
<summary>📂 Code</summary>  


```python
from fastapi import FastAPI, Form, Request  # web server framework
from dotenv import load_dotenv  # .env file loader
from slack_sdk import WebClient  # Slack API client
import os
import logging
import asyncio
from fastapi.responses import JSONResponse
import json
from langsmith import traceable
from app.tools.Gnews_tools import real_estate_news_tool

# Load .env environment variables at module start
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Rights-2-Roof Slash Command")

# Load Slack bot token securely from environment variable
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
if not SLACK_BOT_TOKEN:
    logging.error("SLACK_BOT_TOKEN environment variable not set.")
    raise ValueError("SLACK_BOT_TOKEN environment variable not set.")

# Setup logging
logging.basicConfig(level=logging.INFO)
logging.info(f"Loaded SLACK_BOT_TOKEN: {SLACK_BOT_TOKEN[:10]}...")

# Initialize Slack client with loaded token
client = WebClient(token=SLACK_BOT_TOKEN)
```


</details>  


**Explanation:**  
Prepares the FastAPI app, loads the Slack bot token from the environment, logs status, and initializes the Slack client for API calls.  


***  


### Step 7 – Define Async Slack Response Handler  
<details>  
<summary>📂 Code</summary>  


```python
@traceable
async def post_slack_thread(channel_id: str, user_id: str, query_text: str):
    """
    Asynchronous function that queries the news tool and posts results in a Slack thread.
    """
    try:
        logging.info(f"[Rights2Roof Bot] fetching real estate news for {user_id}: {query_text}")

        # Execute the synchronous news tool function in a non-blocking executor
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: real_estate_news_tool.invoke({"query": query_text} if query_text else {})
        )

        # Parse JSON output or fallback to raw output
        try:
            news_data = json.loads(result.output)
            formatted_news = news_data.get("formatted", "No news articles found.")
        except Exception:
            formatted_news = result.output

        # Post initial message to create a Slack thread
        placeholder = await asyncio.to_thread(
            client.chat_postMessage,
            channel=channel_id,
            text=f"<@{user_id}> Fetching real estate news for your query..."
        )
        thread_ts = placeholder["ts"]

        # Post the formatted news message as a threaded reply
        await asyncio.to_thread(
            client.chat_postMessage,
            channel=channel_id,
            thread_ts=thread_ts,
            text=formatted_news
        )

        logging.info(f"[Rights2Roof Bot] posted news for {user_id}")

    except Exception as e:
        logging.exception("[Rights2Roof Bot] Error fetching real estate news")
```


</details>  


**Explanation:**  
Handles the real estate news retrieval and posting asynchronously in Slack, ensuring event loop non-blocking and robust error logging.  


***  


### Step 8 – Implement Slack Slash Command Endpoint  
<details>  
<summary>📂 Code</summary>  


```python
from fastapi import Form

@app.post("/slack/rights-2-roof")
async def slack_roof(
    text: str = Form(...),
    user_id: str = Form(...),
    channel_id: str = Form(...),
):
    """
    Slack slash command handler for /rights-2-roof.
    Acknowledges command immediately, triggers background task to fetch and post news.
    """
    # Immediate ephemeral response to Slack user
    ephemeral_response = {
        "response_type": "ephemeral",
        "text": f"Got it! Running Rights2Roof search for: {text}"
    }

    # Start async task for posting news in thread
    asyncio.create_task(post_slack_thread(channel_id, user_id, text))

    return ephemeral_response
```


</details>  


**Explanation:**  
Receives the slash command payload, confirms receipt, and delegates news fetching to a background async task to keep Slack responsive.  


***  


### Step 9 – Run and Test  
<details>  
<summary>📂 Code</summary>  


```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```


</details>  


**Explanation:**  
Starts the FastAPI app for local testing and Slack integration validation.  