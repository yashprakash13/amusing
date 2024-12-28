import os
from pathlib import Path

import yaml

APP_CONFIG = {}


def find_or_create_config_file():
    # Define the file path
    default_root_download_path = os.path.join(Path.home(), "Downloads", "Amusing")
    default_config_path = os.path.join(default_root_download_path, "appconfig.yaml")
    alternative_config_path = os.path.join(
        os.path.join(Path.home(), ".config", "amusing"), "appconfig.yaml"
    )

    file_path = default_config_path
    if not os.path.exists(file_path) and os.path.exists(alternative_config_path):
        file_path = alternative_config_path

    # Check if the file exists
    if os.path.exists(file_path):
        return file_path
    else:
        os.makedirs(os.path.join(default_root_download_path), exist_ok=True)
        # Create the file
        with open(file_path, "w") as file:
            # Write default configuration (you can customize this)
            config_data = {
                "root_download_path": str(default_root_download_path),
                "db_name": "library.db",
            }
            yaml.dump(config_data, file)
            print(f"Created a new config file: {file_path}")
        return file_path


with open(find_or_create_config_file(), "r") as file:
    APP_CONFIG = yaml.safe_load(file)
    # Expand possible ~ in paths
    APP_CONFIG["db_name"] = os.path.expanduser(APP_CONFIG["db_name"])
    APP_CONFIG["root_download_path"] = os.path.expanduser(
        APP_CONFIG["root_download_path"]
    )
