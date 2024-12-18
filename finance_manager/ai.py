import os

from click import prompt
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure the API key
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')


def categorize_transaction(description):
    prompt = f"Categorize the following transaction description into a standard financial category (e.g., Food, Utilities, Entertainment, etc.)."

    try:
        return model.generate_content([prompt, description],
                                      generation_config=genai.GenerationConfig(
                                          response_mime_type="application/json"
                                      )
                                      )
    except Exception as e:
        print(f"Error categorizing transaction: {e}")
        return "Uncategorized"


def generate_financial_advice(transactions):
    # Summarize the transactions
    summary = "\n".join([
        f"{txn['type'].capitalize()}: {txn['amount']} in {txn['category']}"
        for txn in transactions
    ])

    # Create the prompt for generating advice
    prompt = f"""
        Analyze the following financial transactions (all amounts are in Kenyan Shillings, Ksh) and provide actionable advice to improve savings and manage expenses:
        Provide your advice in bullet points.
        """

    try:
        return model.generate_content([prompt, summary],
                                      generation_config=genai.GenerationConfig(
                                          response_mime_type="application/json"
                                      )
                                      )
    except Exception as e:
        print(f"Error generating financial advice: {e}")
        return "No advice available at the moment."

def simulate_financial_scenario(transactions, scenario):
    summary = "\n".join([
        f"{txn['type'].capitalize()}: {txn['amount']} in {txn['category']}"
        for txn in transactions
    ])

    prompt = f"""
    Given the following transactions: {summary} (all amounts are in Kenyan Shillings, Ksh), analyze the financial impact of the scenario below:
    {scenario}
    Provide a detailed and clear description of the impact.
    Please generate a financial report in the following format:
    {{
        'analysis': '',
        'impact': '',
    }}
    """

    try:
        return model.generate_content([prompt],
                                      generation_config=genai.GenerationConfig(
                                          response_mime_type="application/json"
                                      ))
    except Exception as e:
        print(f"Error suggesting budget adjustments: {e}")
        return "No budget suggestions available."

