import requests, json, base64, math
from datetime import datetime, timezone

# Read config.json
with open("config.json", "r") as file:
    config_base64 = json.load(file)

decoded_json_str = base64.b64decode(config_base64).decode("utf-8")
config = json.loads(decoded_json_str)

def value_rounding(value):
    decimal_value = (value * 100) % 1
    if decimal_value < 0.5:
        return math.floor(value * 100) / 100
    else:
        return math.ceil(value * 100) / 100
        
class BalanceUpdater:
    def get_user_profile(self):
        user_url = "https://discord.com/api/v9/users/@me"
        headers = {
            "Authorization": f"Bot {config['discord']['discord_token']}"
        }

        response = requests.get(user_url, headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            
            bot_name = user_data["username"]
            avatar = f'https://cdn.discordapp.com/avatars/{user_data["id"]}/{user_data["avatar"]}.png'
            return bot_name, avatar
        else:
            print("Failed to fetch Discord user data:", response.status_code, response.text)
            return ""

    def get_dm_channel_id(self, discord_userid):
        channel_url = "https://discord.com/api/v9/users/@me/channels"
        headers = {
            "Authorization": f"Bot {config['discord']['discord_token']}",
            "Content-Type": "application/json"
        }
        json_data = {"recipient_id": discord_userid}

        response = requests.post(channel_url, headers=headers, json=json_data)
        if response.status_code == 200:
            return response.json()["id"]
        else:
            print("Failed to fetch Discord channel id:", response.status_code, response.text)
            return ""
        
    def send_message_discord(self, discord_name, discord_userid, previous_balance, balance_change, new_balance, amount_raw, saweria_rate):
        bot_name, avatar = self.get_user_profile()
        log_channel_id = config["channel_id_logs"]["balance_logs"]
        dm_channel_id = self.get_dm_channel_id(discord_userid)
        
        embed = {
            "title": f"{discord_name} Balance",
            "description": "Thank you for topping up your balance.",
            "color": int("03fc30", 16),
            "fields": [
                {
                    "name": "<:GKS_Balance:1135755520008015902> Balance Details", 
                    "value": ( 
                        f"**Previous balance**: {previous_balance} <:WL:1124725498363256937>\n"
                        f"**Balance change**: {balance_change} <:WL:1124725498363256937>\n"
                        f"**Current balance**: {new_balance} <:WL:1124725498363256937>"
                    ),
                    "inline": False
                },
                {
                    "name": ":abacus: Balance Calculation", 
                    "value": ( 
                        f"**Calculation**: `Rp{amount_raw:,.2f}`/`Rp{saweria_rate:,.2f}` = {balance_change} <:WL:1124725498363256937>"
                    ),
                    "inline": False
                }
            ],
            "footer": {"text": bot_name, "icon_url": avatar},
            "timestamp": datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
        }

        headers = {
            "Authorization": f"Bot {config['discord']['discord_token']}",
            "Content-Type": "application/json"
        }
        
        data = {
            "content": f"<@{discord_userid}>, successful balance update!", 
            "embeds": [embed]
        }
        
        # Send to logs
        if log_channel_id:
            logs_url = f"https://discord.com/api/v9/channels/{log_channel_id}/messages"
            requests.post(logs_url, headers=headers, data=json.dumps(data))
        
        # DM user
        if dm_channel_id:
            dm_url = f"https://discord.com/api/v9/channels/{dm_channel_id}/messages"
            requests.post(dm_url, headers=headers, data=json.dumps(data))

    def update_balance(self, backup_db, backup_folder_user, mongodb_user_collection, mongodb_payment_collection, topup_data):
        try:
            if topup_data:
                username = topup_data.get("donator_name", "") if topup_data else ""
                donator_email = topup_data.get("donator_email", "") if topup_data else ""
                amount_raw = float(topup_data.get("amount_raw", 0)) if topup_data else float(0)
            else:
                return None
            
            user_data = mongodb_user_collection.find_one({"username": username.upper()})
            payment_data = mongodb_payment_collection.find_one({"_id": "GKS_PAYMENT"})
            
            #topup logs
            topup_logs_folder = "logs"
            topup_logs_filename = "topup_logs"
            topup_logs_data = backup_db.read_data(topup_logs_folder, topup_logs_filename)
            
            if not topup_logs_data:
                topup_logs_data = []
                
            topup_logs_data.append(topup_data)
            backup_db.update_data(topup_logs_folder, topup_logs_filename, topup_logs_data)
            
            if payment_data:
                saweria_rate = float(payment_data.get("saweria_rate", 0)) if payment_data else float(0)
                if donator_email:
                    amount = value_rounding(amount_raw / saweria_rate)
                else:
                    amount = value_rounding(amount_raw)
            
            discord_name = user_data.get('discord_name', username) if user_data else username
            discord_userid = user_data.get('discord_userid', 0) if user_data else 0
            previous_balance = float(user_data.get("balance", 0)) if user_data else float(0)
                
            new_balance = previous_balance + amount
                
            if user_data:
                mongodb_user_collection.update_one({"username": username.upper()}, {"$set": {"balance": new_balance}})

                old_filename = f"{discord_userid}_{user_data.get('login_code', 0)}"
                if backup_db.read_data(backup_folder_user, old_filename):
                    backup_db.delete_data(backup_folder_user, old_filename)

                backup_user_data = mongodb_user_collection.find_one({"username": username.upper()})
                new_filename = f"{backup_user_data.get('discord_userid', 0)}_{backup_user_data.get('login_code', 0)}"
                backup_db.update_data(backup_folder_user, new_filename, backup_user_data)

                self.send_message_discord(discord_name.title(), discord_userid, previous_balance, amount, new_balance, amount_raw, saweria_rate)
                return "Success to update balance!", 200
            else:
                self.send_message_discord(discord_name.title(), discord_userid, previous_balance, amount, new_balance, amount_raw, saweria_rate)
        except Exception as e:
            print(f"[ERROR] Failed to update balance: {e}")
            return "Failed to update balance!", 400
