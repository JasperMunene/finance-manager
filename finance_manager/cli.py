import click
from passlib.hash import bcrypt
from sqlalchemy.exc import IntegrityError
from finance_manager.database import init_db, SessionLocal
from finance_manager.models import User, Transaction, Category, Budget
from finance_manager.ai import categorize_transaction, generate_financial_advice, simulate_financial_scenario
import os
import json
from sqlalchemy import func
from tabulate import tabulate



# Initialize the database
init_db()

# Define the path for storing the logged-in user's email
SESSION_FILE = './user.txt'

def get_logged_in_user():
    """Retrieve the logged-in user's email from the session file."""
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, 'r') as f:
            return f.read().strip()
    return None

def set_logged_in_user(email):
    """Store the logged-in user's email in the session file."""
    with open(SESSION_FILE, 'w') as f:
        f.write(email)

def remove_logged_in_user():
    """Remove the logged-in user's email and delete the session file."""
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

@click.group()
def cli():
    """Finance Manager CLI"""
    pass

@cli.command()
@click.option('--name', prompt='Your name', help='Name of the user.')
@click.option('--email', prompt='Your email', help='Email of the user.')
@click.option('--password', prompt='Your password', hide_input=True, confirmation_prompt=True, help='Password of the user.')
def signup(name, email, password):
    """Register a new user."""
    db = SessionLocal()
    try:
        hashed_password = bcrypt.hash(password)
        user = User(name=name, email=email, password_hash=hashed_password)
        db.add(user)
        db.commit()
        set_logged_in_user(email)  # Save email to session file after successful signup
        click.echo(f"User registered and logged in successfully as {name}!")
    except IntegrityError:
        db.rollback()
        click.echo("Email already exists. Please try a different email.")
    finally:
        db.close()

@cli.command()
@click.option('--email', prompt='Your email', help='Email of the user.')
@click.option('--password', prompt='Your password', hide_input=True, help='Password of the user.')
def login(email, password):
    """Log in as a user."""
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if user and bcrypt.verify(password, user.password_hash):
        set_logged_in_user(email)  # Store the email of the logged-in user
        click.echo(f"Welcome back, {user.name}!")
    else:
        click.echo("Invalid email or password.")
    db.close()


@cli.command()
@click.option('--description', prompt='Transaction description', help='Description of the transaction.')
@click.option('--amount', prompt='Transaction amount', type=float, help='Amount of the transaction.')
@click.option('--type', prompt='Transaction type (income/expense)', type=click.Choice(['income', 'expense']), help='Type of the transaction.')
def add_transaction(description, amount, type):
    """Add a new transaction for the currently logged-in user and track budget usage."""
    email = get_logged_in_user()
    if not email:
        click.echo("You must be logged in to add a transaction.")
        return

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            click.echo("User not found.")
            return

        # Categorize the transaction
        response = categorize_transaction(description)
        try:
            result = json.loads(response.text)
            transaction_category = result.get("category")
        except (json.JSONDecodeError, AttributeError):
            click.echo("Error categorizing the transaction.")
            return

        if not transaction_category:
            click.echo("Unable to determine the transaction category.")
            return

        # Fetch or create the category
        category = db.query(Category).filter(Category.name == transaction_category).first()
        if not category:
            category = Category(name=transaction_category)
            db.add(category)
            db.commit()
            db.refresh(category)

        # Add the transaction
        transaction = Transaction(user_id=user.id, category_id=category.id, amount=amount, type=type)
        db.add(transaction)
        db.commit()
        click.echo(f"Transaction added under category: {transaction_category}")

        # Check against budget
        if type == 'expense':
            budget = db.query(Budget).filter(Budget.category_id == category.id, Budget.user_id == user.id).first()
            if budget:
                # Calculate total spending for the category
                total_spent = db.query(Transaction).filter(
                    Transaction.user_id == user.id,
                    Transaction.category_id == category.id,
                    Transaction.type == 'expense'
                ).with_entities(func.sum(Transaction.amount)).scalar() or 0.0

                # Compare total spent to budget
                remaining_budget = budget.amount - total_spent
                if remaining_budget < 0:
                    click.echo(f"Alert: You have exceeded your budget for '{transaction_category}' by Ksh {abs(remaining_budget):.2f}!")
                else:
                    click.echo(f"Remaining budget for '{transaction_category}': Ksh {remaining_budget:.2f}")

    except Exception as e:
        click.echo(f"An error occurred: {e}")
    finally:
        db.close()




