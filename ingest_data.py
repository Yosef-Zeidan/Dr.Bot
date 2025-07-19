# ingest_data.py

import os
import psycopg2
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import SentenceTransformerEmbeddings

# Load your Supabase credentials from the .env file
load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

def create_vector_store():
    """
    Connects to Supabase, fetches the Q&A data, converts it into
    vector embeddings, and saves it to a local ChromaDB store.
    """
    print("Connecting to the Supabase database to fetch knowledge...")
    try:
        conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
        cursor = conn.cursor()
        cursor.execute("SELECT question_pattern, answer FROM qa_pairs")
        qa_data = cursor.fetchall()
        conn.close()
        print(f"Successfully fetched {len(qa_data)} Q&A pairs.")

    except Exception as e:
        print(f"ERROR: Could not connect to database. Check your .env file. Details: {e}")
        return

    documents = [f"Question: {q}\nAnswer: {a}" for q, a in qa_data]
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.create_documents(documents)
    embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

    print("Creating the local vector store. This might take a moment...")
    db = Chroma.from_documents(
        texts, 
        embedding_function, 
        persist_directory="./chroma_db"
    )
    
    print("---------------------------------")
    print("Vector store has been created successfully in the 'chroma_db' folder.")
    print("The chatbot's knowledge is now indexed.")
    print("---------------------------------")

if __name__ == '__main__':
    create_vector_store()