import requests, json, base64
from datetime import datetime, timezone

# Read config.json
with open("config.json", "r") as file:
    config_base64 = json.load(file)

decoded_json_str = base64.b64decode(config_base64).decode("utf-8")
config = json.loads(decoded_json_str)
    
class BalanceUpdater:
    def get_user_profile(self):
        user_url = "https://discord.com/api/v9/users/@me"
        headers = {
            "Authorization": f"Bot {config['discord']['discord_token']}"
        }

        response = requests.get(user_url, headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            avatar = f'https://cdn.discordapp.com/avatars/{user_data["id"]}/{user_data["avatar"]}.png'
            return avatar
        else:
            print("Failed to fetch Discord user data:", response.status_code, response.text)
            return ""

    def get_dm_channel_id(self, userid):
        channel_url = "https://discord.com/api/v9/users/@me/channels"
        headers = {
            "Authorization": f"Bot {config['discord']['discord_token']}",
            "Content-Type": "application/json"
        }
        json_data = {"recipient_id": userid}

        response = requests.post(channel_url, headers=headers, json=json_data)
        if response.status_code == 200:
            return response.json()["id"]
        else:
            print("Failed to fetch Discord channel id:", response.status_code, response.text)
            return ""

    def send_message_discord(self, userid, donator_name, previous_balance, balance_change, new_balance):
        avatar = self.get_user_profile()
        dm_channel_id = self.get_dm_channel_id(userid)

        embed = {
            "title": f"{donator_name}",
            "description": "Thank you for topping up your balance.",
            "color": int("3bff5f", 16),
            "fields": [
                {"name": "Previous Balance", "value": f"{previous_balance}", "inline": False},
                {"name": "Balance Change", "value": f"+{balance_change}", "inline": False},
                {"name": "Current Balance", "value": f"{new_balance}", "inline": False}
            ],
            "footer": {"text": "Grow King Bot", "icon_url": avatar},
            "timestamp": datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
        }

        headers = {
            "Authorization": f"Bot {config['discord']['discord_token']}",
            "Content-Type": "application/json"
        }

        data = {"embeds": [embed]}
        logs_url = f"https://discord.com/api/v9/channels/{config['channel_id_logs']['balance_logs']}/messages"
        requests.post(logs_url, headers=headers, data=json.dumps(data))

        # DM user
        if dm_channel_id:
            dm_url = f"https://discord.com/api/v9/channels/{dm_channel_id}/messages"
            requests.post(dm_url, headers=headers, data=json.dumps(data))

    def update_balance(self, mongodb_user_collection, backup_db, backup_folder_user, topup_data):
        try:
            donator_name = topup_data["donator_name"]
            amount = float(topup_data["amount_raw"])
            
            user_data = mongodb_user_collection.find_one({"donator_name": donator_name})
            previous_balance = user_data.get("balance", 0) if user_data else 0
            new_balance = previous_balance + amount
            
            if user_data:
                userid = user_data.get('userid', '0')
                mongodb_user_collection.update_one({"donator_name": donator_name}, {"$set": {"balance": new_balance}})

                # Delete old backup
                old_filename = f"{userid}_{user_data.get('code', 0)}"
                if backup_db.read_data(backup_folder_user, old_filename):
                    backup_db.delete_data(backup_folder_user, old_filename)

                # Upload new backup
                backup_user_data = mongodb_user_collection.find_one({"donator_name": donator_name})
                new_filename = f"{backup_user_data.get('userid', '0')}_{backup_user_data.get('code', 0)}"
                backup_db.update_data(backup_folder_user, new_filename, backup_user_data)

                self.send_message_discord(userid, donator_name, previous_balance, amount, new_balance)
                
                #topup logs
                topup_logs_folder = "logs"
                topup_logs_filename = "topup_logs"
                topup_logs_data = backup_db.read_data(topup_logs_folder, topup_logs_filename)
                
                if not topup_logs_data:
                    topup_logs_data = []
                    
                topup_logs_data.append(topup_data)
                
                backup_db.update_data(topup_logs_folder, topup_logs_filename, topup_logs_data)
                
                return "Success to update balance!", 200
        except Exception as e:
            print(f"[ERROR] Failed to update balance: {e}")
            return "Failed to update balance!", 400