@cli.command()
def advice():
    """Provide financial advice based on the user's transactions."""
    email = get_logged_in_user()
    if not email:
        click.echo("You must be logged in to get financial advice.")
        return

    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        click.echo("User not found. Please register first.")
        db.close()
        return

    transactions = db.query(Transaction).filter(Transaction.user_id == user.id).all()
    if not transactions:
        click.echo("No transactions found.")
        db.close()
        return

    formatted_transactions = [
        {
            'type': txn.type,
            'amount': txn.amount,
            'category': db.query(Category).filter(Category.id == txn.category_id).first().name
        }
        for txn in transactions
    ]

    response = generate_financial_advice(formatted_transactions)
    result = json.loads(response.text)
    analysis = result.get("analysis", "No analysis found.")
    advice = result.get("advice", [])
    click.echo("Financial Analysis:")
    click.echo(analysis)
    click.echo("Advice:")
    for tip in advice:
        click.echo(f"- {tip}")

    db.close()

@cli.command()
@click.option('--category', prompt='Category name', help='Name of the category to set a budget for.')
@click.option('--amount', prompt='Budget amount', type=float, help='Budget amount in Ksh.')
def set_budget(category, amount):
    """Set a budget for a specific category."""
    email = get_logged_in_user()
    if not email:
        click.echo("You must be logged in to set a budget.")
        return

    db = SessionLocal()
    try:
        # Get the user from the database
        user = db.query(User).filter(User.email == email).first()
        if not user:
            click.echo("User not found. Please register first.")
            return

        # Check if the category exists
        category_obj = db.query(Category).filter(Category.name == category).first()
        if not category_obj:
            click.echo(f"Category '{category}' not found. Please add the category first.")
            return

        # Check if a budget already exists for this category
        existing_budget = db.query(Budget).filter(Budget.category_id == category_obj.id, Budget.user_id == user.id).first()
        if existing_budget:
            click.echo(f"A budget for '{category}' already exists. Updating the amount.")
            existing_budget.amount = amount
        else:
            # Create a new budget record
            new_budget = Budget(user_id=user.id, category_id=category_obj.id, amount=amount)
            db.add(new_budget)

        db.commit()
        click.echo(f"Budget of Ksh {amount} has been set for {category}")

    except Exception as e:
        click.echo(f"An error occurred: {e}")
    finally:
        db.close()



@cli.command()
@click.option('--name', prompt='Category name', help='The name of the category to add.')
def add_category(name):
    """Add a new category to the finance manager."""
    email = get_logged_in_user()
    if not email:
        click.echo("You must be logged in to add a category.")
        return

    db = SessionLocal()
    try:
        # Check if the category already exists
        existing_category = db.query(Category).filter(Category.name == name).first()
        if existing_category:
            click.echo(f"Category '{name}' already exists.")
            return

        # Create a new category without a budget
        new_category = Category(name=name)
        db.add(new_category)
        db.commit()
        db.refresh(new_category)
        click.echo(f"Category '{name}' added successfully!")

    except Exception as e:
        click.echo(f"An error occurred: {e}")
    finally:
        db.close()

