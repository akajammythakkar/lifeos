from pathlib import Path
from datetime import datetime, timezone
import json
from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
import asyncio
import os

async def ingest_products_data(client: Graphiti, json_path: str | Path):
    """
    Ingests product data from a JSON file into the Graphiti graph.

    Args:
        client (Graphiti): The initialized Graphiti client.
        json_path (str | Path): Path to the JSON file containing product data.

    Raises:
        FileNotFoundError: If the JSON file is not found.
        ValueError: If 'products' key is missing in the JSON file.
    """
    json_path = Path(json_path)
    if not json_path.exists():
        raise FileNotFoundError(f"File not found: {json_path}")

    with open(json_path) as file:
        data = json.load(file)

    products = data.get('products')
    if not products:
        raise ValueError("JSON does not contain 'products' key or it's empty.")

    for i, product in enumerate(products):
        await client.add_episode(
            name=product.get('title', f'Product {i}'),
            episode_body=str({k: v for k, v in product.items() if k != 'images'}),
            source_description='ManyBirds products',
            source=EpisodeType.json,
            reference_time=datetime.now(timezone.utc),
        )

if __name__ == '__main__':
    neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
    neo4j_password = os.environ.get('NEO4J_PASSWORD', 'password')

    client = Graphiti(neo4j_uri, neo4j_user, neo4j_password)
    asyncio.run(ingest_products_data(client, './data/manybirds_products.json'))