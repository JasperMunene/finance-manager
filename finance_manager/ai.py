import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure the API key
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')


def categorize_transaction(description):
    prompt = f"Categorize the following transaction description into a standard financial category (e.g., Food, Utilities, Entertainment, etc.):\n\"{description}\""

    try:
        # Generate content using the model
        response = model.generate_content([prompt])

        # Access the generated response text (assuming 'content' is the correct field)
        category_name = response.candidates[0].content

        print(category_name)
        return category_name
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
    Analyze the following financial transactions and provide actionable advice to improve savings and manage expenses:

    {summary}

    Provide your advice in bullet points.
    """

    try:
        # Generate content using the model
        response = model.generate_content([prompt])

        # Access the generated response text (assuming 'content' is the correct field)
        advice = response.candidates[0].content
        return advice
    except Exception as e:
        print(f"Error generating financial advice: {e}")
        return "No advice available at the moment."



