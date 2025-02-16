# File: models/bank_account_reconciliation.py

from decimal import Decimal
from datetime import datetime
from typing import Dict, List
from models.bank_account_model import BankAccountModel
from models.transaction_model import TransactionModel

class BankAccountReconciliation:
    """Class for handling bank account reconciliation processes"""
    
    def __init__(self, bank_account_model: BankAccountModel, transaction_model: TransactionModel):
        self.bank_account_model = bank_account_model
        self.transaction_model = transaction_model
    
    def start_reconciliation(self, account_id: str, statement_balance: Decimal, 
                           statement_date: datetime) -> Dict:
        """
        Start a reconciliation process for an account
        
        Args:
            account_id: The bank account ID to reconcile
            statement_balance: The balance from the bank statement
            statement_date: The date of the bank statement
            
        Returns:
            Dict containing reconciliation information
        """
        try:
            # Get all transactions up to statement date
            cursor = self.transaction_model.db.execute("""
                SELECT id, date, description, withdrawal, deposit, is_internal_transfer
                FROM transactions
                WHERE account = ?
                AND date <= ?
                AND is_hidden = 0
                ORDER BY date
            """, (account_id, statement_date.isoformat()))
            
            transactions = []
            calculated_balance = Decimal('0')
            
            for row in cursor:
                withdrawal = Decimal(str(row[3])) if row[3] else Decimal('0')
                deposit = Decimal(str(row[4])) if row[4] else Decimal('0')
                calculated_balance = calculated_balance - withdrawal + deposit
                
                transactions.append({
                    'id': row[0],
                    'date': datetime.fromisoformat(row[1]),
                    'description': row[2],
                    'withdrawal': withdrawal,
                    'deposit': deposit,
                    'is_internal': bool(row[5])
                })
            
            difference = calculated_balance - statement_balance
            
            return {
                'account_id': account_id,
                'statement_date': statement_date,
                'statement_balance': statement_balance,
                'calculated_balance': calculated_balance,
                'difference': difference,
                'transactions': transactions
            }
            
        except Exception as e:
            print(f"Error starting reconciliation: {e}")
            return None
    
    def find_potential_matches(self, target_amount: Decimal, 
                             transactions: List[Dict], window_days: int = 5) -> List[Dict]:
        """
        Find potential matching transactions for reconciliation
        
        Args:
            target_amount: The amount to match
            transactions: List of transactions to search
            window_days: Number of days to look around
            
        Returns:
            List of potential matching transactions
        """
        matches = []
        target_amount = abs(target_amount)  # Work with absolute values
        
        for trans in transactions:
            amount = trans['withdrawal'] or trans['deposit']
            if abs(abs(amount) - target_amount) < Decimal('0.01'):
                matches.append(trans)
        
        return matches