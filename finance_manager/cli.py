

import click
from passlib.hash import bcrypt
from sqlalchemy.exc import IntegrityError
from finance_manager.database import init_db, get_db, SessionLocal
from finance_manager.models import User, Transaction, Category
from finance_manager.ai import categorize_transaction, generate_financial_advice
import os
import json

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
    """Add a new transaction for the currently logged-in user."""
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

    except Exception as e:
        click.echo(f"An error occurred: {e}")
    finally:
        db.close()



@cli.command()
def advice(email):
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
def logout():
    """Log out the current user by removing their email from the session file and deleting the file."""
    email = get_logged_in_user()
    if not email:
        click.echo("You are not logged in.")
        return

    remove_logged_in_user()  # Delete the session file
    click.echo(f"You have been logged out, {email}.")


if __name__ == '__main__':
    cli()
