# Domain-Aware Chatbot Project

This project demonstrates a domain-adaptive chatbot framework with dynamic context retrieval and domain-specific configuration, using a Neo4j database and LLMs.

## Prerequisites
- Python 3.8+
- Neo4j database (local or remote)
- Required Python packages (see below)
- Environment variables for Neo4j connection:
  - `NEO4J_URI` (e.g., `bolt://localhost:7687`)
  - `NEO4J_USER` (e.g., `neo4j`)http://claude.ai/
  - `NEO4J_PASSWORD` (your password)

## Setup
1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   Or manually install the required packages:
   ```bash
   pip install graphiti_core langchain_openai langgraph ipywidgets python-dotenv nest_asyncio
   ```

2. **Configure environment variables:**
   - Create a `.env` file in the project root with the following content:
     ```env
     NEO4J_URI=bolt://localhost:7687
     NEO4J_USER=neo4j
     NEO4J_PASSWORD=your_password
     ```

## Usage

### 1. Ingest Data
Before using the chatbot, you must ingest data into the Neo4j database.

- Run the following script to ingest data:
  ```bash
  python ingest_func.py
  ```
  This script should populate your Neo4j database with the necessary nodes and relationships for the chatbot to function.

### 2. Interact with the Agent
- Open the Jupyter notebook:
  ```bash
  jupyter notebook context_agent.ipynb
  ```
- Follow the instructions in the notebook to interact with the domain-aware chatbot and check the responses.

## Notes
- Ensure your Neo4j database is running and accessible before running the scripts.
- You can modify the domain configurations and prompts in the code to suit your use case.

## Files
- `ingest_func.py`: Script to ingest data into the Neo4j database.
- `context_agent.ipynb`: Jupyter notebook to interact with the chatbot agent.
---
Feel free to reach out if you encounter any issues or need further customization!