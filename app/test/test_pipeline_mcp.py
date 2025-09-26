from fastmcp import Client
import asyncio
# from app.pipelines.pipeline_query import pipeline_query

async def test_pipeline_tool():
    async with Client("http://127.0.0.1:5200/mcp") as mcp_client:
        result = await mcp_client.call_tool(
            "pipeline_tool",
            {"query": "Find landlords with open apartments in Oakland", "user_id": "user123"}
        )
        print(result)  # {'result': '<executor final answer>'}

asyncio.run(test_pipeline_tool())
