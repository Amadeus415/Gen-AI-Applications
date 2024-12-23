import google.generativeai as genai
from typing import Dict, List, Any
import json
from datetime import datetime
from dotenv import load_dotenv
import os
import asyncio
import aiohttp

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
SERP_API_KEY = os.getenv('SERP_API_KEY')

#    Search Topic -> Generate 3 Queries -> Execute 3 Searches -> Aggregate Results -> Display Results

class SimpleSearchOrchestrator:
    """Simple orchestrator that handles 3 search queries and aggregates results"""
    
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.history = []

    def _log_action(self, action: str, details: Dict):
        """Log orchestrator actions"""
        self.history.append({
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "details": details
        })

    async def generate_queries(self, topic: str) -> List[str]:
        """Generate 3 search queries for the topic"""
        prompt = f"""Generate exactly 3 different search queries to research this topic: "{topic}"
        
        Make the queries specific and diverse to cover:
        1. Latest developments
        2. Real-world applications
        3. Future potential
        
        Return ONLY a JSON array of 3 queries like this:
        ["query1", "query2", "query3"]
        """
        
        response = self.model.generate_content(prompt)
        try:
            # Extract JSON from response
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            queries = json.loads(response_text)
            self._log_action("query_generation", {
                "topic": topic,
                "queries": queries
            })
            return queries[:3]  # Ensure we only get 3 queries
        except json.JSONDecodeError:
            print(f"Failed to parse queries. Response: {response_text}")
            # Return default queries
            return [
                f"{topic} latest developments",
                f"{topic} real world applications",
                f"{topic} future potential"
            ]

    async def search_google(self, query: str) -> Dict:
        """Perform a single Google search"""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "api_key": SERP_API_KEY,
                    "q": query,
                    "num": 3  # Get 3 results per query
                }
                async with session.get("https://serpapi.com/search", params=params) as response:
                    data = await response.json()
                    results = data.get("organic_results", [])
                    self._log_action("search_execution", {
                        "query": query,
                        "results_count": len(results)
                    })
                    return {
                        "query": query,
                        "results": results
                    }
        except Exception as e:
            print(f"Search failed for query '{query}': {str(e)}")
            return {
                "query": query,
                "error": f"Search failed: {str(e)}"
            }

    async def aggregate_results(self, search_results: List[Dict], topic: str) -> Dict:
        """Aggregate and synthesize search results"""
        # Format results for the model
        formatted_results = []
        for result in search_results:
            if "error" not in result:
                for r in result["results"]:
                    formatted_results.append({
                        "query": result["query"],
                        "title": r.get("title", "No title"),
                        "snippet": r.get("snippet", "No snippet"),
                        "url": r.get("link", "No link")
                    })

        prompt = f"""Analyze and synthesize these search results about: "{topic}"

Search Results:
{json.dumps(formatted_results, indent=2)}

Create a comprehensive summary that includes:
1. Key findings and breakthroughs
2. Current applications
3. Future implications

Return ONLY a JSON object in this format:
{{
    "key_findings": [<list of main findings>],
    "current_applications": [<list of current uses>],
    "future_implications": [<list of potential impacts>],
    "sources": [<list of most relevant source URLs>]
}}"""

        response = self.model.generate_content(prompt)
        try:
            # Extract JSON from response
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            synthesis = json.loads(response_text)
            self._log_action("result_synthesis", {
                "topic": topic,
                "synthesis": synthesis
            })
            return synthesis
        except json.JSONDecodeError:
            print(f"Failed to parse synthesis. Response: {response_text}")
            return {
                "error": "Failed to synthesize results",
                "raw_response": response_text
            }

    async def research_topic(self, topic: str) -> Dict:
        """Main method to research a topic"""
        # 1. Generate search queries
        queries = await self.generate_queries(topic)
        
        # 2. Execute searches in parallel
        search_results = await asyncio.gather(*[
            self.search_google(query) for query in queries
        ])
        
        # 3. Aggregate and synthesize results
        synthesis = await self.aggregate_results(search_results, topic)
        
        return {
            "topic": topic,
            "queries": queries,
            "synthesis": synthesis,
            "raw_results": search_results,
            "timestamp": datetime.now().isoformat()
        }

# Example usage
async def main():
    try:
        orchestrator = SimpleSearchOrchestrator()
        
        # Example research topic
        topic = "Latest advancements in quantum computing"
        
        print(f"🔍 Researching: {topic}")
        print("\nGenerating queries and searching...")
        
        result = await orchestrator.research_topic(topic)
        
        # Print synthesized results
        print("\n=== Research Summary ===")
        synthesis = result["synthesis"]
        
        if "error" in synthesis:
            print(f"\nError in synthesis: {synthesis['error']}")
            print("\nRaw search results:")
            for i, search_result in enumerate(result["raw_results"], 1):
                print(f"\nQuery {i}: {search_result['query']}")
                if "error" in search_result:
                    print(f"Error: {search_result['error']}")
                    continue
                    
                print("\nTop 3 Results:")
                for j, res in enumerate(search_result["results"], 1):
                    print(f"\n{j}. {res.get('title', 'No title')}")
                    print(f"   {res.get('snippet', 'No snippet')}")
                    print(f"   URL: {res.get('link', 'No link')}")
        else:
            print("\nKey Findings:")
            for finding in synthesis["key_findings"]:
                print(f"• {finding}")
            
            print("\nCurrent Applications:")
            for app in synthesis["current_applications"]:
                print(f"• {app}")
            
            print("\nFuture Implications:")
            for impl in synthesis["future_implications"]:
                print(f"• {impl}")
            
            print("\nKey Sources:")
            for source in synthesis["sources"]:
                print(f"• {source}")
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
