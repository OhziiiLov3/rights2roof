# entrypoint.py at root
import asyncio
import uvicorn
from app.server.mcp_server import rights2roof_server  # replace with actual server object

async def main():
    await asyncio.gather(
        asyncio.to_thread(rights2roof_server.run, "http", "0.0.0.0", 5300, "/mcp"),
        uvicorn.run("app.tools.vector_store_tool:app", host="0.0.0.0", port=5400)
    )

# entrypoint.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.services.slack_webhook:app", host="0.0.0.0", port=8000)
