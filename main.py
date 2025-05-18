import os
import logging
from flask import Flask, request
from pymongo import MongoClient
from update_balance import BalanceUpdater

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

def load_db():
    try:
        mongodb_token = "mongodb+srv://gksbot:gttopia01@datacluster.cn2geam.mongodb.net/"
        mongodb_client = MongoClient(mongodb_token)
        mongodb_name = mongodb_client["gks_bot"]
        mongodb_name.list_collection_names()
        print("Successfully connected to the main database!")
        return mongodb_name["user_data"]
    except Exception as e:
        print(f"Failed to connect to the main database: {e}")
        exit()

mongodb_user_collection = load_db()

@app.route('/')
def main():
    return '<h2>GROW KING SCRIPTS</h2>', 200

@app.route('/topup', methods=['POST'])
def topup_webhook():
    try:
        data = request.get_json()
        logging.info(data)
        logging.info("...................")

        donator_name = data["donator_name"]
        amount = float(data["amount_raw"])  # pastikan ini bisa dikonversi ke float

        updater = BalanceUpdater()
        updater.update_balance(mongodb_user_collection, donator_name, amount)
        return "Berhasil", 200
    except Exception as e:
        logging.error(f"JSON parse error: {e}")
        return "Invalid Data", 400
