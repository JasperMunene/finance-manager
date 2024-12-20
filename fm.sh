#!/bin/bash

# The base command for the finance manager CLI
BASE_COMMAND="python -m finance_manager.main"

python3 finance_manager/banner.py
# Check if a subcommand is provided
if [ $# -lt 1 ]; then
  echo "Usage: ./fm.sh [COMMAND]"
  echo ""
  echo "Available Commands:"
  echo "  add-category        Add a new category to the finance manager."
  echo "  add-transaction     Add a new transaction"
  echo "  advice              Provide financial advice"
  echo "  login               Log in as a user."
  echo "  logout              Log out"
  echo "  set-budget          Set a budget for a specific category."
  echo "  signup              Register"
  echo "  simulate-scenario   Simulate a scenario based on transaction history."
  echo "  transactions        Display all transactions"
  echo "  budgets             Display all budgets"
  echo "  categories          Display all categories"
  echo "  delete-transactions Delete all transactions for the currently logged-in user"
  echo "  delete-category     Delete a category"
  echo "  update-transaction  Update a transaction"
  echo ""
  echo "Use './fm.sh --help' for more information."
  exit 1
fi

# Pass the subcommand and its arguments to the base command
$BASE_COMMAND "$@"
