"""
Bank Account Model Module

This module provides bank account management functionality including
account creation, balance tracking, and balance validation.
"""

from dataclasses import dataclass
from typing import Optional, List
from decimal import Decimal
from models.category_model import CategoryType

@dataclass
class BankAccount:
    """Data class representing a bank account"""
    id: str  # Uses the same hierarchical ID system as categories
    name: str
    account_number: str
    bsb: str  # BSB number (Australian bank identifier)
    bank_name: str
    current_balance: Decimal
    last_import_date: Optional[str] = None
    notes: Optional[str] = None

class BankAccountModel:
    """Model for managing bank accounts"""
    def __init__(self, db_manager):
        """Initialise the bank account model with database connection"""
        self.db = db_manager
        self._ensure_bank_account_table()
    
    def _ensure_bank_account_table(self):
        """Ensure the bank accounts table exists in the database"""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS bank_accounts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                account_number TEXT NOT NULL,
                bsb TEXT NOT NULL,
                bank_name TEXT NOT NULL,
                current_balance DECIMAL(15,2) NOT NULL DEFAULT 0.00,
                last_import_date TEXT,
                notes TEXT,
                UNIQUE(bsb, account_number)
            )
        """)
        self.db.commit()
    
    def get_accounts(self) -> List[BankAccount]:
        """
        Retrieve all bank accounts under the Assets tree.
        Returns a list of BankAccount objects for all accounts in the system.
        """
        cursor = self.db.execute("""
            SELECT ba.id, ba.name, ba.account_number, ba.bsb, 
                   ba.bank_name, ba.current_balance, 
                   ba.last_import_date, ba.notes
            FROM bank_accounts ba
            JOIN categories c ON c.id = ba.id
            WHERE c.id LIKE '1%'  -- Get all accounts under Assets (1)
            AND c.is_bank_account = 1  -- Ensure it's a bank account
            ORDER BY ba.id
        """)
        
        return [BankAccount(
            id=row[0],
            name=row[1],
            account_number=row[2],
            bsb=row[3],
            bank_name=row[4],
            current_balance=Decimal(str(row[5])),
            last_import_date=row[6],
            notes=row[7]
        ) for row in cursor]

    def update_balance(self, account_id: str, new_balance: Decimal,
                      import_date: Optional[str] = None) -> bool:
        """Update account balance and optionally the last import date"""
        try:
            if import_date:
                self.db.execute("""
                    UPDATE bank_accounts 
                    SET current_balance = ?,
                        last_import_date = ?
                    WHERE id = ?
                """, (float(new_balance), import_date, account_id))
            else:
                self.db.execute("""
                    UPDATE bank_accounts 
                    SET current_balance = ?
                    WHERE id = ?
                """, (float(new_balance), account_id))
            
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error updating bank account balance: {e}")
            return False

    def recalculate_balance(self, account_id: str) -> bool:
        """
        Recalculate account balance based on all transactions
        
        Args:
            account_id: The bank account ID to recalculate
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.db.execute("BEGIN TRANSACTION")
            
            # Get all transactions for this account
            cursor = self.db.execute("""
                SELECT withdrawal, deposit
                FROM transactions
                WHERE account = ?
                AND is_hidden = 0  -- Exclude hidden transactions
                ORDER BY date
            """, (account_id,))
            
            balance = Decimal('0')
            for row in cursor:
                withdrawal = Decimal(str(row[0])) if row[0] else Decimal('0')
                deposit = Decimal(str(row[1])) if row[1] else Decimal('0')
                balance = balance - withdrawal + deposit
            
            # Update the account balance
            self.db.execute("""
                UPDATE bank_accounts
                SET current_balance = ?
                WHERE id = ?
            """, (float(balance), account_id))
            
            self.db.execute("COMMIT")
            return True
            
        except Exception as e:
            self.db.execute("ROLLBACK")
            print(f"Error recalculating balance: {e}")
            return False
    
    def validate_balance(self, account_id: str, expected_balance: Decimal) -> tuple[bool, Decimal]:
        """
        Validate current balance against expected balance
        
        Args:
            account_id: The bank account ID to validate
            expected_balance: The expected balance to validate against
            
        Returns:
            tuple: (is_valid, difference)
        """
        try:
            # Get current calculated balance
            cursor = self.db.execute("""
                SELECT current_balance 
                FROM bank_accounts 
                WHERE id = ?
            """, (account_id,))
            
            current_balance = Decimal(str(cursor.fetchone()[0]))
            difference = current_balance - expected_balance
            
            # Consider balances matching within 1 cent as valid
            is_valid = abs(difference) < Decimal('0.01')
            
            return is_valid, difference
            
        except Exception as e:
            print(f"Error validating balance: {e}")
            return False, Decimal('0')
    
    def create_account(self, name: str, account_number: Optional[str] = None, 
                      bsb: Optional[str] = None, bank_name: Optional[str] = None, 
                      notes: Optional[str] = None) -> str:
        """
        Create a new bank account
        
        Args:
            name: Account name/description
            account_number: Bank account number
            bsb: BSB code
            bank_name: Name of the bank
            notes: Optional notes
            
        Returns:
            str: The account ID
        """
        try:
            # Import here to avoid circular imports
            from models.category_model import CategoryModel, CategoryType
            
            # Create category model instance
            category_model = CategoryModel(self.db)
            
            # Start transaction
            self.db.execute("BEGIN TRANSACTION")
            
            # First, create the category using the existing CategoryModel logic
            account_id = category_model.add_category(
                name=name,
                parent_id="1",  # Assets category
                category_type=CategoryType.TRANSACTION,
                tax_type=None,
                is_bank_account=True
            )
            
            if not account_id:
                self.db.execute("ROLLBACK")
                raise Exception("Failed to create category for bank account")
            
            # Insert into bank_accounts table with the same ID
            self.db.execute("""
                INSERT INTO bank_accounts (id, name, account_number, bsb, bank_name, current_balance, notes)
                VALUES (?, ?, ?, ?, ?, 0.00, ?)
            """, (account_id, name, account_number or '', bsb or '', bank_name or '', notes or ''))
            
            self.db.execute("COMMIT")
            return account_id
            
        except Exception as e:
            self.db.execute("ROLLBACK")
            raise Exception(f"Error creating bank account: {e}")