# File: controllers/transaction_controller.py

from PySide6.QtWidgets import QDialog
from models.transaction_model import TransactionModel
from views.duplicate_manager import DuplicateManagerDialog
from utils.qif_parser import QIFParser
from models.bank_account_model import BankAccountModel
from typing import List, Set, Optional, Dict
from decimal import Decimal
import datetime
import os

class TransactionController:
    """Controller for managing transaction operations"""
    def __init__(self, transaction_model: TransactionModel, bank_account_model: Optional[BankAccountModel] = None):
        """
        Initialise the transaction controller
        
        Args:
            transaction_model: The transaction model instance
            bank_account_model: Optional bank account model instance for balance tracking
        """
        self.model = transaction_model
        self.bank_account_model = bank_account_model
    
    def get_transactions(self, filter_type: str = "all") -> List:
        """Retrieve transactions based on filter"""
        return self.model.get_transactions(filter_type)
    
    def categorise_transaction(self, transaction_id: int, category_id: str):
        """Assign a category to a transaction"""
        try:
            self.model.update_transaction_category(transaction_id, category_id)
            return True
        except Exception as e:
            print(f"Error categorizing transaction: {e}")
            return False
        
    def create_auto_categorisation_rule(self, rule_data: dict) -> bool:
        """Create a new auto-categorisation rule"""
        return self.model.create_auto_categorisation_rule(rule_data)

    def apply_auto_categorisation_rules(self):
        """Apply auto-categorisation rules to transactions"""
        self.model.apply_auto_categorisation_rules()

    def match_transactions(self, transaction_ids: List[int]):
        """Mark transactions as matched (internal transfers)"""
        try:
            self.model.mark_transactions_matched(transaction_ids)
            return True
        except Exception as e:
            print(f"Error matching transactions: {e}")
            return False
        
    def import_qif_file(self, file_path: str, account_id: str) -> tuple[bool, int, int]:
        """
        Import transactions from QIF file into a specific account
        
        Args:
            file_path: Path to the QIF file
            account_id: Bank account ID to import into
            
        Returns:
            tuple: (success, number of transactions imported, number of duplicates skipped)
        """
        try:
            # Parse file
            parser = QIFParser()
            transactions = parser.parse_file(file_path)
            
            # Set account ID for all transactions
            for trans in transactions:
                trans.account = account_id
            
            # Import transactions
            imported_count, duplicate_count = self.model.import_qif_transactions(
                transactions)
            
            # Update account balance if import successful
            if imported_count > 0 and self.bank_account_model:
                # Calculate new balance from successful imports only
                total_amount = sum(
                    t.amount for t in transactions 
                    if not self.model.is_duplicate_in_account(t, account_id)
                )
                
                # Update account balance
                self.bank_account_model.update_balance(
                    account_id,
                    total_amount,
                    datetime.now().isoformat()
                )
            
            # Detect internal transfers
            self.model.detect_internal_transfers()
            
            return True, imported_count, duplicate_count
            
        except Exception as e:
            print(f"Error importing QIF file: {e}")
            return False, 0, 0
        
    def import_multiple_qif_files(self, import_files: List[Dict]) -> Dict[str, Dict[str, int]]:
        """
        Import multiple QIF files with account associations
        
        Args:
            import_files: List of dictionaries containing file_path and account_id
        
        Returns:
            Dictionary with results for each file:
            {
                'file_name': {
                    'success': bool,
                    'imported_count': int,
                    'duplicate_count': int
                }
            }
        """
        results = {}
        
        for import_file in import_files:
            file_path = import_file['file_path']
            account_id = import_file['account_id']
            
            try:
                # Parse file
                parser = QIFParser()
                transactions = parser.parse_file(file_path)
                
                # Set account ID for all transactions
                for trans in transactions:
                    trans.account = account_id
                
                # Check for duplicates
                file_duplicates = self.model.find_duplicates_in_qif(transactions)
                db_duplicates = self.model.find_database_duplicates(transactions)
                
                selected_transactions = None
                if file_duplicates or db_duplicates:
                    # Show duplicate manager dialog
                    dialog = DuplicateManagerDialog(file_duplicates, db_duplicates)
                    if dialog.exec_() == QDialog.Accepted:
                        selected_transactions = dialog.get_selected_transactions()
                    else:
                        continue  # Skip this file if user cancels
                
                # Import transactions
                imported_count, duplicate_count = self.model.import_qif_transactions(
                    transactions, selected_transactions)
                
                # Update account balance if import successful
                if self.bank_account_model:
                    # Calculate new balance from successful imports only
                    total_amount = sum(
                        t.amount for t in transactions 
                        if not self.model.is_duplicate_transaction(t))
                    
                    # Get current account balance
                    accounts = self.bank_account_model.get_accounts()
                    account = next(a for a in accounts if a.id == account_id)
                    new_balance = account.current_balance + Decimal(str(total_amount))
                    
                    # Update account balance and import date
                    from datetime import datetime
                    self.bank_account_model.update_balance(
                        account_id,
                        new_balance,
                        datetime.now().isoformat()
                    )
                
                results[os.path.basename(file_path)] = {
                    'success': True,
                    'imported_count': imported_count,
                    'duplicate_count': duplicate_count
                }
                
            except Exception as e:
                print(f"Error importing file {file_path}: {e}")
                results[os.path.basename(file_path)] = {
                    'success': False,
                    'imported_count': 0,
                    'duplicate_count': 0,
                    'error': str(e)
                }
        
        return results