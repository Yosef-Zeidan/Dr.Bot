# app.py

import os
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain.vectorstores import Chroma
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.llms import HuggingFacePipeline
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from dotenv import load_dotenv
from ingest_data import create_vector_store

# Load Environment Variables from .env file
load_dotenv()
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

# Global variable to hold our AI chain so we can reload it
qa_chain = None

def initialize_ai_system():
    """
    Loads all AI components and creates the final RAG chain.
    This function is called on startup and after a re-index.
    """
    global qa_chain
    print("Initializing AI system... This may take several minutes.")

    embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_db = Chroma(persist_directory="./chroma_db", embedding_function=embedding_function)

    model_id = 'google/flan-t5-base'
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_id)
    pipe = pipeline("text2text-generation", model=model, tokenizer=tokenizer, max_length=512)
    llm = HuggingFacePipeline(pipeline=pipe)

    prompt_template = """
    Use the following pieces of context to answer the question at the end.
    If you don't know the answer from the context, just say that you don't know.

    Context: {context}
    Question: {question}
    Helpful Answer:"""
    PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_db.as_retriever(),
        chain_type_kwargs={"prompt": PROMPT}
    )
    print("AI System is ready and operational.")

# --- Flask App Setup ---
app = Flask(__name__)
CORS(app)

# --- API Endpoint for the Front-End Chat ---
@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not qa_chain:
        return jsonify({"error": "AI system is still initializing. Please try again in a moment."}), 503
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    try:
        result = qa_chain({"query": user_message})
        return jsonify({"response": result['result']})
    except Exception as e:
        return jsonify({"error": f"Error during AI processing: {e}"}), 500

# --- API Endpoint for the Supabase Webhook ---
@app.route('/webhook-reindex', methods=['POST'])
def webhook_reindex():
    auth_header = request.headers.get('Authorization')
    if not auth_header or auth_header != f"Bearer {WEBHOOK_SECRET}":
        return jsonify({"error": "Unauthorized"}), 401
    
    def run_indexing_task():
        print("Webhook received. Starting background re-indexing...")
        create_vector_store()
        print("Re-indexing complete. Reloading the AI system with new knowledge...")
        initialize_ai_system()

    thread = threading.Thread(target=run_indexing_task)
    thread.start()
    return jsonify({"message": "Re-indexing process initiated."}), 202

# --- Main Execution Block ---
if __name__ == '__main__':
    if not os.path.exists("./chroma_db"):
        print("Local vector store not found. Running initial data ingestion...")
        create_vector_store()
    
    initialize_ai_system()
    app.run(port=5000, debug=False)