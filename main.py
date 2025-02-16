# File: main.py

from PySide6.QtWidgets import QApplication
from views.main_window import MainWindow
from controllers.category_controller import CategoryController
from controllers.transaction_controller import TransactionController
from models.database_manager import DatabaseManager
from models.category_model import CategoryModel
from models.transaction_model import TransactionModel
from models.bank_account_model import BankAccountModel
from models.bank_account_reconciliation import BankAccountReconciliation

def main():
    """Application entry point that initialises the MVC components"""
    app = QApplication([])
    
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
    
    # Initialise main window
    main_window = MainWindow(
        category_controller, 
        transaction_controller,
        bank_account_model,
        bank_reconciliation
    )
    main_window.show()
    
    return app.exec()

if __name__ == "__main__":
    main()