import json, requests, base64

# Read config.json
with open("config.json", "r") as file:
    config = json.load(file)
    
class GitHubDatabase:
    def __init__(self, token, username, repositories_name):
        self.username = username
        self.repositories_name = repositories_name
        self.api_base = f"https://api.github.com/repos/{username}/{repositories_name}/contents"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
    def check_connection(self):
        url = f"{self.api_base}"
        try:
            response = requests.get(url, headers=self.headers)
            return response.status_code
        except Exception as e:
            print(f"[GitHub CHECK] Exception: {e}")
            return None

    def _build_api_url(self, folder, filename):
        return f"{self.api_base}/{folder}/{filename}.json"

    def read_data(self, folder, filename):
        url = self._build_api_url(folder, filename)
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                content = response.json()
                decoded_content = json.loads(base64.b64decode(content["content"]).decode("utf-8"))
                print(f"[GitHub READ] {filename}.json already read.")
                return decoded_content
            else:
                print(f"[GitHub READ] Failed to fetch file: {response.status_code}")
        except Exception as e:
            print(f"[GitHub READ] Exception: {e}")
            
    def update_data(self, folder, filename, data):
        url = self._build_api_url(folder, filename)
        encoded_content = str(base64.b64encode(json.dumps(data, ensure_ascii=False).encode()).decode())
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                sha = response.json()["sha"]
                message = f"Update data for {filename}"
                payload = {
                    "message": message,
                    "content": encoded_content,
                    "sha": sha
                }
                update_resp = requests.put(url, headers=self.headers, data=json.dumps(payload))
                if update_resp.status_code in [200, 201]:
                    print(f"[GitHub UPDATE] {filename}.json updated.")
                else:
                    print(f"[GitHub UPDATE] Failed: {update_resp.status_code} - {update_resp.text}")
            elif response.status_code == 404:
                message = f"Create new data for {filename}"
                payload = {
                    "message": message,
                    "content": encoded_content,
                    "branch": "main"
                }
                update_resp = requests.put(url, headers=self.headers, data=json.dumps(payload, indent=4), timeout=30)
                update_resp.raise_for_status()
                if update_resp.status_code == 201:
                    print(f"[GitHub CREATE] {filename}.json created.")
                else:
                    print(f"[GitHub CREATE] Failed: {update_resp.status_code} - {update_resp.text}")
            else:
                print(f"[GitHub] Unexpected status code: {response.status_code}")
        except Exception as e:
            print(f"[GitHub ERROR] Exception: {e}")
    
    def delete_data(self, folder, filename):
        url = self._build_api_url(folder, filename)
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                sha = response.json()["sha"]
                message = f"Delete data for {filename}"
                payload = {
                    "message": message,
                    "sha": sha
                }
                delete_resp = requests.delete(url, headers=self.headers, data=json.dumps(payload))
                if delete_resp.status_code in [200, 201]:
                    print(f"[GitHub DELETE] {filename}.json deleted.")
                else:
                    print(f"[GitHub DELETE] Failed: {delete_resp.status_code} - {delete_resp.text}")
            else:
                print(f"[GitHub DELETE] Failed to fetch file: {response.status_code}")
        except Exception as e:
            print(f"[GitHub DELETE] Exception: {e}")
