from flask import Flask, request, jsonify
import requests
import base64
import time
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# Set your Plant.id API key
PLANT_ID_API_KEY = os.getenv("PLANT_ID_API_KEY")
PLANT_ID_API_URL = "https://plant.id/api/v3/health_assessment"

MAX_RETRIES = 3  # Total attempts
RETRY_DELAY = 2  # Seconds between retries

@app.route('/detect_disease', methods=['POST'])
def detect_disease():
    if 'images' not in request.files:
        return jsonify({"error": "Please upload at least one image file under the key 'images'."}), 400

    uploaded_files = request.files.getlist('images')
    images_base64 = []

    # Convert uploaded files to Base64
    for file in uploaded_files:
        file_content = file.read()
        encoded_string = base64.b64encode(file_content).decode('utf-8')
        images_base64.append(f"data:{file.content_type};base64,{encoded_string}")

    payload = {"images": images_base64}
    headers = {
        "Api-Key": PLANT_ID_API_KEY,
        "Content-Type": "application/json"
    }

    # Retry logic
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(PLANT_ID_API_URL, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            break
        except requests.exceptions.RequestException as e:
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                return jsonify({"error": f"Failed after {MAX_RETRIES} attempts: {str(e)}"}), 500

    result = response.json()

    # Extract diseases and suggestions
    diseases_detected = []

    for disease in result.get("diseases", []):
        disease_info = {
            "disease_name": disease.get("name"),
            "probability": disease.get("probability"),
            "suggestions": [s.get("name") for s in disease.get("suggestions", [])]
        }
        diseases_detected.append(disease_info)

    return jsonify({
        "diseases_detected": diseases_detected
    })


if __name__ == "__main__":
    app.run(debug=True)