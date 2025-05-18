from flask import Flask, jsonify
from pymongo import MongoClient
import os

app = Flask(__name__)

# Ambil URL MongoDB dari environment variable (Railway menyediakannya)
mongo_uri = os.getenv("mongodb+srv://gksbot:gttopia01@datacluster.cn2geam.mongodb.net/")  # variabel ini kamu isi di Railway
client = MongoClient(mongo_uri)

# Ganti sesuai nama database dan koleksi kamu
db = client["gks_bot"]
collection = db["user_data"]

@app.route('/')
def hello():
    # Ambil data dari koleksi MongoDB
    documents = collection.find()
    
    # Ubah ke bentuk list agar bisa ditampilkan
    result = []
    for doc in documents:
        doc["_id"] = str(doc["_id"])  # ubah ObjectId jadi string agar JSON-valid
        result.append(doc)

    return jsonify(result)
