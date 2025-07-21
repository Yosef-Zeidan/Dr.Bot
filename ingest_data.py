# ingest_data.py (New Mechanism)

import os
import sys
import psycopg2
import google.generativeai as genai
from dotenv import load_dotenv

def ingest_data():
    """
    Connects to Supabase, reads rows without embeddings, generates embeddings
    for them using the Google AI API, and updates the rows in the database.
    """
    # --- 1. Load Environment and Configure API ---
    load_dotenv()
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("ERROR: GOOGLE_API_KEY not found in .env file.")
        sys.exit(1)
    genai.configure(api_key=google_api_key)
    
    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")
    try:
        db_port = int(os.getenv("DB_PORT", "5432"))
    except (ValueError, TypeError):
        print("ERROR: DB_PORT in .env is not a valid number.")
        sys.exit(1)

    # --- 2. Fetch Rows That Need an Embedding ---
    print("Connecting to Supabase to find data to index...")
    try:
        conn = psycopg2.connect(
            host=db_host, port=db_port, dbname=db_name, user=db_user, password=db_pass
        )
        cursor = conn.cursor()
        # Only get rows where the embedding is not yet created
        cursor.execute("SELECT id, question_pattern, answer FROM qa_pairs WHERE embedding IS NULL")
        rows_to_update = cursor.fetchall()
        print(f"-> Found {len(rows_to_update)} new/updated rows to process.")
    except Exception as e:
        print(f"ERROR: Could not connect to or fetch from Supabase. Details: {e}")
        sys.exit(1)

    if not rows_to_update:
        print("No new data to ingest. Knowledge base is up to date.")
        return

    # --- 3. Generate Embeddings and Update Database ---
    embedding_model = "models/embedding-001"
    
    for row in rows_to_update:
        row_id, question, answer = row
        # Combine question and answer for a richer embedding
        text_to_embed = f"Question: {question}\nAnswer: {answer}"
        
        print(f"Generating embedding for row ID: {row_id}...")
        try:
            embedding = genai.embed_content(model=embedding_model, content=text_to_embed)
            # Update the specific row with its new embedding
            cursor.execute("UPDATE qa_pairs SET embedding = %s WHERE id = %s", (embedding['embedding'], row_id))
        except Exception as e:
            print(f"ERROR: Could not generate or save embedding for row {row_id}. Details: {e}")
            continue # Move to the next row

    # --- 4. Commit Changes and Close ---
    conn.commit()
    cursor.close()
    conn.close()
    print("\n--- Knowledge ingestion complete! All new data is now searchable. ---")

if __name__ == '__main__':
    ingest_data()