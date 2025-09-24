Following your provided template style, here is a README update snippet for your `templates_tool.py` vector template search project:

***

# Vector Template Search with Redis and OpenAI  
### Documentation by Prosperity  

***  
## Table of Contents  
- [Project Overview](#project-overview)  
- [Step 1 – Import Packages and Load Environment Variables](#step-1--import-packages-and-load-environment-variables)  
- [Step 2 – Initialize Redis and OpenAI Clients](#step-2--initialize-redis-and-openai-clients)  
- [Step 3 – Redis Connection Test](#step-3--redis-connection-test)  
- [Step 4 – Create Redis Search Index for Templates](#step-4--create-redis-search-index-for-templates)  
- [Step 5 – Embedding Generation Function](#step-5--embedding-generation-function)  
- [Step 6 – Add Template to Redis](#step-6--add-template-to-redis)  
- [Step 7 – Search Templates via Vector Similarity](#step-7--search-templates-via-vector-similarity)  
- [Step 8 – Fetch and Generate Letters](#step-8--fetch-and-generate-letters)  
- [Step 9 – Save Generated Letters Locally](#step-9--save-generated-letters-locally)  
- [Usage Example](#usage-example)  

***  

# Project Overview  
This project enables efficient semantic search over letter templates stored in Redis using OpenAI-generated embeddings and RediSearch vector similarity search. It supports generating personalized letters by filling placeholders in matched templates.

---  

### Step 1 – Import Packages and Load Environment Variables  
<details>  
<summary>📂 Code</summary>  

```python
import redis
import os
import json
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
```

</details>  

**Explanation:**  
Loads required libraries and environment variables for secure configuration access.  

---  

### Step 2 – Initialize Redis and OpenAI Clients  
<details>  
<summary>📂 Code</summary>  

```python
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

r = redis.Redis(**redis_kwargs)

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")
client = OpenAI(api_key=openai_api_key)
```

</details>  

**Explanation:**  
Sets up Redis and OpenAI clients for interaction with vector storage and embedding APIs.  

***

### Step 3 – Redis Connection Test  
<details>  
<summary>📂 Code</summary>  

```python
def test_redis_connection():
    try:
        if r.ping():
            print("Successfully connected to Redis!")
        else:
            print("Ping to Redis failed.")
    except Exception as e:
        print(f"Redis connection error: {e}")
```

</details>  

**Explanation:**  
Verifies connectivity to Redis server before proceeding.  

***

### Step 4 – Create Redis Search Index for Templates  
<details>  
<summary>📂 Code</summary>  

```python
def create_redis_index():
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
```

</details>  

**Explanation:**  
Creates the necessary RediSearch vector index for templates if missing.  

***

### Step 5 – Embedding Generation Function  
<details>  
<summary>📂 Code</summary>  

```python
def get_embedding(text: str) -> list[float]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding
```

</details>  

**Explanation:**  
Generates semantic vector embeddings for texts from OpenAI.  

***

### Step 6 – Add Template to Redis  
<details>  
<summary>📂 Code</summary>  

```python
def add_template(template_name: str, template_text: str):
    embedding_vector = get_embedding(template_text)
    doc = {
        "template_name": template_name,
        "template_text": template_text,
        "embedding": embedding_vector
    }
    r.delete(f"template:{template_name}")
    r.execute_command("JSON.SET", f"template:{template_name}", ".", json.dumps(doc))
    print(f"Template '{template_name}' added to Redis.")
```

</details>  

**Explanation:**  
Adds or updates a template in Redis with its OpenAI embedding, removing any prior copy first.  

***

### Step 7 – Search Templates via Vector Similarity  
<details>  
<summary>📂 Code</summary>  

```python
def to_byte_array(vec: list[float]) -> bytes:
    return np.array(vec, dtype=np.float32).tobytes()

def search_templates(query: str, top_k: int = 3) -> list[dict]:
    query_vec = to_byte_array(get_embedding(query))
    query_string = f"*=>[KNN {top_k} @embedding $vec AS vector_score]"

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

    matches = []
    for i in range(1, len(results), 2):
        fields = results[i + 1]
        matches.append(dict(zip(fields[::2], fields[1::2])))

    return matches
```

</details>  

**Explanation:**  
Searches for top-k templates most semantically similar to the query vector.  

---  

### Step 8 – Fetch and Generate Letters  
<details>  
<summary>📂 Code</summary>  

```python
def fetch_template_from_redis(template_name: str) -> str:
    key = f"template:{template_name}"
    template_json = r.execute_command("JSON.GET", key)
    if not template_json:
        raise ValueError(f"Template '{template_name}' not found in Redis.")
    return json.loads(template_json).get("template_text", "")

def generate_letter(template_name: str, placeholders: dict) -> str:
    template_str = fetch_template_from_redis(template_name)
    try:
        return template_str.format(**placeholders)
    except KeyError as e:
        raise ValueError(f"Missing placeholder for '{e.args[0]}' in letter generation.")
```

</details>  

**Explanation:**  
Fetches template text from Redis and formats it by replacing placeholders with actual data.  

***

### Step 9 – Save Generated Letters Locally  
<details>  
<summary>📂 Code</summary>  

```python
def save_letter_to_file(letter_text: str, filename: str = None) -> str:
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
```

</details>  

**Explanation:**  
Saves personalized letter output to a local timestamped text file for record or sharing.  

***

# Usage Example  
<details>  
<summary>📂 Code</summary>  

```python
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
    matches = search_templates(query)
    print(matches)

    if matches:
        letter = generate_letter(
            matches[0]["template_name"],
            {
                "landlord_name": "John Smith",
                "property_address": "123 Elm St",
                "issue_description": query,
                "tenant_name": "Jane Doe",
            },
        )
        print("\nGenerated Letter:\n", letter)
        save_letter_to_file(letter)
```

</details>  

**Explanation:**  
Runs connection checks, setups, adds example data, and performs search and letter generation to validate workflow.