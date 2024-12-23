import google.generativeai as genai
from typing import Dict, List
import json
from datetime import datetime
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

class SurgeryVotingSystem:
    def __init__(self, api_key: str = GEMINI_API_KEY):
        genai.configure(api_key=api_key)
        # Create models with different temperature settings for more diverse opinions
        self.models = [
            genai.GenerativeModel('gemini-1.5-pro', generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                candidate_count=1,
                top_p=0.9,
                top_k=40
            )),
            genai.GenerativeModel('gemini-1.5-pro', generation_config=genai.types.GenerationConfig(
                temperature=0.8,
                candidate_count=1,
                top_p=0.9,
                top_k=40
            )),
            genai.GenerativeModel('gemini-1.5-pro', generation_config=genai.types.GenerationConfig(
                temperature=0.9,
                candidate_count=1,
                top_p=0.9,
                top_k=40
            ))
        ]

    async def get_vote(self, model: genai.GenerativeModel, patient_data: Dict) -> Dict:
        """Get a single vote from one model instance"""
        prompt = f"""You are a medical expert evaluating a patient for disc herniation surgery.
        Analyze the following patient data and provide your expert opinion, considering both conservative and surgical approaches.
        Return ONLY a JSON response without any additional text.
        Your recommendation MUST be either "surgery" or "no_surgery" (no other values allowed).

        Patient Data:
        - Age: {patient_data['age']}
        - Pain Level (1-10): {patient_data['pain_level']}
        - Duration of Symptoms: {patient_data['symptom_duration']}
        - Previous Treatments: {patient_data['previous_treatments']}
        - MRI Findings: {patient_data['mri_findings']}
        - Neurological Symptoms: {patient_data['neurological_symptoms']}

        Consider factors like:
        - Severity of symptoms
        - Response to conservative treatment
        - Risk factors
        - Long-term prognosis
        - Patient age and health status

        Format your response exactly like this, replacing the example values:
        {{
            "recommendation": "no_surgery",
            "confidence": 0.85,
            "reasoning": [
                "Persistent high pain level",
                "Failed conservative treatment",
                "Clear nerve root compression"
            ],
            "risks": [
                "Infection risk",
                "Anesthesia complications",
                "Potential nerve damage"
            ],
            "benefits": [
                "Pain relief",
                "Improved mobility",
                "Prevent further nerve damage"
            ]
        }}"""
        
        response = model.generate_content(prompt)
        try:
            # Extract JSON from response if there's additional text
            text = response.text
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = text[start:end]
                result = json.loads(json_str)
                # Validate recommendation value
                if result['recommendation'] not in ['surgery', 'no_surgery']:
                    result['recommendation'] = 'no_surgery'  # default to conservative approach
                return result
            raise json.JSONDecodeError("No JSON found", text, 0)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing response: {str(e)}")
            print(f"Raw response: {text}")
            return {
                "recommendation": "no_surgery",  # default to conservative approach
                "confidence": 0.5,
                "reasoning": ["Failed to parse model response"],
                "risks": [],
                "benefits": []
            }

    async def aggregate_votes(self, votes: List[Dict]) -> Dict:
        """Aggregate multiple votes into a final decision"""
        # Count recommendations
        surgery_votes = sum(1 for v in votes if v['recommendation'] == 'surgery')
        no_surgery_votes = sum(1 for v in votes if v['recommendation'] == 'no_surgery')
        
        # Calculate average confidence
        confidences = [v['confidence'] for v in votes]
        avg_confidence = sum(confidences) / len(confidences)
        
        # Aggregate unique reasons
        all_reasoning = set()
        all_risks = set()
        all_benefits = set()
        
        for vote in votes:
            all_reasoning.update(vote.get('reasoning', []))
            all_risks.update(vote.get('risks', []))
            all_benefits.update(vote.get('benefits', []))
        
        final_recommendation = 'surgery' if surgery_votes > no_surgery_votes else 'no_surgery'
        
        return {
            "final_recommendation": final_recommendation,
            "vote_distribution": {
                "surgery": surgery_votes,
                "no_surgery": no_surgery_votes
            },
            "confidence": avg_confidence,
            "consolidated_reasoning": list(all_reasoning),
            "consolidated_risks": list(all_risks),
            "consolidated_benefits": list(all_benefits),
            "unanimous": surgery_votes == len(votes) or no_surgery_votes == len(votes)
        }

    async def get_surgery_recommendation(self, patient_data: Dict) -> Dict:
        """Get parallel votes and aggregate them"""
        # Get votes in parallel
        votes = await asyncio.gather(*[
            self.get_vote(model, patient_data)
            for model in self.models
        ])
        
        # Print individual votes for debugging
        print("\nIndividual Model Votes:")
        for i, vote in enumerate(votes, 1):
            print(f"\nModel {i} Vote:")
            print(f"Recommendation: {vote['recommendation']}")
            print(f"Confidence: {vote['confidence']}")
            print(f"Reasoning: {vote['reasoning']}")
        
        # Aggregate results
        final_decision = await self.aggregate_votes(votes)
        
        return {
            "individual_votes": votes,
            "aggregated_decision": final_decision,
            "timestamp": datetime.now().isoformat()
        }

# Example usage
async def main():
    patient_data = {
        "age": 23,
        "pain_level": 3,
        "symptom_duration": "1 month",
        "previous_treatments": [
            "Physical therapy",
            # "Pain medication",
            # "Epidural injections"
        ],
        "mri_findings": "L4-L5 disc herniation with nerve root compression",
        "neurological_symptoms": [
            "Leg weakness",
            "Sore back",
            # "Numbness in foot",
            # "Reduced reflexes"
        ]
    }
    
    voting_system = SurgeryVotingSystem()
    result = await voting_system.get_surgery_recommendation(patient_data)
    
    # Print results
    print("\n=== Surgery Recommendation Results ===")
    print(f"\nFinal Recommendation: {result['aggregated_decision']['final_recommendation'].upper()}")
    print(f"Confidence: {result['aggregated_decision']['confidence']:.2f}")
    print(f"Vote Distribution: {result['aggregated_decision']['vote_distribution']}")
    print("\nConsolidated Reasoning:")
    for reason in result['aggregated_decision']['consolidated_reasoning']:
        print(f"- {reason}")
    
    if not result['aggregated_decision']['unanimous']:
        print("\nNote: Decision was not unanimous among models")

if __name__ == "__main__":
    asyncio.run(main())
