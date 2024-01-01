import os
from pathlib import Path

import yaml

APP_CONFIG = {}


def find_or_create_config_file():
    # Define the file path
    os.makedirs(os.path.join(Path.home(), "Downloads", "Amusing"), exist_ok=True)
    file_path = os.path.join(Path.home(), "Downloads", "Amusing", "appconfig.yaml")

    # Check if the file exists
    if os.path.exists(file_path):
        return file_path
    else:
        # Create the file
        with open(file_path, "w") as file:
            # Write default configuration (you can customize this)
            config_data = {
                "root_download_path": str(
                    os.path.join(Path.home(), "Downloads", "Amusing", "data")
                ),
                "db_name": "library.db",
            }
            yaml.dump(config_data, file)
            print(f"Created a new config file: {file_path}")
        return file_path


with open(find_or_create_config_file(), "r") as file:
    APP_CONFIG = yaml.safe_load(file)
