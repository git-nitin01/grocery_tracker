# fast api backend to process the image and extract data
from veryfi import Client
from fastapi import FastAPI
from pymongo import MongoClient
from pydantic import BaseModel

app = FastAPI()

# data model
class Data(BaseModel):
    items: list
    quantity: list
    total: list
    last_purchased: list
    frequency: list

# Create a MongoDB client
client = MongoClient("mongodb://localhost:27017/")

# Find the user database
db = client["grocery_tracker_users"]

# Find the grocery data database
db_tracker = client["grocery_tracker_data"]

from fastapi import HTTPException

@app.get("/get_user")
async def get_user(user_name: str):

    # Find the collection with the user_name
    collection = db[user_name]

    # Check if the collection exists
    if collection is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Find the user document in the collection
    user_data = collection.find_one()

    # Return the user details
    return {"message": "User found", "status": 200, "username": user_data["user_name"],
             "user_id": user_data["user_id"], "user_secret": user_data["user_secret"], 
             "user_api_key": user_data["user_api_key"]}

    


@app.post("/set_user")
async def set_user(user_name: str, user_id: str, user_secret: str, user_api_key: str):

    try:
        # Access or create the collection
        collection = db[user_name]

        # Insert the data into the collection
        result = collection.insert_one({
            "user_name": user_name,
            "user_id": user_id,
            "user_secret": user_secret,
            "user_api_key": user_api_key
        })

        if result.inserted_id:
            return {"message": f"User data saved successfully!{result}", "status": 200} 
        else:
            return {"message": "User data not saved!", "status": 500}  # Internal Server Error
    except Exception as e:
        return {"message": f"Error: {e}", "status": 500} 


async def process_document_async(client_id, client_secret, username, api_key, file_path, categories):
    # Create a Veryfi client
    veryfi_client = Client(client_id, client_secret, username, api_key)
    # Submit document for processing
    return veryfi_client.process_document(file_path, categories=categories)

# endpoint to extract data from the image
@app.post("/extract_data")
async def extract_data(image, client_id, client_secret, username, api_key): 
    categories = ['Grocery']

    # Submit the document for processing asynchronously
    data = await process_document_async(client_id, client_secret, username, api_key, image, categories)

    # send the data back to the client in json format
    buy_date =  data["date"].split()[0]
    extracted_data = {
        'last_purchased': [buy_date]*len(data["line_items"]),
        'total': [],
        'items': [],
        'quantity': [],
        'frequency': [1]*len(data["line_items"])
    }

    for item in data["line_items"]:
        extracted_data["items"].append(item["description"])
        extracted_data["quantity"].append(item["quantity"])
        extracted_data["total"].append(item["total"])
    
    return extracted_data

# endpoint to retrieve the grocery list of the user
@app.get("/get_grocery_list")
async def get_grocery_list(username):

    # Find the collection with the user_name
    collection = db_tracker[username]

    # Check if the collection exists
    if collection is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Find the user document in the collection
    data = collection.find_one()

    # Return the grocery list
    grocery_list = {
        "items": data["items"],
        "quantity": data["quantity"],
        "total": data["total"],
        "last_purchased": data["last_purchased"],
        "frequency": data["frequency"]
    }
    return grocery_list

# save the extracted data to the database
@app.post("/save_data")
async def save_data(user_name, data: Data):

    # find the database
    db = client["grocery_tracker_data"]

    # find the collection with the user_id
    collection = db[user_name]

    # check if the collection exists
    if collection is None:
        # create a new collection
        collection = db.create_collection(user_name)
    
    # delete the existing data
    collection.delete_many({})
    # Insert the data into the collection
    collection.insert_one(data.dict())

    return {"message": "Data saved successfully!"}
    

# endpoint to update the grocery list of the user
@app.post("/update_grocery_list")
async def update_grocery_list(user_name, data: Data):

    # find the collection with the user_id
    collection = db_tracker[user_name]

    # Check if the collection exists
    if collection is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    else:
        # update the grocery list
        existing_data = collection.find_one()

        # for similar items, add the quantities, total and update the last purchased date
        data = data.dict()
        for i in range(len(data["items"])):
            if data["items"][i] in existing_data["items"]:
                # skip update if date is same or less than the last purchased date
                if data["last_purchased"][i] <= existing_data["last_purchased"][existing_data["items"].index(data["items"][i])]:
                    continue
                
                else:
                    index = existing_data["items"].index(data["items"][i])
                    existing_data["frequency"][index] += 1
                    existing_data["quantity"][index] += data["quantity"][i]
                    existing_data["total"][index] += data["total"][i]
                    existing_data["last_purchased"][index] = data["last_purchased"][i]
            else:
                existing_data["items"].append(data["items"][i])
                existing_data["quantity"].append(data["quantity"][i])
                existing_data["total"].append(data["total"][i])
                existing_data["frequency"].append(1)
                existing_data["last_purchased"].append(data["last_purchased"][i])

        # update the collection
        collection.update_one({}, {"$set": existing_data})

        return {"message": "Grocery list updated successfully!"}


