from typing import Any

from hvac import Client as VaultHVACClient


class VaultClient:
    def __init__(self, vault_address: str, vault_token: str) -> None:
        self.vault_address: str = vault_address
        self.vault_token: str = vault_token
        self.client: VaultHVACClient = VaultHVACClient(url=self.vault_address, token=self.vault_token)

    def get_secret(self, path: str, key: str) -> str | None:
        try:
            secret: dict[str, Any] = self.client.secrets.kv.v2.read_secret_version(  # type: ignore
                path=f"{path}/{key}"
            )
            return secret["data"]["data"]["token"]  # type: ignore
        except Exception as e:
            print(f"Error retrieving secret from path {path}: {e}")
            return None
