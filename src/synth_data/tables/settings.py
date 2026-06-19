import os

from dotenv import load_dotenv

load_dotenv()

_DB_CONFIG = {
    "host": os.getenv("DB_HOST_LOCAL"),
    "port": int(os.getenv("DB_PORT_LOCAL")),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}