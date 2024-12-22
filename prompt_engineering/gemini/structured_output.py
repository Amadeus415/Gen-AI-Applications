import PIL.Image
import os
from dotenv import load_dotenv
import google.generativeai as genai
import typing_extensions as typing
from typing import Dict, List
import json
import base64

image_path_1 = "./images/pancakes.jpg"  # Replace with the actual path to your first image
image_path_2 = "./images/pancakes.jpg" # Replace with the actual path to your second image

sample_file_1 = PIL.Image.open(image_path_1)
sample_file_2 = PIL.Image.open(image_path_2)

# Convert image to base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

base64_image_1 = encode_image(image_path_1)
base64_image_2 = encode_image(image_path_2)


load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

genai.configure(api_key=GEMINI_API_KEY)

#Define the JSON schema
class Output(typing.TypedDict):
    score: int
    potential_score: int
    confidence: int
    skin: int
    jawline: int
    hair: int
    smile: int
    visual_age: int
    age_percentage: str
    description: Dict[str, List[str]]
    image_quality: Dict[str, typing.Union[str, List[str]]]



#model_name = "gemini-1.5-pro"
model_name = "gemini-1.5-flash"
#Choose a Gemini model.
model = genai.GenerativeModel(model_name=model_name)

prompt = """You are a professional image analysis model. Analyze the provided images and output a structured JSON response with the following specific scores and attributes:

Required fields:
- score (0-100): Overall attractiveness score
- potential_score (0-100): Potential score with improvements
- confidence (0-100): Confidence in the analysis
- skin (0-100): Skin quality score
- jawline (0-100): Jawline definition score
- hair (0-100): Hair quality and style score
- smile (0-100): Smile quality score
- visual_age: Estimated age in years
- age_percentage: Percentile ranking (e.g. "Top 15%")
- description: Object with "standout" and "weaknesses" arrays
- image_quality: Object with quality assessment details

Please ensure all numeric scores are provided as integers between 0 and 100."""
 
response = model.generate_content([prompt, base64_image_1, base64_image_2]
                                  , generation_config=genai.GenerationConfig(temperature=0.1, response_mime_type="application/json" ))

#print output
#print(response.text)

response_json = json.loads(response.text)


print("score: ", response_json['score'])
print("potential_score: ", response_json['potential_score'])
print("confidence: ", response_json['confidence'])
print("skin: ", response_json['skin'])
print("jawline: ", response_json['jawline'])
print("hair: ", response_json['hair'])
print("smile: ", response_json['smile'])
print("visual_age: ", response_json['visual_age'])
print("age_percentage: ", response_json['age_percentage'])
print("description: ", response_json['description'])
print("image_quality: ", response_json['image_quality']['lighting'])

