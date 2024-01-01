import yaml

APP_CONFIG = {}
with open("appconfig.yaml", "r") as file:
    APP_CONFIG = yaml.safe_load(file)
