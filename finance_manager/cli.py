import click
from passlib.hash import bcrypt
from sqlalchemy.exc import IntegrityError
from finance_manager.database import init_db, get_db, SessionLocal
from finance_manager.models import User, Transaction, Category
from finance_manager.ai import categorize_transaction, generate_financial_advice

# Initialize the database
init_db()

# Global variable to store the logged-in user
logged_in_user = None

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
        click.echo("User registered successfully!")
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
    global logged_in_user
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if user and bcrypt.verify(password, user.password_hash):
        logged_in_user = user  # Store the logged-in user
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
    global logged_in_user
    if not logged_in_user:
        click.echo("You must be logged in to add a transaction.")
        return

    db = SessionLocal()
    category_name = categorize_transaction(description)
    category = db.query(Category).filter(Category.name == category_name).first()

    if not category:
        category = Category(name=category_name)
        db.add(category)
        db.commit()

    transaction = Transaction(user_id=logged_in_user.id, category_id=category.id, amount=amount, type=type)
    db.add(transaction)
    db.commit()
    click.echo(f"Transaction added under category: {category_name}")
    db.close()


@cli.command()
@click.option('--email', prompt='Your email', help='Email of the user.')
def advice(email):
    """Provide financial advice based on the user's transactions."""
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

    advice = generate_financial_advice(formatted_transactions)
    click.echo("Financial Advice:")
    click.echo(advice)
    db.close()


if __name__ == '__main__':
    cli()
