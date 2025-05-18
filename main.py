import os, json
from flask import Flask, request
from pymongo import MongoClient
from update_balance import BalanceUpdater
from database.github_db import GitHubDatabase

app = Flask(__name__)

# Read config.json
with open("config.json", "r") as file:
    config = json.load(file)
    
def load_db():
	# Setup MongoDB
	try:
		mongodb_config = config["database"]["mongodb"]
		mongodb_token = mongodb_config["mongodb_token"]
		mongodb_client = MongoClient(mongodb_token)
		mongodb_name = mongodb_client[mongodb_config["mongodb_name"]]
		mongodb_name.list_collection_names()
		
		mongodb_user_collection = mongodb_name[mongodb_config["mongodb_collection"]["user"]]
		
		print("Successfully connected to the main database!")
	except Exception as e:
		print(f"Failed to connect to the main database: {e}")
		exit()
		
	# Setup GitHub backup DB
	try:
		github_config = config["database"]["github"]
		github_token = github_config["github_token"]
		github_username = github_config["github_username"]
		github_repositories = github_config["github_repositories"]
		github_folder = github_config["github_folder"]

		backup_db = GitHubDatabase(token=github_token, username=github_username, repositories_name=github_repositories)
		backup_folder_user = github_folder["user"]
		
		status = backup_db.check_connection()
		if status == 200:
			print("Successfully connected to the backup database!")
		else:
			print("Failed to connect to the backup database! Repositories are not found or tokens cannot be accessed.")
			exit()
	except Exception as e:
		print(f"Failed to connect to the backup database: {e}")
		exit()
		
	return mongodb_user_collection, backup_db, backup_folder_user

mongodb_user_collection, backup_db, backup_folder_user = load_db()

@app.route('/')
def main():
	return '<h2>GROW KING SCRIPTS</h2>', 200

@app.route('/topup', methods=['POST'])
def topup_webhook():
	try:
		data = request.get_json()
		donator_name = data["donator_name"]
		amount = float(data["amount_raw"])  # pastikan ini bisa dikonversi ke float

		updater = BalanceUpdater()
		updater.update_balance(mongodb_user_collection, backup_db, backup_folder_user, donator_name, amount)
		return "Berhasil", 200
	except Exception as e:
		print(f"JSON parse error: {e}")
		return "Invalid Data", 400

if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0', port=5000)
