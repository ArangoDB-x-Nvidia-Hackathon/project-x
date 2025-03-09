from dotenv import load_dotenv
from arango import ArangoClient
from arango_datasets import Datasets
import os


# Load environment variables from .env file
load_dotenv()

# Initialize the ArangoDB client.
host = os.getenv("HOST")
username = os.getenv("USER")
password = os.getenv("PASSWORD")


# Connect to database
db = ArangoClient(hosts=host).db(username= username, password=password, verify=True)

# Connect to datasets
datasets = Datasets(db)