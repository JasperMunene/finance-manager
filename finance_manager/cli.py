import click
from passlib.hash import bcrypt
from sqlalchemy.exc import IntegrityError
from finance_manager.database import init_db, get_db, SessionLocal
from finance_manager.models import User, Transaction, Category
from finance_manager.ai import categorize_transaction, generate_financial_advice

init_db()

@click.group()
def cli():
    """Finance Manager CLI"""

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