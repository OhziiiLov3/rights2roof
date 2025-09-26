import redis
import os
import json
import numpy as np
import time
import pathlib
import datetime
from dotenv import load_dotenv
from openai import OpenAI
from app.services.redis_helpers import redis_client

load_dotenv()

# REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
# REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
# REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

# redis_kwargs = {
#     "host": REDIS_HOST,
#     "port": REDIS_PORT,
#     "ssl": False,
#     "decode_responses": True,
# }
# if REDIS_PASSWORD:
#     redis_kwargs["password"] = REDIS_PASSWORD

# r = redis.Redis(**redis_kwargs)

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY env var not set")

client = OpenAI(api_key=openai_api_key)


def test_redis_connection():
    try:
        print("Connected to Redis!" if redis_client.ping() else "Redis ping failed")
    except Exception as e:
        print(f"Redis connection error: {e}")


def create_redis_index():
    try:
        redis_client.ft("idx:templates").info()
        print("Index exists")
    except redis.exceptions.ResponseError:
        schema = (
            "ON", "JSON", "PREFIX", "1", "template:",
            "SCHEMA",
            "$.template_name", "AS", "template_name", "TEXT",
            "$.template_text", "AS", "template_text", "TEXT",
            "$.embedding", "AS", "embedding",
            "VECTOR", "FLAT", "6",
            "TYPE", "FLOAT32",
            "DIM", "1536",
            "DISTANCE_METRIC", "COSINE"
        )
        redis_client.execute_command("FT.CREATE", "idx:templates", *schema)
        print("Created index")


def get_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-3-small", input=text)
    return response.data[0].embedding


def to_byte_array(vec):
    return np.array(vec, dtype=np.float32).tobytes()


def add_template(template_name: str, template_text: str):
    embedding = get_embedding(template_text)
    doc = {
        "template_name": template_name,
        "template_text": template_text,
        "embedding": embedding
    }
    redis_client.delete(f"template:{template_name}")
    redis_client.execute_command(
        "JSON.SET", f"template:{template_name}", ".", json.dumps(doc))
    print(f"Template '{template_name}' added.")


def import_templates_from_folder(folder_path: str):
    """
    Import templates from all JSON files in the given folder.
    Each JSON file should contain one template object with "name" and "text".
    """
    count = 0
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            full_path = os.path.join(folder_path, filename)
            with open(full_path, "r", encoding="utf-8") as f:
                tpl = json.load(f)
                add_template(tpl["name"], tpl["text"])
                count += 1
    print(f"Imported {count} templates from folder {folder_path}")


def search_templates(query: str, top_k: int = 3):
    query_vec = to_byte_array(get_embedding(query))
    query_str = f"*=>[KNN {top_k} @embedding $vec AS vector_score]"
    try:
        results = r.execute_command(
            "FT.SEARCH", "idx:templates", query_str,
            "DIALECT", "2", "PARAMS", "2", "vec", query_vec,
            "SORTBY", "vector_score", "ASC",
            "RETURN", "2", "template_name", "template_text",
            "LIMIT", "0", str(top_k)
        )
    except Exception as e:
        print(f"Search error: {e}")
        return []

    matches = []
    for i in range(1, len(results), 2):
        fields = results[i + 1]
        matches.append(dict(zip(fields[::2], fields[1::2])))
    return matches


def fetch_template_from_redis(template_name: str):
    key = f"template:{template_name}"
    raw = redis_client.execute_command("JSON.GET", key)
    if not raw:
        raise ValueError(f"Not found: {template_name}")
    doc = json.loads(raw)
    return doc.get("template_text", "")


def generate_letter(template_name: str, placeholders: dict):
    template = fetch_template_from_redis(template_name)
    try:
        return template.format(**placeholders)
    except KeyError as e:
        raise ValueError(f"Placeholder '{e.args[0]}' missing.")


def save_letter_to_file(letter_text: str, filename: str = None):
    output_dir = "generated_letters"
    pathlib.Path(output_dir).mkdir(exist_ok=True, parents=True)
    if not filename:
        filename = f"letter_{datetime.datetime.now():%Y%m%d_%H%M%S}.txt"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(letter_text)
    return filepath


def generate_template_from_query(user_query: str, template_name: str):
    prompt = f"Write a letter template with placeholders for: {user_query}"
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    template_text = response.choices[0].message.content
    add_template(template_name, template_text)
    return template_text


def find_or_generate_template(query: str, top_k: int = 3):
    results = search_templates(query, top_k=top_k)
    if results:
        return fetch_template_from_redis(results[0]["template_name"])
    name = f"auto_{int(time.time())}"
    return generate_template_from_query(query, name)


if __name__ == "__main__":
    test_redis_connection()
    create_redis_index()
    import_templates_from_folder("templates_tool")

    while True:
        user_query = input("Enter your letter query (or 'exit' to quit): ")
        if user_query.lower() == "exit":
            break

        results = search_templates(user_query, top_k=1)

        if results:
            template_name = results[0]["template_name"]
            print(f"Using template: {template_name}")
        else:
            template_name = f"auto_{int(time.time())}"
            generate_template_from_query(user_query, template_name)
            print(f"Generated new template: {template_name}")

        placeholders = {
            "landlord_name": "John Smith",
            "property_address": "123 Elm St",
            "issue_description": "I believe the increase is too high.",
            "tenant_name": "Jane Doe",
        }

        letter_text = generate_letter(template_name, placeholders)
        print("\nGenerated letter:\n")
        print(letter_text)
        print("\n" + "-"*40 + "\n")