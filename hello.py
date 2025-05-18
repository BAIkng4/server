from flask import Flask, jsonify
from pymongo import MongoClient
import os

app = Flask(__name__)
mongodb_token = "mongodb+srv://gksbot:gttopia01@datacluster.cn2geam.mongodb.net/"

try:
    mongodb_client = MongoClient(mongodb_token)
    mongodb_name = mongodb_client["gks_bot"]
    mongodb_name.list_collection_names()
    
    mongodb_user_collection = mongodb_name["user_data"]

    print("Successfully connected to the main database!")
except Exception as e:
    print(f"Failed to connect to the main database: {e}")
    exit()
    
@app.route('/')
def hello():
    # Ambil data dari koleksi MongoDB
    documents = mongodb_user_collection.find()
    
    # Ubah ke bentuk list agar bisa ditampilkan
    result = []
    for doc in documents:
        doc["_id"] = str(doc["_id"])  # ubah ObjectId jadi string agar JSON-valid
        result.append(doc)

    return jsonify(result)
