
from streamlit_cropperjs import st_cropperjs
import streamlit as st
import aiohttp
import time
import asyncio

# User class to store user details
class User:
    def __init__(self, username, user_id, user_secret, user_api_key):
        self.user_name = username
        self.user_id = user_id
        self.user_secret = user_secret
        self.user_api_key = user_api_key
    
    # Function to generate the client package
    def get_client_package(self):
        return {
            'client_id': self.user_id, 
            'client_secret': self.user_secret,
            'username': self.user_name,
            'api_key': self.user_api_key
        }

# Function to get user details from backend
async def get_user(username):
    url = f"http://127.0.0.1:8000/get_user?user_name={username}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                print(data)
                return data
            else:
                print(f"Request failed with status code: {response}")
                return None

# Function to save the user details to the database
async def save_user(username, client_package):
    url = f"http://127.0.0.1:8000/set_user?user_name={username}&user_id={client_package['client_id']}&user_secret={client_package['client_secret']}&user_api_key={client_package['api_key']}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url) as response:
            if response.status == 200:
                data = await response.json()
                print(data)
                return data
            else:
                print(f"Request failed with status code: {response}")
                return None

# Function to process the image
async def process_image(image, payload):
    url = f"http://127.0.0.1:8000/extract_data?image={image}&client_id={payload['client_id']}&client_secret={payload['client_secret']}&username={payload['username']}&api_key={payload['api_key']}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url) as response:
            if response.status == 200:
                data = await response.json()
                print(data)
                return data
            else:
                print(f"Request failed with status code: {response}")
                return None

# Function to update the grocery data
async def update_grocery_data(username, data):
    url = f"http://127.0.0.1:8000/update_grocery_list?user_name={username}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as response:
            if response.status == 200:
                data = await response.json()
                print(data)
                return data
            else:
                print(f"Request failed with status code: {response}")
                return None
        
# Function to get the grocery list
async def get_grocery_list(username):
    url = f"http://127.0.0.1:8000/get_grocery_list?username={username}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                print(data)
                return data
            else:
                print(f"Request failed with status code: {response}")
                return None

# Function to save the grocery list
async def save_grocery_list(username, data):
    url = f"http://127.0.0.1:8000/save_data?user_name={username}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as response:
            if response.status == 200:
                data = await response.json()
                print(data)
                return data
            else:
                print(f"Request failed with status code: {response}")
                return None

# Main function to run the Streamlit app
async def main():
    # Set the title of the app
    st.title("Grocery Tracker App")

    # make a user object
    st_session = st.session_state
    if "payload" not in st_session:
        st_session.payload = None
    
    if "data" not in st_session:
        st_session.data = None

    # Get the user action (sign-in or sign-up)
    action = st.radio("Select action", ["Sign In", "Sign Up", "Upload Image", "View Data"])

    if action == "Sign In":
        # Draw the user sign-in form
        st.subheader("Sign In")
        username = st.text_input("Username")
        response = None
        if st.button("Sign In"):
            with st.spinner("Signing in..."):
                response = await get_user(username)

            if response is None:
                st.error("User not found! Please sign up.")
            else:
                obj = User(response["username"], response["user_id"], response["user_secret"], response["user_api_key"])
                st_session.payload = obj.get_client_package()
                st.success("Sign-in successful!")
                del obj

                # Proceed with your application logic using the obtained user details

    elif action == "Sign Up":
        # Draw the user sign-up form
        st.subheader("Sign Up")
        username = st.text_input("Username")
        user_id = st.text_input("User ID")
        user_secret = st.text_input("User Secret")
        user_api_key = st.text_input("User API Key")
        
        if st.button("Sign Up"):
            with st.spinner("Signing up..."):
                user = User(username, user_id, user_secret, user_api_key)
                response = await save_user(username, user.get_client_package())
                if response is not None:
                    st.success("Sign-up successful!")
                    # Proceed with your application logic using the obtained user details
                else:
                    st.error("Failed to sign up. Please try again.")
        
                # delete the user object
                del user

    elif action == "Upload Image":
        payload = st_session.payload
        if payload is not None:
            st.subheader("Upload image")
            uploaded_image = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

            if uploaded_image is not None:
                # Use st_cropperjs to allow users to crop the image
                cropped_image = st_cropperjs(uploaded_image.read(), btn_text="Crop", key="foo")

                # Display the cropped image
                if cropped_image is not None:
                    st.image(cropped_image, caption="Cropped Image", width=400)
                
                    # creating a unique name for image based on timestamp
                    image_name = f"receipts/image_{int(time.time())}.png"

                    # Save the cropped image to receipts folder
                    with open(image_name, "wb") as f:
                        f.write(cropped_image)

                    # ask user if they want to upload list or update list
                    list_action = st.radio("Select action", ["Update Grocery List", "Save Grocery List"])
                    
                    if st.button("Proceed"):
                        with st.spinner("Uploading image..."):
                            # Process the image asynchronously
                            data = await process_image(image_name, payload)
                            if list_action == "Update Grocery List":
                                response = await update_grocery_data(payload["username"], data)
                                if response is not None:
                                    st.success("Grocery list updated successfully!")
                                else:
                                    st.error("Failed to update grocery list. Please try again.")
                            else:
                                # save the grocery list
                                response = await save_grocery_list(payload["username"], data)
                                if response is not None:
                                    st.success("Grocery list saved successfully!")
                                else:
                                    st.error("Failed to save grocery list. Please try again.")
        
        else:
            st.error("Please sign in to proceed.")
    
    elif action == "View Data":
        st.subheader("View Data")
        payload = st_session.payload
        if payload is not None:
            st_session.data = await get_grocery_list(payload["username"])

            if st_session.data is not None:
                st.table(st_session.data)
            else:
                st.error("Failed to fetch grocery list. Please try again.")
        else:
            st.error("Please sign in to proceed.")
        

        


if __name__ == "__main__":
    asyncio.run(main())
