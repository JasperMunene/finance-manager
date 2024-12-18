#!/bin/bash

# The base command for the finance manager CLI
BASE_COMMAND="python -m finance_manager.main"

# Check if a subcommand is provided
if [ $# -lt 1 ]; then
  echo "Usage: ./fm.sh [COMMAND] [ARGS...]"
  echo ""
  echo "Available Commands:"
  echo "  add-category       Add a new category to the finance manager."
  echo "  add-transaction    Add a new transaction for the currently logged-in user."
  echo "  advice             Provide financial advice based on the user's data."
  echo "  login              Log in as a user."
  echo "  logout             Log out the current user."
  echo "  set-budget         Set a budget for a specific category."
  echo "  signup             Register a new user."
  echo "  suggest-adjustment Suggest budget adjustments"
  echo ""
  echo "Use './fm.sh --help' for more information."
  exit 1
fi

# Pass the subcommand and its arguments to the base command
$BASE_COMMAND "$@"
