import os
import sys
import json

class Config:
    def __init__(self, filename: str = "config.json"):
        self.config_path = os.path.join(sys.path[0], filename)

    def get(self) -> dict:
        try:
            with open(self.config_path, "r") as config_file:
                data = config_file.read()
                config_info = json.loads(data)
                return config_info
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise RuntimeError(f"Failed to load config: {e}")