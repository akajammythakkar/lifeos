from neo4j import GraphDatabase
from typing import List, Dict, Any
import os
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

class Neo4jHandler:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.driver = None
        self.create_schema()

    def create_schema(self):
        """Create schema constraints and indexes"""
        if not self.driver:
            self.connect()

        with self.driver.session() as session:
            # Create constraints (only unique constraints as they're supported in Community Edition)
            constraints = [
                # Transcript constraints
                "CREATE CONSTRAINT transcript_id IF NOT EXISTS ON (t:Transcript) ASSERT t.id IS UNIQUE",
                
                # ActionItem constraints
                "CREATE CONSTRAINT action_item_id IF NOT EXISTS ON (a:ActionItem) ASSERT a.id IS UNIQUE"
            ]

            # Create indexes
            indexes = [
                # Transcript indexes
                "CREATE INDEX transcript_created_at_idx IF NOT EXISTS FOR (t:Transcript) ON (t.created_at)",
                "CREATE INDEX transcript_updated_at_idx IF NOT EXISTS FOR (t:Transcript) ON (t.updated_at)",
                
                # ActionItem indexes
                "CREATE INDEX action_item_created_at_idx IF NOT EXISTS FOR (a:ActionItem) ON (a.created_at)",
                "CREATE INDEX action_item_updated_at_idx IF NOT EXISTS FOR (a:ActionItem) ON (a.updated_at)",
                "CREATE INDEX action_item_status_idx IF NOT EXISTS FOR (a:ActionItem) ON (a.status)"
            ]

            try:
                # Create constraints
                for constraint in constraints:
                    try:
                        session.run(constraint)
                    except Exception as e:
                        print(f"Failed to create constraint: {str(e)}")
                
                # Create indexes
                for index in indexes:
                    try:
                        session.run(index)
                    except Exception as e:
                        print(f"Failed to create index: {str(e)}")
                
                return True
            except Exception as e:
                print(f"Failed to create schema: {str(e)}")
                return False

    def connect(self):
        """Establish connection to Neo4j database"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            return True
        except Exception as e:
            print(f"Failed to connect to Neo4j: {str(e)}")
            return False

    def close(self):
        """Close the Neo4j connection"""
        if self.driver:
            self.driver.close()

    def delete_all_data(self):
        """Delete all nodes and relationships from the database"""
        if not self.driver:
            self.connect()

        with self.driver.session() as session:
            query = """
            MATCH (n)
            DETACH DELETE n
            """
            try:
                session.run(query)
                return True
            except Exception as e:
                print(f"Failed to delete data: {str(e)}")
                return False

    def create_transcript_node(self, transcript_id: str, content: str, metadata: Dict[str, Any] = None):
        """Create a transcript node in Neo4j"""
        if not self.driver:
            self.connect()

        # Add timestamp to metadata
        if metadata is None:
            metadata = {}
        created_at = datetime.now().isoformat()
        metadata["created_at"] = created_at
        metadata["updated_at"] = created_at

        # Serialize metadata to JSON string
        metadata_str = json.dumps(metadata) if metadata else "{}"

        with self.driver.session() as session:
            query = """
            CREATE (t:Transcript {
                id: $transcript_id,
                content: $content,
                metadata: $metadata,
                created_at: datetime($created_at),
                updated_at: datetime($updated_at)
            })
            RETURN t
            """
            result = session.run(query, {
                "transcript_id": transcript_id,
                "content": content,
                "metadata": metadata_str,
                "created_at": created_at,
                "updated_at": created_at
            })
            return result.single()

    def create_action_item(self, transcript_id: str, action_item: Dict[str, Any]):
        """Create an action item node and connect it to its transcript"""
        if not self.driver:
            self.connect()

        # Add timestamps
        created_at = datetime.now().isoformat()
        action_item["created_at"] = created_at
        action_item["updated_at"] = created_at

        with self.driver.session() as session:
            query = """
            MATCH (t:Transcript {id: $transcript_id})
            CREATE (a:ActionItem {
                id: $action_id,
                description: $description,
                status: $status,
                priority: $priority,
                created_at: datetime($created_at),
                updated_at: datetime($updated_at)
            })
            CREATE (t)-[:HAS_ACTION_ITEM]->(a)
            RETURN a
            """
            result = session.run(query, {
                "transcript_id": transcript_id,
                "action_id": action_item.get("id"),
                "description": action_item.get("description"),
                "status": action_item.get("status", "pending"),
                "priority": action_item.get("priority", "medium"),
                "created_at": created_at,
                "updated_at": created_at
            })
            return result.single()

    def search_similar_transcripts(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar transcripts using full-text search"""
        if not self.driver:
            self.connect()

        with self.driver.session() as session:
            query = """
            CALL db.index.fulltext.queryNodes("transcriptContent", $query)
            YIELD node, score
            RETURN 
                node.content as content, 
                node.metadata as metadata, 
                datetime(node.created_at) as created_at,
                datetime(node.updated_at) as updated_at,
                score
            ORDER BY score DESC
            LIMIT $limit
            """
            result = session.run(query, {"query": query, "limit": limit})
            records = [dict(record) for record in result]
            
            # Process each record
            for record in records:
                # Parse metadata JSON strings back to dictionaries
                if record.get("metadata"):
                    try:
                        record["metadata"] = json.loads(record["metadata"])
                    except json.JSONDecodeError:
                        record["metadata"] = {}
                
                # Convert Neo4j DateTime objects to ISO format strings
                if record.get("created_at"):
                    record["created_at"] = record["created_at"].isoformat()
                if record.get("updated_at"):
                    record["updated_at"] = record["updated_at"].isoformat()
            
            return records

    def create_fulltext_index(self):
        """Create a full-text index for transcript content if it doesn't exist"""
        if not self.driver:
            self.connect()

        with self.driver.session() as session:
            # First check if the index exists
            check_query = """
            CALL db.indexes()
            YIELD name, type, labelsOrTypes, properties
            WHERE name = 'transcriptContent'
            RETURN count(*) as count
            """
            result = session.run(check_query)
            count = result.single()["count"]

            if count == 0:
                # Create the index only if it doesn't exist
                create_query = """
                CALL db.index.fulltext.createNodeIndex(
                    "transcriptContent",
                    ["Transcript"],
                    ["content"]
                )
                """
                try:
                    session.run(create_query)
                    return True
                except Exception as e:
                    print(f"Failed to create index: {str(e)}")
                    return False
            else:
                print("Index 'transcriptContent' already exists")
                return True 