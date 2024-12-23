import google.generativeai as genai
from typing import Dict, List, Tuple
import re
from dotenv import load_dotenv
import os
from enum import Enum
import json

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

class ModelType(Enum):
    FLASH = "gemini-1.5-flash"
    PRO = "gemini-1.5-pro"

class ModelRouter:
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        # Initialize both models
        self.flash_model = genai.GenerativeModel('gemini-1.5-flash')
        self.pro_model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Router model for classification
        self.router_model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Define routing criteria patterns
        self.complex_patterns = {
            "reasoning": [
                r"explain\s+in\s+detail",
                r"analyze",
                r"compare\s+and\s+contrast",
                r"what\s+are\s+the\s+implications",
                r"why\s+does",
                r"how\s+would\s+you\s+design"
            ],
            "technical": [
                r"system\s+design",
                r"architecture",
                r"security",
                r"optimization",
                r"scalability",
                r"microservices"
            ],
            "code": [
                r"debug",
                r"refactor",
                r"code\s+review",
                r"complex\s+algorithm",
                r"performance\s+optimization"
            ]
        }

    async def _analyze_complexity(self, question: str) -> Tuple[ModelType, float]:
        """
        Use the router model to analyze question complexity and choose appropriate model
        """
        prompt = f"""
        Analyze this technical question and determine if it requires Gemini 1.5 Pro (for complex reasoning) 
        or if Gemini 1.5 Flash (for simpler queries) would suffice.

        Question: {question}

        Return a JSON object with:
        1. "model": Either "FLASH" or "PRO"
        2. "confidence": Number between 0-1
        3. "reasoning": Brief explanation of the choice

        Consider:
        - Complex reasoning/analysis needs -> Pro
        - System design/architecture -> Pro
        - Advanced code review/debugging -> Pro
        - Simple explanations/basic concepts -> Flash
        - Straightforward code questions -> Flash
        - Quick factual queries -> Flash
        """

        response = self.router_model.generate_content(prompt)
        try:
            result = json.loads(response.text)
            model_type = ModelType[result["model"]]
            confidence = float(result["confidence"])
            return model_type, confidence
        except (json.JSONDecodeError, KeyError):
            # Default to PRO if analysis fails
            return ModelType.PRO, 0.5

    def _pattern_match_complexity(self, question: str) -> bool:
        """Check if question matches any complex patterns"""
        question = question.lower()
        
        # Check all patterns
        for category, patterns in self.complex_patterns.items():
            for pattern in patterns:
                if re.search(pattern, question):
                    return True
        return False

    def _contains_code_block(self, text: str) -> bool:
        """Check if text contains code blocks"""
        return bool(re.search(r'```[\s\S]*?```', text))

    async def route_question(self, question: str) -> genai.GenerativeModel:
        """
        Route the question to appropriate model based on complexity analysis
        """
        # First check for obvious indicators
        if self._contains_code_block(question) or self._pattern_match_complexity(question):
            return self.pro_model
            
        # Use LLM router for more nuanced analysis
        model_type, confidence = await self._analyze_complexity(question)
        
        # If confidence is low, fall back to pattern matching
        if confidence < 0.7:
            return self.pro_model if self._pattern_match_complexity(question) else self.flash_model
            
        return self.pro_model if model_type == ModelType.PRO else self.flash_model

    async def get_response(self, question: str) -> Dict:
        """Get response from the appropriate model with metadata"""
        model = await self.route_question(question)
        response = model.generate_content(question)
        
        return {
            "model_used": model.model_name,
            "response": response.text,
            "timestamp": datetime.now().isoformat()
        }

# Example usage
async def main():
    router = ModelRouter()
    
    # Test cases
    questions = [
        "What is a variable in Python?",
        """Can you review this code for security vulnerabilities?
        ```python
        def process_user_input(data):
            query = f"SELECT * FROM users WHERE id = {data}"
            return execute_query(query)
        ```
        """,
        "Design a scalable microservices architecture for an e-commerce platform",
        "What's the syntax for a for loop in JavaScript?"
    ]
    
    for question in questions:
        response = await router.get_response(question)
        print(f"\nQuestion: {question[:50]}...")
        print(f"Routed to: {response['model_used']}")
        # print(f"Response: {response['response']}"), Uncomment this to see the response

if __name__ == "__main__":
    import asyncio
    from datetime import datetime
    asyncio.run(main())
