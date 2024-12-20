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

def signup():
    """Register a new user."""
    name = input("Your name: ")
    email = input("Your email: ")
    password = input("Your password: ")
    password_confirm = input("Confirm password: ")
    if password != password_confirm:
        print("Passwords do not match.")
        return

    db = SessionLocal()
    try:
        hashed_password = bcrypt.hash(password)
        user = User(name=name, email=email, password_hash=hashed_password)
        db.add(user)
        db.commit()
        set_logged_in_user(email)  # Save email to session file after successful signup
        print(f"User registered and logged in successfully as {name}!")
    except IntegrityError:
        db.rollback()
        print("Email already exists. Please try a different email.")
    finally:
        db.close()

def login():
    """Log in as a user."""
    email = input("Your email: ")
    password = input("Your password: ")

    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if user and bcrypt.verify(password, user.password_hash):
        set_logged_in_user(email)  # Store the email of the logged-in user
        print(f"Welcome back, {user.name}!")
    else:
        print("Invalid email or password.")
    db.close()


def add_transaction():
    """Add a new transaction for the currently logged-in user and track budget usage."""
    email = get_logged_in_user()
    if not email:
        print("You must be logged in to add a transaction.")
        return

    description = input("Transaction description: ")
    amount = float(input("Transaction amount: "))
    type = input("Transaction type (income/expense): ")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print("User not found.")
            return

        # Categorize the transaction
        response = categorize_transaction(description)
        try:
            result = json.loads(response.text)
            transaction_category = result.get("category")
        except (json.JSONDecodeError, AttributeError):
            print("Error categorizing the transaction.")
            return

        if not transaction_category:
            print("Unable to determine the transaction category.")
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
        print(f"Transaction added under category: {transaction_category}")

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
                    print(f"Alert: You have exceeded your budget for '{transaction_category}' by Ksh {abs(remaining_budget):.2f}!")
                else:
                    print(f"Remaining budget for '{transaction_category}': Ksh {remaining_budget:.2f}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()


def advice():
    """Provide financial advice based on the user's transactions."""
    email = get_logged_in_user()
    if not email:
        print("You must be logged in to get financial advice.")
        return

    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        print("User not found. Please register first.")
        db.close()
        return

    transactions = db.query(Transaction).filter(Transaction.user_id == user.id).all()
    if not transactions:
        print("No transactions found.")
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
    print("Financial Analysis:")
    print(analysis)
    print("Advice:")
    for tip in advice:
        print(f"- {tip}")

    db.close()


def set_budget():
    """Set a budget for a specific category."""
    email = get_logged_in_user()
    if not email:
        print("You must be logged in to set a budget.")
        return

    category = input("Category name: ")
    amount = float(input("Budget amount (in Ksh): "))

    db = SessionLocal()
    try:
        # Get the user from the database
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print("User not found. Please register first.")
            return

        # Check if the category exists
        category_obj = db.query(Category).filter(Category.name == category).first()
        if not category_obj:
            print(f"Category '{category}' not found. Please add the category first.")
            return

        # Check if a budget already exists for this category
        existing_budget = db.query(Budget).filter(Budget.category_id == category_obj.id, Budget.user_id == user.id).first()
        if existing_budget:
            print(f"A budget for '{category}' already exists. Updating the amount.")
            existing_budget.amount = amount
        else:
            # Create a new budget record
            new_budget = Budget(user_id=user.id, category_id=category_obj.id, amount=amount)
            db.add(new_budget)

        db.commit()
        print(f"Budget of Ksh {amount} has been set for {category}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()


def transactions():
    """Display all transactions for the currently logged-in user."""
    email = get_logged_in_user()
    if not email:
        print("You must be logged in to view transactions.")
        return

    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        print("User not found. Please register first.")
        db.close()
        return

    # Fetch all transactions for the logged-in user
    transactions = db.query(Transaction).filter(Transaction.user_id == user.id).all()
    if not transactions:
        print("No transactions found.")
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
    print(tabulate(table_data, headers, tablefmt="grid"))

    db.close()

def logout():
    """Log out the current user"""
    email = get_logged_in_user()
    if not email:
        print("You are not logged in.")
        return

    remove_logged_in_user()  # Delete the session file
    print(f"You have been logged out, {email}.")

def quit_program():
    """Quit the program."""
    print("Goodbye!")
    exit()

def update_transaction():
    """Update an existing transaction."""
    
    transaction_id = input("Transaction id")
    amount = input("Amount")
    type = input("Type")
    category = input("Category")
    email = get_logged_in_user()
    if not email:
        print("You must be logged in to update a transaction.")
        return

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print("User not found.")
            return

        # Fetch the transaction
        transaction = db.query(Transaction).filter(Transaction.id == transaction_id, Transaction.user_id == user.id).first()
        if not transaction:
            print("Transaction not found.")
            return

        # Update the transaction fields if new values are provided
        if amount:
            transaction.amount = amount
        if type:
            transaction.type = type

        # Handle the category update
        if category:
            # Normalize the category name
            category = category.strip().title()
            
            # Check if the category exists
            existing_category = db.query(Category).filter_by(name=category).first()
            if not existing_category:
                # Create a new category if it doesn't exist
                new_category = Category(name=category)
                db.add(new_category)
                db.commit()  # Commit to generate an ID for the new category
                existing_category = new_category
            
            # Update the transaction's category_id
            transaction.category_id = existing_category.id

        # Commit the updates
        db.commit()
        print("Transaction updated successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()

def delete_transactions():
    """Delete all transactions for the currently logged-in user."""
    email = get_logged_in_user()
    if not email:
        print("You must be logged in to delete transactions.")
        return

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print("User not found.")
            return

        # Delete all transactions for the user
        db.query(Transaction).filter(Transaction.user_id == user.id).delete()
        db.commit()

        print("All transactions have been deleted successfully.")
    except Exception as e:
        db.rollback()
        print(f"An error occurred: {e}")
    finally:
        db.close()

def simulate_scenario(scenario):
    """Simulate a scenario based on transaction history."""
    email = get_logged_in_user()
    if not email:
        print("You must be logged in to simulate scenarios.")
        return

    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        print("User not found. Please register first.")
        db.close()
        return

    transactions = db.query(Transaction).filter(Transaction.user_id == user.id).all()
    if not transactions:
        print("No transactions found.")
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

    print("Analysis: ")
    print(analysis)

    print("Impact: ")
    print(impact)


    db.close()
    
def set_budget(category, amount):
    """Set a budget for a specific category."""
    email = get_logged_in_user()
    if not email:
        print("You must be logged in to set a budget.")
        return

    db = SessionLocal()
    try:
        # Get the user from the database
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print("User not found. Please register first.")
            return

        # Check if the category exists
        category_obj = db.query(Category).filter(Category.name == category).first()
        if not category_obj:
            print(f"Category '{category}' not found. Please add the category first.")
            return

        # Check if a budget already exists for this category
        existing_budget = db.query(Budget).filter(Budget.category_id == category_obj.id, Budget.user_id == user.id).first()
        if existing_budget:
            print(f"A budget for '{category}' already exists. Updating the amount.")
            existing_budget.amount = amount
        else:
            # Create a new budget record
            new_budget = Budget(user_id=user.id, category_id=category_obj.id, amount=amount)
            db.add(new_budget)

        db.commit()
        print(f"Budget of Ksh {amount} has been set for {category}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()
def menu():
    """Display the menu and handle user input."""
    while True:
        print("\nFinance Manager CLI")
        print("1. Sign Up")
        print("2. Log In")
        print("3. Add Transaction")
        print("4. Get Financial Advice")
        print("5. Set Budget")
        print("6. View Transactions")
        print("7. Log Out")
        print("8. Quit")
        print("9. Update Transaction")
        print("10. Advice")
        print("11. Delete Transactions")
        print("12. Simulate Scenario")
        print("Enter a budget: ")

        choice = input("Choose an option: ")

        if choice == '1':
            signup()
        elif choice == '2':
            login()
        elif choice == '3':
            add_transaction()
        elif choice == '4':
            advice()
        elif choice == '5':
            set_budget()
        elif choice == '6':
            transactions()
        elif choice == '7':
            logout()
        elif choice == '8':
            quit_program()
        elif choice == '9':
            update_transaction()
        elif choice == '10':
            advice()
        elif choice == '11':
            delete_transactions()
        elif choice == '12':
            scenario = input("Enter the scenario: ")
            simulate_scenario(scenario)
        
        else:
            print("Invalid choice. Please try again.")


if __name__ == '__main__':
    menu()
