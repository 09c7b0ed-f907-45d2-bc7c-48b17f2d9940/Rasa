import os
from hvac import Client
from dotenv import load_dotenv

load_dotenv()

class VaultClient:
    def __init__(self, vault_address: str, vault_token: str):
        self.vault_address = vault_address
        self.vault_token = vault_token
        self.client = Client(url=self.vault_address, token=self.vault_token)

    def get_secret(self, path: str, key: str):
        try:
            secret = self.client.secrets.kv.v2.read_secret_version(path=f"tokens/{key}")
            token = secret['data']['data']['token']
            return token
        except Exception as e:
            print(f"Error retrieving secret from path {path}: {e}")
            return None