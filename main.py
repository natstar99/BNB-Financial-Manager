"""
BNB Financial Manager - Main Entry Point

This module serves as the entry point for the BNB Financial Manager application.
It initialises the MVC architecture components and starts the application.
"""

from controllers.category_controller import CategoryController
from controllers.transaction_controller import TransactionController
from models.database_manager import DatabaseManager
from models.category_model import CategoryModel
from models.transaction_model import TransactionModel
from models.bank_account_model import BankAccountModel
from models.bank_account_reconciliation import BankAccountReconciliation


def main():
    """
    Application entry point that initialises the MVC components.
    
    This function sets up the database manager, models, and controllers
    for the financial management application. Since the GUI views have been
    migrated to a separate frontend, this now serves as the API backend.
    """
    # Initialise database and models
    db_manager = DatabaseManager("finance.db")
    category_model = CategoryModel(db_manager)
    transaction_model = TransactionModel(db_manager)
    bank_account_model = BankAccountModel(db_manager)
    bank_reconciliation = BankAccountReconciliation(bank_account_model, transaction_model)
    
    # Initialise controllers
    category_controller = CategoryController(category_model)
    transaction_controller = TransactionController(
        transaction_model, 
        bank_account_model,
        category_controller
    )
    
    print("BNB Financial Manager backend initialised successfully")
    print("Database models and controllers are ready")
    
    # Note: GUI components removed - now using separate React frontend
    # Run the API server from api/main.py instead
    return 0


if __name__ == "__main__":
    main()