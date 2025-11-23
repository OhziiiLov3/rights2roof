# # test_pipeline_query.py
# import pprint
# from app.pipelines.pipeline_query import pipeline_query

# def main():
#     user_query = "Find affordable housing in SF"
#     user_id = "test_user"

#     print(f"Running pipeline for user_id={user_id} and query='{user_query}'\n")

#     # Run the pipeline
#     executor_response = pipeline_query(user_query=user_query, user_id=user_id)

#     print("\n=== Executor Response ===")
#     print(executor_response)

#     # If you want to see the full cached result
#     from app.services.redis_helpers import get_cached_result
#     cache_key = f"user:{user_id}:query:{user_query}"
#     cached = get_cached_result(cache_key)

#     if cached:
#         cached_data = cached
#         print("\n=== Full Cached Pipeline Output ===")
#         pprint.pprint(cached_data)

# if __name__ == "__main__":
#     main()
# test_pipeline_multiturn.py
import pprint
from app.pipelines.pipeline_query import pipeline_query
from app.services.redis_helpers import get_cached_result, cache_result

def run_multiturn_test():
    user_id = "test_user"
    queries = [
        "Find affordable housing in SF",
        "What is the eligibility criteria for these housing programs?",
        "Are there any available units in Mission District right now?"
    ]

    for turn, query in enumerate(queries, start=1):
        print(f"\n--- Turn {turn} ---")
        print(f"User query: {query}")

        # Run pipeline
        response = pipeline_query(user_query=query, user_id=user_id)
        print("\nExecutor Response:")
        print(response)

        # Show cached state for this user/query
        cache_key = f"user:{user_id}:query:{query}"
        cached = get_cached_result(cache_key)
        if cached:
            print("\nCached full pipeline output:")
            pprint.pprint(cached)

if __name__ == "__main__":
    run_multiturn_test()
