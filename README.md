# Finance Manager CLI Project

## Overview

This is a command-line interface (CLI) application designed to help users manage their personal finances. It allows users to perform various financial activities such as:

- Registering and logging in as a user.
- Adding income and expense transactions.
- Categorizing transactions and managing budgets.
- Providing financial advice based on transaction history.
- Simulating financial scenarios.
- Displaying transaction history, budgets, and categories.
- Managing user sessions.
---
## Features

- **User Registration & Login:** Sign up and log in to the application with email and password.
- **Transaction Management:** Add income/expense transactions with automatic categorization using AI.
- **Budget Management:** Set and track budgets for various categories.
- **Financial Advice:** Get financial advice based on your transaction history.
- **Scenario Simulation:** Simulate financial scenarios to understand their potential impact.
- **Category Management:** Add and view categories for transactions and budgets.
- **Data Visualization:** View transactions, budgets, and categories in a well-formatted table.
- **Database Management:** Uses SQLAlchemy for database interactions, with Alembic for handling migrations.
- **AI-powered Transaction Categorization:** Leverages Gemini API to categorize transactions and generate financial insights.
---
## Requirements

- Python 3.8+
- [Google Gemini API Key](https://ai.google.dev/gemini-api/docs/) for transaction categorization and financial advice
- [Python-dotenv](https://pypi.org/project/python-dotenv/) for loading environment variables
- [SQLAlchemy](https://www.sqlalchemy.org/) for database management
- [Alembic](https://alembic.sqlalchemy.org/en/latest/) for database migrations
- [Click](https://click.palletsprojects.com/en/8.1.x/) for creating the command-line interface
- [Tabulate](https://pypi.org/project/tabulate/) for displaying tables in the CLI
- [Pyfiglet](https://pypi.org/project/pyfiglet/) for ASCII banners
- [Passlib](https://pypi.org/project/passlib/) for password hashing

---
## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/JasperMunene/finance-manager.git
   cd finance-manager
   ```

2. Install the required dependencies:
   ```bash
   pip install [...dependancy]
   ```

3. Set up the environment variables:
   - Create a `.env` file in the root of the project and add your Gemini API key:
     ```
     GEMINI_API_KEY=your_api_key_here
     ```

4. Set up the database and apply migrations:
   ```bash
   alembic upgrade head
   ```
---
## Usage

### CLI Commands

The project uses **Click** to create a command-line interface (CLI) for interacting with the finance manager. Available commands are listed below.

### User Commands

- **signup**: Register a new user
  ```bash
  python -m finance_manager.main signup
  ```

- **login**: Log in with your email and password
  ```bash
  python -m finance_manager.main login
  ```

- **logout**: Log out the current user
  ```bash
  python -m finance_manager.main logout
  ```

### Transaction Management

- **add-transaction**: Add a new transaction (income/expense)
  ```bash
  python -m finance_manager.main add-transaction
  ```

- **transactions**: Display all transactions for the currently logged-in user
  ```bash
  python -m finance_manager.main transactions
  ```

### Budget Management

- **set-budget**: Set a budget for a specific category
  ```bash
  python -m finance_manager.main set-budget
  ```

- **budgets**: Display all budgets for the logged-in user
  ```bash
  python -m finance_manager.main budgets
  ```

### Category Management

- **add-category**: Add a new category to the finance manager
  ```bash
  python -m finance_manager.main add-category
  ```

- **categories**: Display all categories in the system
  ```bash
  python -m finance_manager.main categories
  ```

### Financial Insights

- **advice**: Get financial advice based on your transactions
  ```bash
  python -m finance_manager.main advice
  ```

- **simulate-scenario**: Simulate a scenario based on transaction history
  ```bash
  python -m finance_manager.main simulate-scenario
  ```

### Deletion

- **delete-transactions**: Delete all transactions for the currently logged-in user
  ```bash
  python -m finance_manager.main delete-transactions
  ```

---
## Session Management

- **`get_logged_in_user`**: Retrieves the email of the logged-in user from the session file (`user.txt`).
- **`set_logged_in_user`**: Stores the logged-in user's email in the session file.
- **`remove_logged_in_user`**: Logs out the user by removing the session file.
---
## Database Models

The project uses the following SQLAlchemy models:

- **User**: Stores user details such as name, email, and password hash.
- **Transaction**: Stores transactions (income/expense) along with their associated category.
- **Category**: Stores categories for transactions (e.g., "Food", "Entertainment").
- **Budget**: Stores the budget set by users for each category.
---
## Database

The project uses **SQLAlchemy** for database management and **Alembic** for handling migrations.

1. To generate a new migration after making changes to the models, run:
   ```bash
   alembic revision --autogenerate -m "your message here"
   ```

2. To apply the migrations to the database:
   ```bash
   alembic upgrade head
   ```
---
## Custom Shell Script (`fm.sh`)

A shell script `fm.sh` is provided for easier usage of commands. To run any command, use the following format:

```bash
./fm.sh [COMMAND]
```

Example:
```bash
./fm.sh add-transaction
```

This will call the respective subcommand from the Python script.

---
## Contributing

Feel free to contribute to this project by submitting issues or pull requests.

---

## Author

**Jasper Munene**  
Creator & Developer of the Finance Manager CLI

- GitHub: [@JasperMunene](https://github.com/JasperMunene)
- Email: [devjaspermunene@gmail.com](mailto:devjaspermunene@gmail.com)

Feel free to reach out if you have any questions or suggestions!

---


## License

This project is licensed under the MIT License.