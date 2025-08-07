# Dell Graphiti Core Example - Quick Setup

## Setup Instructions

1. Create and activate a virtual environment:
   ```
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with the following variables:
   ```
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password
   OPENAI_API_KEY=your_openai_api_key
   ```

## Running the Application

1. Make sure your Neo4j database is running

2. Initialize the database and add Dell product data:
   ```
   python dell_integrated_app.py
   ```

3. Run the Dell chatbot:
   ```
   python agent/tools_and_llm_2.py
   ```
