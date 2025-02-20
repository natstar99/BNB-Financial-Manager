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
    def __init__(self, transaction_model: TransactionModel, 
                 bank_account_model: Optional[BankAccountModel] = None,
                 category_controller = None):
        """
        Initialise the transaction controller
        
        Args:
            transaction_model: The transaction model instance
            bank_account_model: Optional bank account model instance for balance tracking
            category_controller: CategoryController instance for category operations
        """
        self.model = transaction_model
        self.bank_account_model = bank_account_model
        self.category_controller = category_controller
    
    def get_transactions(self, filter_type: str = "all") -> List:
        """Retrieve transactions based on filter"""
        return self.model.get_transactions(filter_type)
    
    def categorise_transaction(self, transaction_id: int, category_id: str = None,
                           is_internal_transfer: bool = False, is_hidden: bool = False):
        """
        Assign a category to a transaction or mark it with a special state
        
        Args:
            transaction_id: The ID of the transaction to categorise
            category_id: The category ID to assign (None if special state)
            is_internal_transfer: Flag indicating if this is an internal transfer
            is_hidden: Flag indicating if this transaction should be hidden
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if is_internal_transfer:
                self.model.db.execute("""
                    UPDATE transactions 
                    SET category_id = NULL,
                        is_internal_transfer = 1,
                        is_matched = 1,
                        is_hidden = 0
                    WHERE id = ?
                """, (transaction_id,))
            elif is_hidden:
                self.model.db.execute("""
                    UPDATE transactions 
                    SET category_id = NULL,
                        is_internal_transfer = 0,
                        is_matched = 0,
                        is_hidden = 1
                    WHERE id = ?
                """, (transaction_id,))
            else:
                self.model.db.execute("""
                    UPDATE transactions 
                    SET category_id = ?,
                        is_internal_transfer = 0,
                        is_matched = 0,
                        is_hidden = 0
                    WHERE id = ?
                """, (category_id, transaction_id))
                
            self.model.db.commit()
            return True
        except Exception as e:
            print(f"Error categorising transaction: {e}")
            self.model.db.rollback()
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
        
    def import_qif_files(self, import_files: List[Dict]) -> Dict[str, Dict[str, int]]:
        """
        Import one or more QIF files with account associations
        
        Args:
            import_files: List of dictionaries containing file_path and account_id
        
        Returns:
            Dictionary with results for each file:
            {
                'file_name': {
                    'success': bool,
                    'imported_count': int,
                    'duplicate_count': int,
                    'error': Optional[str]
                }
            }
        """
        results = {}
        all_transactions = []  # Store all transactions for internal transfer detection
        
        from datetime import datetime, timedelta  # Import at top of method
        
        # First pass: Parse all files and collect transactions
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
                
                all_transactions.extend(transactions)
                
                # Split transactions into new and potential duplicates
                duplicates = self.model.find_database_duplicates(transactions)
                duplicate_trans_ids = {(d['transaction'].date, d['transaction'].amount, 
                                    d['transaction'].payee, d['transaction'].memo) 
                                    for d in duplicates}
                new_transactions = [t for t in transactions 
                                if (t.date, t.amount, t.payee, t.memo) not in duplicate_trans_ids]

                # Show transaction manager dialog
                dialog = DuplicateManagerDialog(new_transactions, duplicates)
                if dialog.exec_() == QDialog.Accepted:
                    selected = dialog.get_selected_transactions()
                    transactions_to_import = [t for t in transactions if (
                        t.date, t.amount, t.payee, t.memo) in selected]
                else:
                    continue  # Skip this file if user cancels
                
                # Import transactions
                imported_count, duplicate_count = self.model.import_qif_transactions(
                    transactions, account_id)
                
                # Update account balance
                if self.bank_account_model:
                    # Calculate new balance from successful imports only
                    total_amount = sum(t.amount for t in transactions 
                                    if not self.model.is_duplicate_transaction(t))
                    
                    # Get current account balance
                    account = next(a for a in self.bank_account_model.get_accounts() 
                                if a.id == account_id)
                    new_balance = account.current_balance + Decimal(str(total_amount))
                    
                    # Update account balance and import date
                    self.bank_account_model.update_balance(
                        account_id,
                        new_balance,
                        datetime.now().isoformat()  # Using datetime.now() correctly now
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
        
        # After all files are imported, detect internal transfers
        if len(import_files) > 1:
            self.model.detect_internal_transfers()
        
        return results
    
    def get_auto_categorisation_rules(self) -> List[Dict]:
        """Get all auto-categorisation rules"""
        return self.model.get_auto_categorisation_rules()

    def update_auto_categorisation_rule(self, rule_id: int, rule_data: Dict) -> bool:
        """Update an existing auto-categorisation rule"""
        return self.model.update_auto_categorisation_rule(rule_id, rule_data)

    def delete_auto_categorisation_rule(self, rule_id: int) -> bool:
        """Delete an auto-categorisation rule"""
        return self.model.delete_auto_categorisation_rule(rule_id)