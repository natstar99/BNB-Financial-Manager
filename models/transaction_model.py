# File: models/transaction_model.py

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Set
from enum import Enum
from utils.qif_parser import QIFTransaction
from models.category_model import CategoryType

class TaxType(Enum):
    """Enumeration of possible tax types"""
    GST = "GST"    # Goods and Services Tax
    FRE = "FRE"    # GST Free
    NT = "NT"      # Not Taxable
    NONE = "NONE"  # No tax type specified

@dataclass
class Transaction:
    """Data class representing a financial transaction"""
    id: Optional[int]
    date: datetime
    account: str
    description: str
    withdrawal: Decimal
    deposit: Decimal
    category_id: Optional[str]
    tax_type: TaxType
    is_tax_deductible: bool
    is_hidden: bool
    is_matched: bool
    is_internal_transfer: bool = False

class TransactionModel:
    """Model for managing financial transactions"""
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_transactions(self, filter_type: str = "all") -> List[Transaction]:
        """
        Retrieve transactions based on filter type
        
        Args:
            filter_type: Type of filter to apply (all, uncategorised, categorised, 
                        internal_transfers, hidden)
            
        Returns:
            List of filtered transactions
        """
        query = "SELECT * FROM transactions"
        params = []
        
        if filter_type == "uncategorised":
            query += " WHERE category_id IS NULL AND is_internal_transfer = 0"
        elif filter_type == "categorised":
            query += " WHERE category_id IS NOT NULL AND is_internal_transfer = 0"
        elif filter_type == "internal_transfers":
            query += " WHERE is_internal_transfer = 1"
        elif filter_type == "hidden":
            query += " WHERE is_hidden = 1"
        elif filter_type != "all":
            query += " WHERE is_hidden = 0"  # Default to showing non-hidden
        
        query += " ORDER BY date DESC"
        
        cursor = self.db.execute(query, params)
        return [self._row_to_transaction(row) for row in cursor]
    
    def _row_to_transaction(self, row):
        """
        Convert a database row to a Transaction object
        
        Args:
            row: Database row containing transaction data
            
        Returns:
            Transaction: A transaction object with all fields populated
        """
        try:
            tax_type_value = row[7]  # Get the tax_type value from the row
            # If tax_type is None/NULL, default to TaxType.NONE
            tax_type = TaxType(tax_type_value) if tax_type_value else TaxType.NONE
            
            return Transaction(
                id=row[0],
                date=datetime.fromisoformat(row[1]),
                account=row[2],
                description=row[3],
                withdrawal=Decimal(str(row[4])) if row[4] else Decimal('0'),
                deposit=Decimal(str(row[5])) if row[5] else Decimal('0'),
                category_id=row[6],
                tax_type=tax_type,
                is_tax_deductible=bool(row[8]),
                is_hidden=bool(row[9]),
                is_matched=bool(row[10]),
                is_internal_transfer=bool(row[11])  # Get is_internal_transfer from row
            )
        except Exception as e:
            print(f"Error converting row to transaction: {e}")
            print(f"Row data: {row}")
            raise
    
    def is_duplicate_transaction(self, trans: QIFTransaction, window_days: int = 3) -> bool:
        """
        Check if a transaction already exists in the database.
        
        Args:
            trans: The transaction to check
            window_days: Number of days to look around the transaction date
        
        Returns:
            bool: True if a matching transaction is found
        """
        # Calculate date range for checking
        start_date = (trans.date - timedelta(days=window_days)).isoformat()
        end_date = (trans.date + timedelta(days=window_days)).isoformat()
        
        # Determine withdrawal/deposit amounts
        withdrawal = float(abs(trans.amount)) if trans.amount < 0 else 0.0
        deposit = float(trans.amount) if trans.amount > 0 else 0.0
        
        # Build the description as it would appear in the database
        description = trans.payee + (f" - {trans.memo}" if trans.memo else '')
        
        # Query for matching transactions
        cursor = self.db.execute("""
            SELECT COUNT(*) FROM transactions
            WHERE date BETWEEN ? AND ?
            AND ABS(withdrawal - ?) < 0.01  -- Use small epsilon for float comparison
            AND ABS(deposit - ?) < 0.01
            AND description = ?
        """, (start_date, end_date, withdrawal, deposit, description))
        
        count = cursor.fetchone()[0]
        return count > 0

    def import_qif_transactions(self, transactions: List[QIFTransaction], account_id: str) -> tuple[int, int]:
        """
        Import transactions from QIF format into a specific bank account.
        
        Args:
            transactions (List[QIFTransaction]): List of transactions to import
            account_id (str): Bank account ID to import into
            
        Returns:
            tuple[int, int]: (number of transactions imported, number of duplicates skipped)
        """
        try:
            imported_count = 0
            duplicate_count = 0
            
            # Verify this is a valid bank account
            cursor = self.db.execute("""
                SELECT 1 FROM categories 
                WHERE id = ? 
                AND is_bank_account = 1
                AND category_type = ?
            """, (account_id, CategoryType.TRANSACTION.value))
            
            if not cursor.fetchone():
                raise ValueError(f"Invalid bank account ID: {account_id}")
            
            # Process each transaction
            for trans in transactions:
                # Skip if it's a duplicate
                if self.is_duplicate_in_account(trans, account_id):
                    duplicate_count += 1
                    continue
                
                # Process the transaction
                withdrawal = float(abs(trans.amount)) if trans.amount < 0 else 0.0
                deposit = float(trans.amount) if trans.amount > 0 else 0.0
                
                self.db.execute("""
                    INSERT INTO transactions (
                        date, account, description, withdrawal, deposit,
                        is_matched, is_internal_transfer
                    ) VALUES (?, ?, ?, ?, ?, 0, 0)
                """, (
                    trans.date.isoformat(),
                    account_id,
                    trans.payee + (f" - {trans.memo}" if trans.memo else ''),
                    withdrawal,
                    deposit
                ))
                
                imported_count += 1
            
            self.db.commit()
            
            # After import, detect any internal transfers
            self.detect_internal_transfers()
            
            return imported_count, duplicate_count
            
        except Exception as e:
            self.db.rollback()
            print(f"Error importing transactions: {e}")
            raise
    
    def is_duplicate_in_account(self, trans: QIFTransaction, account_id: str, window_days: int = 3) -> bool:
        """
        Check if a transaction already exists in the specified bank account.
        
        Args:
            trans (QIFTransaction): The transaction to check
            account_id (str): The bank account ID to check against
            window_days (int): Number of days to look around the transaction date

        Returns:
            bool: True if a matching transaction is found in the specified account
        """
        try:
            # Calculate date range for checking
            start_date = (trans.date - timedelta(days=window_days)).isoformat()
            end_date = (trans.date + timedelta(days=window_days)).isoformat()
            
            # Determine withdrawal/deposit amounts
            withdrawal = float(abs(trans.amount)) if trans.amount < 0 else 0.0
            deposit = float(trans.amount) if trans.amount > 0 else 0.0
            
            # Build description
            description = trans.payee + (f" - {trans.memo}" if trans.memo else '')
            
            # Query for matching transactions in the same account
            cursor = self.db.execute("""
                SELECT COUNT(*) FROM transactions
                WHERE date BETWEEN ? AND ?
                AND account = ?
                AND ABS(withdrawal - ?) < 0.01
                AND ABS(deposit - ?) < 0.01
                AND description = ?
            """, (start_date, end_date, account_id, withdrawal, deposit, description))
            
            return cursor.fetchone()[0] > 0
            
        except Exception as e:
            print(f"Error checking for duplicate transaction: {e}")
            return False

    def create_auto_categorisation_rule(self, rule_data: dict) -> bool:
        """
        Create a new auto-categorisation rule
        
        Args:
            rule_data: Dictionary containing rule configuration:
                {
                    'category_id': str,
                    'description': {
                        'text': str,
                        'case_sensitive': bool
                    },
                    'amount': {
                        'operator': str,
                        'value': Decimal,
                        'value2': Optional[Decimal]
                    },
                    'account': {
                        'text': str
                    },
                    'date_range': str,
                    'apply_to': {
                        'existing': bool,
                        'future': bool
                    }
                }
        
        Returns:
            bool: True if rule was created successfully, False otherwise
        """
        try:
            self.db.execute("""
                INSERT INTO auto_categorisation_rules (
                    category_id, description_text, description_case_sensitive,
                    amount_operator, amount_value, amount_value2,
                    account_text, date_range, apply_future
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rule_data['category_id'],
                rule_data['description']['text'],
                rule_data['description']['case_sensitive'],
                rule_data['amount']['operator'],
                float(rule_data['amount']['value']) if rule_data['amount']['value'] else None,
                float(rule_data['amount']['value2']) if rule_data['amount']['value2'] else None,
                rule_data['account']['text'],
                rule_data['date_range'],
                rule_data['apply_to']['future']
            ))
            
            self.db.commit()
            
            # Apply to existing transactions if requested
            if rule_data['apply_to']['existing']:
                self.apply_auto_categorisation_rules()
                
            return True
            
        except Exception as e:
            print(f"Error creating auto-categorisation rule: {e}")
            self.db.rollback()
            return False

    def apply_auto_categorisation_rules(self):
        """Apply auto-categorisation rules to uncategorised transactions"""
        try:
            # Get all rules
            cursor = self.db.execute("SELECT * FROM auto_categorisation_rules")
            rules = cursor.fetchall()

            # Get uncategorised transactions
            transactions = self.get_transactions("uncategorised")

            for trans in transactions:
                for rule in rules:
                    if self._transaction_matches_rule(trans, rule):
                        self.update_transaction_category(trans.id, rule[1])  # rule[1] is category_id
                        break  # Stop after first matching rule

            self.db.commit()
        except Exception as e:
            print(f"Error applying auto-categorisation rules: {e}")

    def get_auto_categorisation_rules(self) -> List[Dict]:
        """
        Get all auto-categorisation rules with their associated category names.
        
        Returns:
            List[Dict]: List of dictionaries containing rule information:
            {
                'id': int,
                'category_id': str,
                'category_name': str,
                'description_text': str,
                'description_case_sensitive': bool,
                'amount_operator': str,
                'amount_value': float,
                'amount_value2': float,
                'account_text': str,
                'date_range': str,
                'apply_future': bool
            }
        """
        try:
            # Join with categories table to get category names
            cursor = self.db.execute("""
                SELECT 
                    r.id,
                    r.category_id,
                    c.name as category_name,
                    r.description_text,
                    r.description_case_sensitive,
                    r.amount_operator,
                    r.amount_value,
                    r.amount_value2,
                    r.account_text,
                    r.date_range,
                    r.apply_future
                FROM auto_categorisation_rules r
                JOIN categories c ON r.category_id = c.id
                ORDER BY c.name, r.description_text
            """)
            
            rules = []
            for row in cursor:
                rules.append({
                    'id': row[0],
                    'category_id': row[1],
                    'category_name': row[2],
                    'description_text': row[3],
                    'description_case_sensitive': bool(row[4]),
                    'amount_operator': row[5],
                    'amount_value': row[6],
                    'amount_value2': row[7],
                    'account_text': row[8],
                    'date_range': row[9],
                    'apply_future': bool(row[10])
                })
            
            return rules
            
        except Exception as e:
            print(f"Error getting auto-categorisation rules: {e}")
            return []

    def update_auto_categorisation_rule(self, rule_id: int, rule_data: Dict) -> bool:
        """
        Update an existing auto-categorisation rule
        
        Args:
            rule_id: ID of the rule to update
            rule_data: Dictionary containing updated rule configuration
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            self.db.execute("""
                UPDATE auto_categorisation_rules
                SET category_id = ?,
                    description_text = ?,
                    description_case_sensitive = ?,
                    amount_operator = ?,
                    amount_value = ?,
                    amount_value2 = ?,
                    account_text = ?,
                    date_range = ?,
                    apply_future = ?
                WHERE id = ?
            """, (
                rule_data['category_id'],
                rule_data['description']['text'],
                rule_data['description']['case_sensitive'],
                rule_data['amount']['operator'],
                float(rule_data['amount']['value']) if rule_data['amount']['value'] else None,
                float(rule_data['amount']['value2']) if rule_data['amount']['value2'] else None,
                rule_data['account']['text'],
                rule_data['date_range'],
                rule_data['apply_to']['future'],
                rule_id
            ))
            
            self.db.commit()
            
            # Apply to existing transactions if requested
            if rule_data['apply_to']['existing']:
                self.apply_auto_categorisation_rules()
                
            return True
            
        except Exception as e:
            print(f"Error updating auto-categorisation rule: {e}")
            self.db.rollback()
            return False

    def delete_auto_categorisation_rule(self, rule_id: int) -> bool:
        """
        Delete an auto-categorisation rule
        
        Args:
            rule_id: ID of the rule to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            self.db.execute(
                "DELETE FROM auto_categorisation_rules WHERE id = ?",
                (rule_id,)
            )
            self.db.commit()
            return True
            
        except Exception as e:
            print(f"Error deleting auto-categorisation rule: {e}")
            self.db.rollback()
            return False

    def _transaction_matches_rule(self, transaction, rule) -> bool:
        """Check if a transaction matches an auto-categorisation rule"""
        # Unpack rule data
        (rule_id, category_id, desc_text, desc_case, amount_op, 
         amount_val, amount_val2, account_text, date_range, apply_future) = rule

        # Description matching
        if desc_text:
            trans_desc = transaction.description
            rule_desc = desc_text
            if not desc_case:
                trans_desc = trans_desc.lower()
                rule_desc = rule_desc.lower()
            if rule_desc not in trans_desc:
                return False

        # Account matching
        if account_text and account_text.lower() not in transaction.account.lower():
            return False

        # Amount matching
        amount = float(transaction.withdrawal or transaction.deposit)
        if amount_op and amount_val is not None:
            if amount_op == "Equal to" and amount != float(amount_val):
                return False
            elif amount_op == "Greater than" and amount <= float(amount_val):
                return False
            elif amount_op == "Less than" and amount >= float(amount_val):
                return False
            elif amount_op == "Between" and amount_val2 is not None:
                if not (float(amount_val) <= amount <= float(amount_val2)):
                    return False

        # Date matching
        from datetime import datetime, timedelta
        trans_date = transaction.date
        if date_range:
            today = datetime.now()
            if date_range == "Last 30 days":
                if trans_date < (today - timedelta(days=30)):
                    return False
            elif date_range == "Last 90 days":
                if trans_date < (today - timedelta(days=90)):
                    return False
            elif date_range == "This year":
                if trans_date.year != today.year:
                    return False

        return True
    
    def update_transaction_category(self, transaction_id: int, category_id: str) -> bool:
        """Update the category of a transaction"""
        try:
            self.db.execute("""
                UPDATE transactions 
                SET category_id = ?
                WHERE id = ?
            """, (category_id, transaction_id))
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error updating transaction category: {e}")
            return False

    def check_account_duplicates(self, transaction: QIFTransaction, account_id: str, window_days: int = 3) -> bool:
        """
        Check if a transaction already exists in the database for the specified account.
        
        Args:
            transaction (QIFTransaction): The transaction to check
            account_id (str): The bank account ID to check against
            window_days (int): Number of days to look around the transaction date
        
        Returns:
            bool: True if a matching transaction is found in the specified account
        """
        try:
            # Calculate date range for checking
            start_date = (transaction.date - timedelta(days=window_days)).isoformat()
            end_date = (transaction.date + timedelta(days=window_days)).isoformat()
            
            # Determine withdrawal/deposit amounts
            withdrawal = float(abs(transaction.amount)) if transaction.amount < 0 else 0.0
            deposit = float(transaction.amount) if transaction.amount > 0 else 0.0
            
            # Build the description as it would appear in the database
            description = transaction.payee + (f" - {transaction.memo}" if transaction.memo else '')
            
            # Query for matching transactions in the same account
            cursor = self.db.execute("""
                SELECT COUNT(*) FROM transactions
                WHERE date BETWEEN ? AND ?
                AND ABS(withdrawal - ?) < 0.01  -- Use small epsilon for float comparison
                AND ABS(deposit - ?) < 0.01
                AND description = ?
                AND account = ?
            """, (start_date, end_date, withdrawal, deposit, description, account_id))
            
            count = cursor.fetchone()[0]
            return count > 0
            
        except Exception as e:
            print(f"Error checking account duplicates: {e}")
            return False
        
    def detect_internal_transfers(self) -> bool:
        """
        Detect and mark internal transfers between bank accounts.
        Looks for matching amounts (one positive, one negative) on the same day or next day.
        
        Returns:
            bool: True if successful, False if error occurred
        """
        try:
            self.db.execute("BEGIN TRANSACTION")
            
            # Get all bank account IDs
            cursor = self.db.execute("""
                SELECT id FROM categories 
                WHERE is_bank_account = 1
                AND category_type = ?
            """, (CategoryType.TRANSACTION.value,))
            
            bank_accounts = [row[0] for row in cursor]
            
            # Look for potential transfers between accounts
            for account_id in bank_accounts:
                # Get unmatched transactions for this account
                cursor = self.db.execute("""
                    SELECT id, date, withdrawal, deposit 
                    FROM transactions
                    WHERE account = ?
                    AND is_matched = 0
                    ORDER BY date
                """, (account_id,))
                
                for trans_id, date, withdrawal, deposit in cursor.fetchall():
                    amount = deposit - withdrawal  # Net amount
                    
                    if amount == 0:
                        continue  # Skip zero-amount transactions
                    
                    # Look for matching opposite transaction in other accounts
                    date_obj = datetime.fromisoformat(date)
                    next_day = (date_obj + timedelta(days=1)).isoformat()
                    
                    # Find matching transaction with opposite amount
                    match_cursor = self.db.execute("""
                        SELECT id 
                        FROM transactions
                        WHERE account != ?
                        AND date BETWEEN ? AND ?
                        AND ABS((deposit - withdrawal) + ?) < 0.01
                        AND is_matched = 0
                        LIMIT 1
                    """, (account_id, date, next_day, amount))
                    
                    match = match_cursor.fetchone()
                    if match:
                        # Mark both transactions as matched internal transfers
                        self.db.execute("""
                            UPDATE transactions
                            SET is_matched = 1,
                                is_internal_transfer = 1
                            WHERE id IN (?, ?)
                        """, (trans_id, match[0]))
            
            self.db.execute("COMMIT")
            return True
            
        except Exception as e:
            self.db.execute("ROLLBACK")
            print(f"Error detecting internal transfers: {e}")
            return False

    def find_database_duplicates(self, transactions: List[QIFTransaction], window_days: int = 3) -> List[Dict]:
        """
        Find potential duplicate transactions in the database.
        
        Args:
            transactions: List of transactions to check
            window_days: Number of days to look around each transaction date for matches
            
        Returns:
            List of dictionaries containing duplicate information:
            {
                'transaction': QIFTransaction,
                'count': int (number of matches found),
                'group_id': str (identifier for grouping related duplicates)
            }
        """
        duplicates = []
        
        try:
            for trans in transactions:
                # Calculate date range for checking
                start_date = (trans.date - timedelta(days=window_days)).isoformat()
                end_date = (trans.date + timedelta(days=window_days)).isoformat()
                
                # Determine withdrawal/deposit amounts
                withdrawal = float(abs(trans.amount)) if trans.amount < 0 else 0.0
                deposit = float(trans.amount) if trans.amount > 0 else 0.0
                
                # Build description as it would appear in the database
                description = trans.payee + (f" - {trans.memo}" if trans.memo else '')
                
                # Query for matching transactions
                cursor = self.db.execute("""
                    SELECT COUNT(*) 
                    FROM transactions
                    WHERE date BETWEEN ? AND ?
                    AND ABS(withdrawal - ?) < 0.01  -- Use small epsilon for float comparison
                    AND ABS(deposit - ?) < 0.01
                    AND description = ?
                """, (start_date, end_date, withdrawal, deposit, description))
                
                match_count = cursor.fetchone()[0]
                
                if match_count > 0:
                    duplicates.append({
                        'transaction': trans,
                        'count': match_count,
                        # Generate a simple group ID based on date and amount
                        'group_id': f"{trans.date.strftime('%Y%m%d')}_{abs(trans.amount)}"
                    })
        
        except Exception as e:
            print(f"Error checking for database duplicates: {e}")
        
        return duplicates