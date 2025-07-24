# app.py (New Mechanism)

import os
import sys
import psycopg2
import google.generativeai as genai
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- 1. Load Environment and Configure API ---
load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key:
    print("FATAL: GOOGLE_API_KEY not found in .env file. The application cannot start.")
    sys.exit(1)
genai.configure(api_key=google_api_key)

db_host = os.getenv("DB_HOST")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_pass = os.getenv("DB_PASS")
db_port = int(os.getenv("DB_PORT", "5432"))

# --- 2. Global Models ---
# These models are lightweight and just represent the API endpoints
embedding_model = "models/embedding-001"
generative_model = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. Flask App Setup ---
app = Flask(__name__)
CORS(app)
# --- NEW: Add a simple root endpoint to confirm the server is running ---
@app.route('/')
def index():
    return "<h1>AI Backend Server</h1><p>The server is running. Please use the front-end application to chat.</p>"

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    try:
        # --- RAG Step 1: Create an embedding for the user's query ---
        query_embedding = genai.embed_content(model=embedding_model, content=user_message)['embedding']

        # --- RAG Step 2: Find relevant documents in the database ---
        conn = psycopg2.connect(
            host=db_host, port=db_port, dbname=db_name, user=db_user, password=db_pass
        )
        cursor = conn.cursor()
        
        # Use the "<=>" cosine distance operator from pgvector to find the 3 most similar documents
        cursor.execute(
            "SELECT answer FROM qa_pairs ORDER BY embedding <=> %s::vector LIMIT 3",
            (str(query_embedding),)
        )
        relevant_docs = cursor.fetchall()
        cursor.close()
        conn.close()

        # Format the retrieved documents into a single context string
        context = "\n".join([doc[0] for doc in relevant_docs])

        # --- RAG Step 3: Generate a response using the context ---
        prompt = f"""
        Based ONLY on the following context, answer the user's question.
        If the context doesn't contain the answer, say that you don't have enough information to answer.
        
        Context:
        {context}
        
        User's Question:
        {user_message}
        
        Answer:
        """
        
        response = generative_model.generate_content(prompt)
        
        print(f"User Query: {user_message}\nAI Response: {response.text}")
        return jsonify({"response": response.text})

    except Exception as e:
        print(f"ERROR during chat processing: {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

# The webhook logic remains the same concept, but is now much faster.
@app.route('/webhook-reindex', methods=['POST'])
def webhook_reindex():
    # ... (You can add the webhook security logic here as before) ...
    # Now, it just calls the new, faster ingest_data script
    os.system('python ingest_data.py')
    return jsonify({"message": "Re-indexing process initiated."}), 202

if __name__ == '__main__':
    print("Backend server starting...")
    app.run(port=5000, debug=True, host='0.0.0.0')
