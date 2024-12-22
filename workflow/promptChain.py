import google.generativeai as genai
from typing import Dict, List
import json
from datetime import datetime
from dotenv import load_dotenv
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
console = Console()

def format_requirements(requirements: Dict) -> None:
    """Format and display nutritional requirements"""
    console.print("\n[bold cyan]🎯 Daily Nutritional Requirements[/bold cyan]", style="bold")
    
    # Main requirements table
    table = Table(box=box.HEAVY_EDGE, show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan", justify="right")
    table.add_column("Value", style="green", justify="left")
    
    table.add_row("Daily Calories", f"{requirements['daily_calories']} kcal")
    
    # Macros section
    table.add_section()
    table.add_row("[yellow]Protein[/yellow]", f"{requirements['macronutrient_split']['protein']}g")
    table.add_row("[yellow]Carbs[/yellow]", f"{requirements['macronutrient_split']['carbs']}g")
    table.add_row("[yellow]Fats[/yellow]", f"{requirements['macronutrient_split']['fats']}g")
    
    # Additional info
    table.add_section()
    table.add_row("Meal Frequency", f"{requirements['meal_frequency']} meals/day")
    table.add_row("Key Nutrients", ", ".join(requirements['micronutrient_focus']))
    
    console.print(Panel(table, title="[bold]Nutritional Breakdown[/bold]", border_style="cyan"))
    
    if requirements.get('dietary_considerations'):
        considerations = "\n".join(f"• {consideration}" for consideration in requirements['dietary_considerations'])
        console.print(Panel(considerations, title="[bold]Dietary Considerations[/bold]", 
                          border_style="yellow", title_align="left"))

def format_meal_structure(structure: Dict) -> None:
    """Format and display meal structure"""
    console.print("\n[bold cyan]🍽️ Daily Meal Schedule[/bold cyan]", style="bold")
    
    grid_items = []
    for meal in structure['meals']:
        content = [
            f"[bold green]⏰ Time:[/bold green] {meal['timing']}",
            f"[bold yellow]🔥 Calories:[/bold yellow] {meal['calorie_allocation']} kcal",
            "\n[bold cyan]Macronutrients:[/bold cyan]",
            f"🥩 Protein: {meal['macro_allocation']['protein']}g",
            f"🌾 Carbs: {meal['macro_allocation']['carbs']}g",
            f"🥑 Fats: {meal['macro_allocation']['fats']}g",
            "\n[bold magenta]Suggested Foods:[/bold magenta]"
        ]
        content.extend(f"• {food}" for food in meal.get('example_foods', []))
        
        panel = Panel(
            "\n".join(content),
            title=f"[bold]{meal['meal_name']}[/bold]",
            border_style="cyan",
            box=box.HEAVY_EDGE
        )
        console.print(panel)
        console.print()  # Add spacing between meals

def format_meal_options(meal_options: Dict) -> None:
    """Format and display meal options"""
    console.print("\n[bold cyan]🍳 Meal Options & Recipes[/bold cyan]", style="bold")
    
    try:
        for meal_period in meal_options.get("meal_options", []):
            meal_name = meal_period.get("meal_name", "Meal")
            console.print(f"\n[bold magenta]📍 {meal_name}[/bold magenta]")
            
            for option in meal_period.get("options", []):
                # Create a nested table for nutritional info
                nutrition_table = Table(box=box.SIMPLE, show_header=False)
                nutrition_table.add_column("Metric", style="yellow")
                nutrition_table.add_column("Value", style="green")
                
                calories = option.get("calories", 0)
                macros = option.get("macronutrients", {})
                
                nutrition_table.add_row("Calories", f"{calories} kcal")
                nutrition_table.add_row("Protein", f"{macros.get('protein', 0)}g")
                nutrition_table.add_row("Carbs", f"{macros.get('carbs', 0)}g")
                nutrition_table.add_row("Fats", f"{macros.get('fats', 0)}g")
                
                content = [
                    "[bold yellow]📝 Ingredients:[/bold yellow]",
                    *[f"• {ingredient}" for ingredient in option.get("ingredients", [])],
                    f"\n[bold green]⏱️ Prep Time:[/bold green] {option.get('preparation_time', 'N/A')}",
                    "\n[bold cyan]👩‍🍳 Instructions:[/bold cyan]",
                    *[f"{i+1}. {instruction}" for i, instruction in enumerate(option.get("cooking_instructions", []))],
                    "\n[bold magenta]📊 Nutrition Facts:[/bold magenta]",
                    nutrition_table
                ]
                
                panel = Panel(
                    "\n".join(str(item) for item in content),
                    title=f"[bold]{option.get('name', 'Meal Option')}[/bold]",
                    border_style="cyan",
                    box=box.HEAVY_EDGE
                )
                console.print(panel)
                console.print()  # Add spacing between options
    except Exception as e:
        console.print(f"[bold red]Error formatting meal options:[/bold red] {str(e)}")

def format_shopping_list(shopping_list: Dict) -> None:
    """Format and display shopping list"""
    console.print("\n[bold cyan]🛒 Shopping List[/bold cyan]", style="bold")
    
    total_cost = 0
    for category in shopping_list['shopping_list']:
        console.print(f"\n[bold magenta]📦 {category['category']}[/bold magenta]")
        
        table = Table(box=box.HEAVY_EDGE, show_header=True, header_style="bold cyan")
        table.add_column("Item", style="green")
        table.add_column("Quantity", style="yellow", justify="center")
        table.add_column("Est. Cost", style="cyan", justify="right")
        table.add_column("Alternatives", style="magenta")
        
        category_cost = 0
        for item in category['items']:
            cost = item['estimated_cost']
            category_cost += cost
            table.add_row(
                item['name'],
                str(item['quantity']),
                f"${cost:.2f}",
                ", ".join(item.get('alternatives', []) or ["—"])
            )
        
        total_cost += category_cost
        table.add_section()
        table.add_row(
            "[bold]Category Total[/bold]",
            "",
            f"[bold]${category_cost:.2f}[/bold]",
            ""
        )
        
        console.print(table)
    
    console.print(Panel(
        f"[bold green]Total Estimated Cost: ${total_cost:.2f}[/bold green]",
        border_style="cyan",
        box=box.HEAVY_EDGE
    ))

class MealPlanChain:
    def __init__(self, api_key: str = GEMINI_API_KEY, model: str = "gemini-1.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.history = []

    def _log_step(self, step_name: str, prompt: str, response: str):
        """Log each step of the chain for tracking"""
        self.history.append({
            "step": step_name,
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response": response
        })

    async def analyze_requirements(self, user_input: Dict) -> Dict:
        """Step 1: Analyze user requirements and calculate nutritional needs"""
        prompt = """
        Based on these user details, calculate daily nutritional requirements:
        - Age: {age}
        - Weight: {weight}
        - Height: {height}
        - Activity Level: {activity_level}
        - Dietary Restrictions: {restrictions}
        - Goals: {goals}
        - Health Conditions: {health_conditions}

        Return a JSON object with these exact fields:
        {{
            "daily_calories": 2000,
            "macronutrient_split": {{
                "protein": 150,
                "carbs": 200,
                "fats": 70
            }},
            "micronutrient_focus": ["vitamin_a", "vitamin_d"],
            "meal_frequency": 3,
            "dietary_considerations": ["consideration1", "consideration2"]
        }}

        Follow this exact format but replace the values appropriately.
        """.format(**user_input)
        
        response = self.model.generate_content(prompt)
        try:
            result = json.loads(response.text)
        except json.JSONDecodeError:
            text = response.text
            try:
                json_str = text[text.find('{'):text.rfind('}')+1]
                result = json.loads(json_str)
            except (json.JSONDecodeError, ValueError):
                result = {
                    "daily_calories": 2000,
                    "macronutrient_split": {"protein": 150, "carbs": 200, "fats": 67},
                    "micronutrient_focus": ["Vitamin D", "Iron"],
                    "meal_frequency": 3,
                    "dietary_considerations": user_input.get('restrictions', [])
                }
        
        self._log_step("requirements_analysis", prompt, result)
        return result

    async def create_meal_structure(self, requirements: Dict) -> Dict:
        """Step 2: Create meal structure and timing"""
        prompt = """
        Create a daily meal structure based on:
        - Daily Calories: {daily_calories}
        - Meal Frequency: {meal_frequency}
        - Macros: {macronutrient_split}
        - Dietary Considerations: {dietary_considerations}

        Return a JSON object in this exact format:
        {{
            "meals": [
                {{
                    "meal_name": "Breakfast",
                    "timing": "08:00",
                    "calorie_allocation": 500,
                    "macro_allocation": {{
                        "protein": 30,
                        "carbs": 60,
                        "fats": 20
                    }}
                }}
            ]
        }}

        Follow this format but adjust values and add more meals as needed.
        """.format(**requirements)

        response = self.model.generate_content(prompt)
        try:
            result = json.loads(response.text)
        except json.JSONDecodeError:
            text = response.text
            try:
                json_str = text[text.find('{'):text.rfind('}')+1]
                result = json.loads(json_str)
            except (json.JSONDecodeError, ValueError):
                result = {
                    "meals": [
                        {
                            "meal_name": "Default Meal",
                            "timing": "12:00",
                            "calorie_allocation": requirements['daily_calories'] / requirements['meal_frequency'],
                            "macro_allocation": requirements['macronutrient_split']
                        }
                    ]
                }
        
        self._log_step("meal_structure", prompt, result)
        return result

    async def generate_meal_options(self, 
                                 structure: Dict, 
                                 restrictions: List[str]) -> Dict:
        """Step 3: Generate specific meal options"""
        meals_str = json.dumps(structure["meals"], indent=2)
        restrictions_str = json.dumps(restrictions)
        
        prompt = f"""
        Generate meal options for each meal period considering:
        Meal Structure: {meals_str}
        Dietary Restrictions: {restrictions_str}

        Return a JSON object in this exact format:
        {{
            "meal_options": [
                {{
                    "meal_name": "Breakfast",
                    "options": [
                        {{
                            "name": "Oatmeal Bowl",
                            "ingredients": ["oats", "banana", "honey"],
                            "preparation_time": "15 minutes",
                            "cooking_instructions": ["Boil water", "Add oats", "Top with fruits"],
                            "macronutrients": {{
                                "protein": 15,
                                "carbs": 45,
                                "fats": 8
                            }},
                            "calories": 350
                        }}
                    ]
                }}
            ]
        }}

        Create 2-3 options for each meal period in the meal structure, ensuring they match the calorie and macro requirements.
        """

        response = self.model.generate_content(prompt)
        try:
            result = json.loads(response.text)
        except json.JSONDecodeError:
            text = response.text
            try:
                json_str = text[text.find('{'):text.rfind('}')+1]
                result = json.loads(json_str)
            except (json.JSONDecodeError, ValueError):
                # Create a default meal option for each meal in the structure
                result = {
                    "meal_options": [
                        {
                            "meal_name": meal["meal_name"],
                            "options": [
                                {
                                    "name": f"Default {meal['meal_name']} Option",
                                    "ingredients": ["protein source", "vegetables", "grains"],
                                    "preparation_time": "30 minutes",
                                    "cooking_instructions": ["Prepare ingredients", "Cook according to preferences", "Serve hot"],
                                    "macronutrients": meal["macro_allocation"],
                                    "calories": meal["calorie_allocation"]
                                }
                            ]
                        }
                        for meal in structure["meals"]
                    ]
                }
        
        self._log_step("meal_options", prompt, result)
        return result

    async def create_shopping_list(self, meal_plan: Dict) -> Dict:
        """Step 4: Generate shopping list"""
        meal_options_str = json.dumps(meal_plan["meal_options"], indent=2)
        
        prompt = f"""
        Create a consolidated shopping list from these meals:
        {meal_options_str}

        Return a JSON object in this exact format:
        {{
            "shopping_list": [
                {{
                    "category": "Produce",
                    "items": [
                        {{
                            "name": "Banana",
                            "quantity": "6 pieces",
                            "estimated_cost": 3.99,
                            "alternatives": ["Apple", "Pear"]
                        }}
                    ]
                }}
            ]
        }}

        Follow this format but create appropriate categories and items based on the meals.
        """

        response = self.model.generate_content(prompt)
        try:
            result = json.loads(response.text)
        except json.JSONDecodeError:
            text = response.text
            try:
                json_str = text[text.find('{'):text.rfind('}')+1]
                result = json.loads(json_str)
            except (json.JSONDecodeError, ValueError):
                result = {
                    "shopping_list": [
                        {
                            "category": "Basic Ingredients",
                            "items": [
                                {
                                    "name": "Default Item",
                                    "quantity": "1 unit",
                                    "estimated_cost": 5.00,
                                    "alternatives": ["Alternative 1"]
                                }
                            ]
                        }
                    ]
                }
        
        self._log_step("shopping_list", prompt, result)
        return result

async def generate_meal_plan(user_input: Dict):
    """Main function to run the meal planning chain"""
    try:
        chain = MealPlanChain()
        
        # Step 1: Analyze Requirements
        requirements = await chain.analyze_requirements(user_input)
        print("✓ Requirements analyzed")
        format_requirements(requirements)

        # Step 2: Create Meal Structure
        structure = await chain.create_meal_structure(requirements)
        print("✓ Meal structure created")
        format_meal_structure(structure)

        # Step 3: Generate Meal Options
        meal_options = await chain.generate_meal_options(
            structure,
            user_input.get('restrictions', [])
        )
        print("✓ Meal options generated")
        format_meal_options(meal_options)

        # Step 4: Create Shopping List
        shopping_list = await chain.create_shopping_list(meal_options)
        print("✓ Shopping list created")
        format_shopping_list(shopping_list)

        return {
            "requirements": requirements,
            "meal_structure": structure,
            "meal_options": meal_options,
            "shopping_list": shopping_list,
            "chain_history": chain.history
        }

    except Exception as e:
        console.print(f"[bold red]Error in meal plan generation:[/bold red] {str(e)}")
        return None

# Example Usage
user_input = {
    "age": 23,
    "weight": "150lbs",
    "height": "5'10",
    "activity_level": "moderate",
    "restrictions": ["No oatmeal, no highlyprocessed foods"],
    "goals": "build muscle",
    "health_conditions": ["none"]
}

async def main():
    # Run the chain
    meal_plan = await generate_meal_plan(user_input)
    return meal_plan

if __name__ == "__main__":
    import asyncio
    meal_plan = asyncio.run(main())
    #print(meal_plan)