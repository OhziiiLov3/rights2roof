import redis
import os
import json
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
import time


# Load environment variables from .env file for configuration
load_dotenv()


# Redis configuration from environment variables, with sane defaults
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")


redis_kwargs = {
    "host": REDIS_HOST,
    "port": REDIS_PORT,
    "ssl": False,
    "decode_responses": True,
}
if REDIS_PASSWORD:
    redis_kwargs["password"] = REDIS_PASSWORD


# Initialize Redis client
r = redis.Redis(**redis_kwargs)


# Obtain OpenAI API key from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")


# Initialize OpenAI client
client = OpenAI(api_key=openai_api_key)


def test_redis_connection() -> None:
    """
    Test connectivity to Redis server.
    """
    try:
        if r.ping():
            print("Successfully connected to Redis!")
        else:
            print("Ping to Redis failed.")
    except Exception as e:
        print(f"Redis connection error: {e}")


def create_redis_index() -> None:
    """
    Create RediSearch index with vector field if it does not exist.
    """
    try:
        r.ft("idx:templates").info()
        print("RediSearch index 'idx:templates' already exists.")
    except redis.exceptions.ResponseError:
        schema = (
            "ON", "JSON",
            "PREFIX", "1", "template:",
            "SCHEMA",
            "$.template_name", "AS", "template_name", "TEXT",
            "$.template_text", "AS", "template_text", "TEXT",
            "$.embedding", "AS", "embedding",
            "VECTOR", "FLAT", "6",
            "TYPE", "FLOAT32",
            "DIM", "1536",
            "DISTANCE_METRIC", "COSINE"
        )
        r.execute_command("FT.CREATE", "idx:templates", *schema)
        print("Created RediSearch index 'idx:templates'.")


def get_embedding(text: str) -> list[float]:
    """
    Generate embedding vector for text using OpenAI embeddings API.

    Args:
        text: Input string to embed.

    Returns:
        List of floats representing the embedding vector.
    """
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def to_byte_array(vec: list[float]) -> bytes:
    """
    Convert list of floats to float32 byte array for Redis vector search.

    Args:
        vec: List of float values.

    Returns:
        Byte array of float32 values.
    """
    return np.array(vec, dtype=np.float32).tobytes()


def add_template(template_name: str, template_text: str) -> None:
    """
    Add or update a template in Redis JSON with its OpenAI embedding.

    Args:
        template_name: Unique name for the template.
        template_text: Template text with placeholders.
    """
    embedding_vector = get_embedding(template_text)
    doc = {
        "template_name": template_name,
        "template_text": template_text,
        "embedding": embedding_vector
    }

    # Remove existing key if any to avoid conflicts
    r.delete(f"template:{template_name}")
    r.execute_command(
        "JSON.SET", f"template:{template_name}", ".", json.dumps(doc))
    print(f"Template '{template_name}' added to Redis.")


def search_templates(query: str, top_k: int = 3) -> list[dict]:
    """
    Vector search templates stored in Redis using embedding similarity.

    Args:
        query: Search query string.
        top_k: Number of top matches to return.

    Returns:
        List of dictionaries each containing 'template_name' and 'template_text'.
    """
    query_vec = to_byte_array(get_embedding(query))
    query_string = f"*=>[KNN {top_k} @embedding $vec AS vector_score]"

    try:
        results = r.execute_command(
            "FT.SEARCH",
            "idx:templates",
            query_string,
            "DIALECT", "2",
            "PARAMS", "2", "vec", query_vec,
            "SORTBY", "vector_score",
            "ASC",
            "RETURN", "2", "template_name", "template_text",
            "LIMIT", "0", str(top_k)
        )
    except redis.ResponseError as e:
        print(f"Redis search error: {e}")
        return []

    matches = []
    for i in range(1, len(results), 2):
        fields = results[i + 1]
        matches.append(dict(zip(fields[::2], fields[1::2])))

    return matches


def fetch_template_from_redis(template_name: str) -> str:
    """
    Retrieve raw template text from Redis JSON by template name.

    Args:
        template_name: The template's unique name.

    Returns:
        Template text string.
    """
    key = f"template:{template_name}"
    template_json = r.execute_command("JSON.GET", key)
    if not template_json:
        raise ValueError(f"Template '{template_name}' not found in Redis.")
    template_data = json.loads(template_json)
    return template_data.get("template_text", "")


def generate_letter(template_name: str, placeholders: dict) -> str:
    """
    Format the template by replacing placeholders with actual values.

    Args:
        template_name: Template name to fetch.
        placeholders: Dictionary of placeholder names and their values.

    Returns:
        Formatted string with placeholders filled.
    """
    template_str = fetch_template_from_redis(template_name)
    try:
        return template_str.format(**placeholders)
    except KeyError as e:
        raise ValueError(
            f"Missing placeholder for '{e.args[0]}' in letter generation."
        )


def save_letter_to_file(letter_text: str, filename: str = None) -> str:
    """
    Save a generated letter to a file in 'generated_letters' folder.

    Args:
        letter_text: Text content of the letter.
        filename: Optional filename, autogenerated if omitted.

    Returns:
        Path to saved file.
    """
    import datetime
    import pathlib

    output_dir = "generated_letters"
    pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)
    if not filename:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"letter_{timestamp}.txt"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(letter_text)
    return filepath


def generate_template_from_query(user_query: str, template_name: str) -> str:
    """
    Generate a letter template from user query using OpenAI chat completion,
    then add it to Redis.
    """
    prompt = f"Write a letter template with placeholders for the following topic:\n{user_query}"

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    template_text = response.choices[0].message.content

    add_template(template_name, template_text)
    print(f"Generated and saved new template: {template_name}")
    return template_text


def find_or_generate_template(query: str, top_k: int = 3) -> str:
    """
    Search for existing templates matching query.
    If none found, generate a new one from the query and store it.
    Returns the text of the matched or generated template.
    """
    results = search_templates(query, top_k=top_k)
    if results:
        # Return the top matched template text
        template_name = results[0]["template_name"]
        return fetch_template_from_redis(template_name)

    # No match found: generate a new template
    timestamp = int(time.time())
    generated_template_name = f"auto_gen_{timestamp}"
    return generate_template_from_query(query, generated_template_name)


if __name__ == "__main__":
    test_redis_connection()
    create_redis_index()

    add_template(
        "dispute_rent_increase",
        """Dear {landlord_name},

I am writing to dispute the 20% rent increase at {property_address}.

{issue_description}

Please consider this notice as per tenant rights.

Thank you,
{tenant_name}
"""
    )

    query = "I want a letter to dispute my landlord's rent increase."
    template_text = find_or_generate_template(query)
    print("Retrieved or Generated Template:\n", template_text)