@cli.command()
@click.option('--scenario', prompt='Scenario', help='The scenario to simulate.')
def simulate_scenario(scenario):
    """Simulate a scenario based on transaction history."""
    email = get_logged_in_user()
    if not email:
        click.echo("You must be logged in to simulate scenarios.")
        return

    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        click.echo("User not found. Please register first.")
        db.close()
        return

    transactions = db.query(Transaction).filter(Transaction.user_id == user.id).all()
    if not transactions:
        click.echo("No transactions found.")
        db.close()
        return

    formatted_transactions = [
        {
            'type': txn.type,
            'amount': txn.amount,
            'category': db.query(Category).filter(Category.id == txn.category_id).first().name
        }
        for txn in transactions
    ]

    response = simulate_financial_scenario(formatted_transactions, scenario)
    result = json.loads(response.text)
    analysis = result.get("analysis", "No analysis found.")
    impact = result.get("impact", "No impact found.")

    click.echo("Analysis: ")
    click.echo(analysis)

    click.echo("Impact: ")
    click.echo(impact)


    db.close()

@cli.command()
def transactions():
    """Display all transactions for the currently logged-in user."""
    email = get_logged_in_user()
    if not email:
        click.echo("You must be logged in to view transactions.")
        return

    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        click.echo("User not found. Please register first.")
        db.close()
        return

    # Fetch all transactions for the logged-in user
    transactions = db.query(Transaction).filter(Transaction.user_id == user.id).all()
    if not transactions:
        click.echo("No transactions found.")
        db.close()
        return

    # Prepare data for the table
    table_data = []
    for txn in transactions:
        category_name = db.query(Category).filter(Category.id == txn.category_id).first().name
        table_data.append([txn.timestamp.strftime('%Y-%m-%d %H:%M:%S'), txn.type, txn.amount, category_name])

    # Define the table headers
    headers = ["Date", "Type", "Amount (Ksh)", "Category"]

    # Display the table using tabulate
    click.echo(tabulate(table_data, headers, tablefmt="grid"))

    db.close()

@cli.command()
def budgets():
    """Display all budgets for the currently logged-in user."""
    email = get_logged_in_user()
    if not email:
        click.echo("You must be logged in to view budgets.")
        return

    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        click.echo("User not found. Please register first.")
        db.close()
        return

    # Fetch all budgets for the logged-in user
    budgets = db.query(Budget).filter(Budget.user_id == user.id).all()
    if not budgets:
        click.echo("No budgets found.")
        db.close()
        return

    # Prepare data for the table
    table_data = []
    for budget in budgets:
        category_name = db.query(Category).filter(Category.id == budget.category_id).first().name
        table_data.append([category_name, budget.amount])

    # Define the table headers
    headers = ["Category", "Budget Amount (Ksh)"]

    # Display the table using tabulate
    click.echo(tabulate(table_data, headers, tablefmt="grid"))

    db.close()


@cli.command()
def categories():
    """Display all categories in the system."""
    db = SessionLocal()

    # Fetch all categories
    categories = db.query(Category).all()
    if not categories:
        click.echo("No categories found.")
        db.close()
        return

    # Prepare data for the table
    table_data = []
    for category in categories:
        table_data.append([category.name])

    # Define the table headers
    headers = ["Category Name"]

    # Display the table using tabulate
    click.echo(tabulate(table_data, headers, tablefmt="grid"))

    db.close()

@cli.command()
def delete_transactions():
    """Delete all transactions for the currently logged-in user."""
    email = get_logged_in_user()
    if not email:
        click.echo("You must be logged in to delete transactions.")
        return

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            click.echo("User not found.")
            return

        # Delete all transactions for the user
        db.query(Transaction).filter(Transaction.user_id == user.id).delete()
        db.commit()

        click.echo("All transactions have been deleted successfully.")
    except Exception as e:
        db.rollback()
        click.echo(f"An error occurred: {e}")
    finally:
        db.close()



@cli.command()
def logout():
    """Log out the current user"""
    email = get_logged_in_user()
    if not email:
        click.echo("You are not logged in.")
        return

    remove_logged_in_user()  # Delete the session file
    click.echo(f"You have been logged out, {email}.")


if __name__ == '__main__':
    cli()
