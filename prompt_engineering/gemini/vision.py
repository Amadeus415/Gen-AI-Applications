import PIL.Image
import os
from dotenv import load_dotenv
import google.generativeai as genai

image_path_1 = "./images/amade.png"  # Replace with the actual path to your first image
image_path_2 = "./images/webcam_photo.jpg" # Replace with the actual path to your second image

sample_file_1 = PIL.Image.open(image_path_1)
sample_file_2 = PIL.Image.open(image_path_2)


load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

genai.configure(api_key=GEMINI_API_KEY)
#Choose a Gemini model.
model = genai.GenerativeModel(model_name="gemini-1.5-pro")

prompt = """Give this person a score out of (0-100), as well as a potential score(0-100)
    Use this JSON schema: 
    output = {
    "score": 0-100,
    "potential_score": 0-100,
    "confidence" : 0-100,
    "skin" : 0-100,
    "jawline" : 0-100,
    "hair" : 0-100,
    "smile" : 0-100,
    "visual_age" : 0-100,
    "age_percentage" : "Top 3%",
    "description" : {
        "standout" : [standout_features]
        "weaknesses" : [weaknesses looks wise]
        },
    "image_quality": {
      "overall_assessment": "",
      "lighting": [],
      "focus": [],
      "composition": [],
      "resolution": []
        }
    }

    Return: 
    output

    Instructions:
    - IMPORTANT: Output must be in valid JSON format. Do not include any text before or after the JSON brackets.
    - For age percentage, give the percentage of how good looking the person is for their age group. Ex: "Top 3%"
    - For image_quality, fill in the fields with the most relevant information based on the image.
    - For description, be straight forward and honest with human like responses. Be like "You need to work on your jawline", or "Your skin is very good for your age"
    - Image quality "overall_assessment": A brief statement about the technical quality of the image (e.g., "Good quality image," "Slightly blurry," "Poor lighting").
    - Image quality "lighting": A brief statement about the lighting of the image (e.g., "Good lighting," "Poor lighting," "Even lighting").
    - Image quality "focus": A brief statement about the focus of the image (e.g., "Good focus," "Poor focus," "Sharp focus").
    - Image quality "composition": A brief statement about the composition of the image (e.g., "Good composition," "Poor composition," "Even composition").
    - Image quality "resolution": A brief statement about the resolution of the image (e.g., "Good resolution," "Poor resolution," "High resolution").

"""

response = model.generate_content([prompt, sample_file_1, sample_file_2])

#print(response.text)

#Print raw output
print(repr(response.text))