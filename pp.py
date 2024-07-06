import requests
import os

# Define the URL of your ngrok endpoint
url = "http://b36a-34-173-147-145.ngrok-free.app/crop"

# Define the JSON payload
json_body = {
    "url": "https://t3.ftcdn.net/jpg/06/37/72/10/360_F_637721083_ap5scVXgJP36cMu5KjzQi78eY0pJa7JW.jpg",
    "query": "frisbee"
}

try:
    # Send POST request
    response = requests.post(url, json=json_body)
    response.raise_for_status()  # Raise error for bad response status
    
    # Save the received image
    with open('cropped_image.jpg', 'wb') as f:
        f.write(response.content)
    
    print("Image saved as cropped_image.jpg")

except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
