# xAI.py - main file for xAI project

import os
from openai import OpenAI
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get API keys from .env file
XAI_API_KEY = os.getenv("XAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(
    api_key=XAI_API_KEY,
    base_url="https://api.x.ai/v1",
)

# Generate analysis
completion = client.chat.completions.create(
    model="grok-beta",
    messages=[
        {"role": "system", "content": 
         
        """
        You are a crypto analysis AI. Given a $TICKER, provide a concise analysis in the following JSON format:

        {
        "analysis": {
            "summary": {
            "sentiment": "bullish|bearish|neutral",
            "confidence": 0-100,
            "risk_level": "low|medium|high"
            },
            "key_points": {
            "strengths": [
                "max 3 key strength points"
            ],
            "risks": [
                "max 3 key risk points"
            ]
            },
            "prediction": {
            "short_term": "1-2 sentence outlook",
            "price_action": {
                "support": "nearest support level",
                "resistance": "nearest resistance level"
            }
            },
            "market_sentiment": {
            "social_media": "positive|negative|neutral",
            "trading_volume": "increasing|decreasing|stable",
            "market_cap_trend": "up|down|stable"
            }
        },
        "disclaimer": "This is AI-generated analysis for informational purposes only. Not financial advice."
        }

        Keep the analysis concise, factual, and focused on current market conditions. Avoid speculation and maintain a balanced perspective."""
         },

        {"role": "user", "content": "$govai pidgeon tech coin"},
    ],
)

# Print the analysis
print(completion.choices[0].message.content)
