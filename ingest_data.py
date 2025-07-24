# ingest_data.py (Definitive Version - Corrected and Enhanced)

import os
import sys
import firebase_admin
import google.generativeai as genai
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

def ingest_data():
    """
    Connects to Firestore, finds all documents in the 'qa_pairs' collection,
    checks if they have an embedding, generates one if missing, and updates the document.
    This is the most reliable method.
    """
    # --- 1. Initialize Firebase & Google AI (with safety check) ---
    try:
        load_dotenv()
        
        # Check if the app is already initialized to prevent errors
        if not firebase_admin._apps:
            cred = credentials.Certificate("firebase-key.json")
            firebase_admin.initialize_app(cred)
            print("Firebase app initialized.")
        
        db = firestore.client()

        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY not found in .env file.")
        genai.configure(api_key=google_api_key)
        print("Successfully connected to Firebase and configured Google AI.")
    except Exception as e:
        print(f"FATAL: Initialization failed. Details: {e}")
        sys.exit(1)

    # --- 2. Fetch ALL Documents and Identify Those to Process ---
    try:
        print("Fetching all documents from 'qa_pairs' collection to check their status...")
        qa_ref = db.collection('qa_pairs')
        all_docs = qa_ref.stream()
        
        docs_to_process = []
        total_docs = 0
        for doc in all_docs:
            total_docs += 1
            data = doc.to_dict()
            # This is the corrected logic: check if the 'embedding' key is missing.
            if 'embedding' not in data:
                docs_to_process.append(doc)
        
        print(f"-> Found {total_docs} total documents.")
        print(f"-> Found {len(docs_to_process)} documents that need an embedding created.")

    except Exception as e:
        print(f"FATAL: Could not fetch documents from Firestore. Details: {e}")
        sys.exit(1)

    if not docs_to_process:
        print("Knowledge base is already up to date. No new embeddings needed.")
        return

    # --- 3. Generate Embeddings and Update Firestore ---
    embedding_model = "models/embedding-001" 
    
    # We use a batch to update Firestore, which is more efficient.
    batch = db.batch()
    
    for doc in docs_to_process:
        doc_id = doc.id
        data = doc.to_dict()
        # Ensure that question_pattern and answer exist before creating the text
        question = data.get('question_pattern', '')
        answer = data.get('answer', '')
        text_to_embed = f"Question: {question}\nAnswer: {answer}"
        
        if not text_to_embed.strip():
            print(f"WARNING: Skipping document {doc_id} because it has no text content.")
            continue
            
        print(f"Generating embedding for document ID: {doc_id}...")
        try:
            embedding_result = genai.embed_content(model=embedding_model, content=text_to_embed)
            
            # Get a reference to the document and add the update to the batch
            doc_ref = qa_ref.document(doc_id)
            batch.update(doc_ref, {'embedding': embedding_result['embedding']})
            
        except Exception as e:
            print(f"ERROR: Could not process document {doc_id}. The API call might have failed. Details: {e}")
            continue

    # --- 4. Commit all the updates at once ---
    try:
        print("\nCommitting all updates to Firestore...")
        batch.commit()
        print("-> Batch commit successful!")
    except Exception as e:
        print(f"FATAL: Failed to commit updates to Firestore. Details: {e}")

    print("\n--- Knowledge ingestion complete! ---")

if __name__ == '__main__':
    ingest_data()
