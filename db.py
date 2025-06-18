import os
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv

# Load secrets from .env
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

def add_coins_to_user(identifier, coins_to_add):
    """
    Add coins to a user in MongoDB by email or _id.

    Parameters:
    - identifier (str): User email or ObjectId string
    - coins_to_add (float): Number of coins to add

    Returns:
    - dict: {"status": "success" or "error", "message": str}
    """
    try:
        client = MongoClient(MONGO_URI)
        db = client["cv_tailoring"]
        users_col = db["users"]

        # Detect whether the identifier is an ObjectId or email
        try:
            query = {"_id": ObjectId(identifier)}
        except:
            query = {"email": identifier}

        result = users_col.update_one(
            query,
            {"$inc": {"coin_balance": coins_to_add}}
        )

        if result.matched_count == 0:
            return {"status": "error", "message": "User not found"}
        
        return {"status": "success", "message": f"Added {coins_to_add} coins."}

    except Exception as e:
        return {"status": "error", "message": str(e)}


# By email
response = add_coins_to_user("johnnyjonathan008@gmail.com", 5)
print(response)

# # By ObjectId
# response = add_coins_to_user("665f33b946bccef6e86c48a3", 2.5)
# print(response)
