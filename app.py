# app.py (Final "Loud Debugging" Version)

import os
import sys
import firebase_admin
import google.generativeai as genai
from firebase_admin import credentials, firestore
import numpy as np
from numpy.linalg import norm
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- Global variables ---
generative_model = None
knowledge_base = []
is_system_healthy = False

def manual_cosine_similarity(vec_a, vec_b):
    """Calculates cosine similarity between two vectors using only numpy."""
    vec_a = np.array(vec_a, dtype=np.float32)
    vec_b = np.array(vec_b, dtype=np.float32)
    
    if vec_a.shape != vec_b.shape:
        # This is a critical new check
        print(f"--- SHAPE MISMATCH ERROR ---")
        print(f"Vector A shape: {vec_a.shape}")
        print(f"Vector B shape: {vec_b.shape}")
        print(f"----------------------------")
        # Return a similarity of 0 if shapes don't match
        return 0

    dot_product = np.dot(vec_a, vec_b)
    norm_a = norm(vec_a)
    norm_b = norm(vec_b)
    similarity = dot_product / ((norm_a * norm_b) + 1e-9)
    return similarity

def initialize_system():
    global generative_model, knowledge_base, is_system_healthy
    print("--- Starting AI System Initialization ---")
    try:
        load_dotenv()
        cred = credentials.Certificate("firebase-key.json")
        firebase_admin.initialize_app(cred)
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key: raise ValueError("GOOGLE_API_KEY not found")
        genai.configure(api_key=google_api_key)
        generative_model = genai.GenerativeModel('gemini-1.5-flash')
        print("-> APIs Initialized Successfully.")
    except Exception as e:
        print(f"FATAL: API Initialization failed. Details: {e}")
        return
    try:
        load_knowledge_base()
    except Exception as e:
        print(f"FATAL: Could not load knowledge base. Details: {e}")
        return
    is_system_healthy = True
    print("\n--- AI System is Ready and Operational ---")

def load_knowledge_base():
    global knowledge_base
    print("Loading knowledge base from Firestore...")
    db = firestore.client()
    docs = db.collection('qa_pairs').stream()
    temp_kb = []
    for doc in docs:
        data = doc.to_dict()
        if 'embedding' in data and 'answer' in data:
            temp_kb.append({
                'id': doc.id,
                'answer': data['answer'],
                'embedding': np.array(data['embedding'], dtype=np.float32) # Enforce type on load
            })
    knowledge_base = temp_kb
    print(f"-> Knowledge base loaded successfully with {len(knowledge_base)} documents.")

app = Flask(__name__)
CORS(app)

@app.route('/chat', methods=['POST'])
def chat():
    if not is_system_healthy:
        return jsonify({"error": "AI system not ready."}), 503

    user_message = request.json.get('message')
    if not user_message: return jsonify({"error": "No message"}), 400

    print("\n--- NEW CHAT REQUEST ---")
    print(f"User Message: '{user_message}'")

    try:
        # Step 1: Get user query embedding
        print("[Debug] Step 1: Generating embedding for user query...")
        embedding_model = "models/embedding-001"
        query_embedding_result = genai.embed_content(model=embedding_model, content=user_message)
        query_embedding = query_embedding_result['embedding']
        print(f"[Debug] -> Query embedding received. Type: {type(query_embedding)}, Length: {len(query_embedding)}")

        # Step 2: Perform similarity search
        if not knowledge_base:
            print("[Error] Knowledge base is empty. Cannot perform search.")
            return jsonify({"error": "The knowledge base is empty."}), 500

        print("[Debug] Step 2: Calculating similarities...")
        # Print the shape of the first item in the KB for comparison
        if knowledge_base:
             print(f"[Debug] -> Shape of first KB embedding: {knowledge_base[0]['embedding'].shape}")
        
        similarities = [manual_cosine_similarity(query_embedding, item['embedding']) for item in knowledge_base]
        
        print(f"[Debug] -> Similarities calculated: {similarities}")
        
        top_indices = np.argsort(similarities)[-3:][::-1]
        print(f"[Debug] -> Top 3 indices found: {top_indices}")
        
        context = "\n".join([knowledge_base[i]['answer'] for i in top_indices])
        print(f"[Debug] -> Context built:\n---\n{context}\n---")
        
        # Step 3: Generate final response
        print("[Debug] Step 3: Sending to Gemini for final answer...")
        prompt = f"Based ONLY on the following context, answer the user's question.\nContext: {context}\nUser's Question: {user_message}\nAnswer:"
        response = generative_model.generate_content(prompt)
        
        print(f"[Debug] -> Final AI response: {response.text}")
        return jsonify({"response": response.text})

    except Exception as e:
        print(f"--- UNHANDLED EXCEPTION in /chat ---")
        # This will now print any unexpected error to the console
        import traceback
        traceback.print_exc()
        print(f"------------------------------------")
        return jsonify({"error": "An internal error occurred while generating a response."}), 500

if __name__ == '__main__':
    initialize_system()
    if is_system_healthy:
        app.run(port=5000, debug=True, host='0.0.0.0')
    else:
        print("Server did not start due to a fatal error during initialization.")

# ### **Your Final Action Plan**

# 1.  **Replace Code:** Put the new "Loud Debugging" code into `app.py`.
# 2.  **Stop and Restart Server:** Go to your terminal, stop the server (`Ctrl + C`), and start it again (`python app.py`).
# 3.  **Trigger the Error:** Go to your front-end and send one message.
# 4.  **Examine the Backend Terminal:** This is the most important step. Do not look at the browser. Look at the terminal where `app.py` is running.

# You will now see a series of `[Debug]` messages printing out the status at every single step. **Please copy and paste the entire output from the terminal, starting from "--- NEW CHAT REQUEST ---"**.

# This output will show us:
# *   The type and length of the embedding generated for your question.
# *   The shape of the embeddings stored in your knowledge base.
# *   The list of similarity scores.
# *   The exact point where it fails.

# With this information, we will be able to pinpoint the exact line and data that is causing the final issue.
