class BalanceUpdater:
    def update_balance(self, collection, username, amount):
        try:
            user = collection.find_one({"username": username})
            
            if not user:
                print(f"User {username} tidak ditemukan.")
                return False

            current_balance = user.get("balance", 0)
            new_balance = current_balance + amount

            result = collection.update_one(
                {"username": username},
                {"$set": {"balance": new_balance}}
            )

            if result.modified_count == 1:
                print(f"Saldo {username} berhasil diupdate menjadi {new_balance}.")
            else:
                print(f"Saldo {username} tidak berubah.")
            return True

        except Exception as e:
            print(f"Error saat update saldo: {e}")
            return False
