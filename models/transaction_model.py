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
        Create a new auto-categorisation rule.
        For internal transfers, we use '0' as a special category_id to indicate internal transfer.
        
        Args:
            rule_data: Dictionary containing rule configuration
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.db.execute("BEGIN TRANSACTION")
            
            # For internal transfers, use '0' as a special category_id
            category_id = '0' if rule_data['category_id'] is None else rule_data['category_id']
            
            # Insert main rule
            cursor = self.db.execute("""
                INSERT INTO auto_categorisation_rules (
                    category_id, amount_operator, amount_value, amount_value2,
                    account_id, date_range, apply_future
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                category_id,
                rule_data['amount']['operator'],
                float(rule_data['amount']['value']) if rule_data['amount']['value'] else None,
                float(rule_data['amount']['value2']) if rule_data['amount']['value2'] else None,
                rule_data['account']['id'],
                rule_data['date_range'],
                rule_data['apply_to']['future']
            ))
            
            rule_id = cursor.lastrowid
            
            # Insert description conditions
            for i, condition in enumerate(rule_data['description']['conditions']):
                self.db.execute("""
                    INSERT INTO auto_categorisation_rule_descriptions (
                        rule_id, operator, description_text, case_sensitive, sequence
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    rule_id,
                    condition['operator'],
                    condition['text'],
                    condition['case_sensitive'],
                    i
                ))
            
            self.db.execute("COMMIT")
            
            # Apply to existing transactions if requested
            if rule_data['apply_to']['existing']:
                self.apply_auto_categorisation_rules()
                
            return True
            
        except Exception as e:
            self.db.execute("ROLLBACK")
            print(f"Error creating auto-categorisation rule: {e}")
            return False

    def get_auto_categorisation_rules(self) -> List[Dict]:
        """
        Get all auto-categorisation rules with their conditions
        
        Returns:
            List[Dict]: List of rule dictionaries with all their details
        """
        try:
            # Get main rules
            cursor = self.db.execute("""
                SELECT 
                    r.id,
                    r.category_id,
                    CASE 
                        WHEN r.category_id = '0' THEN NULL
                        ELSE c.name 
                    END as category_name,
                    r.amount_operator,
                    r.amount_value,
                    r.amount_value2,
                    r.account_id,
                    COALESCE(ba.name, 'Any') as account_name,
                    r.date_range,
                    r.apply_future
                FROM auto_categorisation_rules r
                LEFT JOIN categories c ON r.category_id = c.id AND r.category_id != '0'
                LEFT JOIN bank_accounts ba ON r.account_id = ba.id
                ORDER BY c.name
            """)
            
            rules = []
            for row in cursor:
                rule_id = row[0]
                
                # Get description conditions for this rule
                desc_cursor = self.db.execute("""
                    SELECT operator, description_text, case_sensitive
                    FROM auto_categorisation_rule_descriptions
                    WHERE rule_id = ?
                    ORDER BY sequence
                """, (rule_id,))
                
                # Convert description conditions to list of dictionaries
                description_conditions = []
                for desc_row in desc_cursor:
                    description_conditions.append({
                        'operator': desc_row[0],
                        'text': desc_row[1],
                        'case_sensitive': bool(desc_row[2])
                    })
                
                rules.append({
                    'id': rule_id,
                    'category_id': row[1],
                    'category_name': row[2],
                    'description_conditions': description_conditions,
                    'amount_operator': row[3],
                    'amount_value': row[4],
                    'amount_value2': row[5],
                    'account_id': row[6],
                    'account_name': row[7],
                    'date_range': row[8],
                    'apply_future': bool(row[9])
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
            self.db.execute("BEGIN TRANSACTION")
            
            # Handle internal transfers by using '0' as category_id
            category_id = '0' if rule_data['category_id'] is None else rule_data['category_id']
            
            # Update main rule
            self.db.execute("""
                UPDATE auto_categorisation_rules
                SET category_id = ?,
                    amount_operator = ?,
                    amount_value = ?,
                    amount_value2 = ?,
                    account_id = ?,
                    date_range = ?,
                    apply_future = ?
                WHERE id = ?
            """, (
                category_id,
                rule_data['amount']['operator'],
                float(rule_data['amount']['value']) if rule_data['amount']['value'] else None,
                float(rule_data['amount']['value2']) if rule_data['amount']['value2'] else None,
                rule_data['account']['id'],
                rule_data['date_range'],
                rule_data['apply_to']['future'],
                rule_id
            ))
            
            # Delete existing description conditions
            self.db.execute("""
                DELETE FROM auto_categorisation_rule_descriptions
                WHERE rule_id = ?
            """, (rule_id,))
            
            # Insert new description conditions
            for i, condition in enumerate(rule_data['description']['conditions']):
                self.db.execute("""
                    INSERT INTO auto_categorisation_rule_descriptions (
                        rule_id, operator, description_text, case_sensitive, sequence
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    rule_id,
                    condition['operator'],
                    condition['text'],
                    condition['case_sensitive'],
                    i
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

    def _transaction_matches_rule(self, transaction: Transaction, rule: tuple) -> bool:
        """
        Check if a transaction matches an auto-categorisation rule
        
        Args:
            transaction: Transaction object to check
            rule: Tuple from database containing rule criteria
            
        Returns:
            bool: True if transaction matches rule criteria
        """
        try:
            # Extract rule components from tuple
            (rule_id, category_id, account_id, amount_operator, 
            amount_value, amount_value2, date_range) = rule

            # Get description conditions for this rule
            cursor = self.db.execute("""
                SELECT operator, description_text, case_sensitive
                FROM auto_categorisation_rule_descriptions
                WHERE rule_id = ?
                ORDER BY sequence
            """, (rule_id,))
            description_conditions = cursor.fetchall()

            # Check account if specified
            if account_id and transaction.account != account_id:
                return False

            # Check description conditions
            if not self._check_description_conditions(transaction.description, description_conditions):
                return False

            # Check amount
            amount = transaction.withdrawal or transaction.deposit
            if not self._check_amount_condition(amount, amount_operator, amount_value, amount_value2):
                return False

            # Check date range
            if not self._check_date_condition(transaction.date, date_range):
                return False

            return True

        except Exception as e:
            print(f"Error checking rule match: {e}")
            return False

    def _check_description_conditions(self, description: str, conditions: List[tuple]) -> bool:
        """
        Check if a description matches the conditions using AND/OR logic
        
        Args:
            description: Transaction description to check
            conditions: List of tuples (operator, text, case_sensitive)
            
        Returns:
            bool: True if description matches the conditions
        """
        if not conditions:
            return True

        # First condition (no operator)
        result = self._check_single_description(
            description,
            conditions[0][1],  # description_text
            conditions[0][2]   # case_sensitive
        )

        # Process subsequent conditions with operators
        for condition in conditions[1:]:
            operator = condition[0]  # AND/OR
            matches = self._check_single_description(
                description,
                condition[1],  # description_text
                condition[2]   # case_sensitive
            )

            if operator == 'AND':
                result = result and matches
            else:  # OR
                result = result or matches

        return result

    def _check_single_description(self, description: str, match_text: str, case_sensitive: bool) -> bool:
        """
        Check if a single description condition matches
        
        Args:
            description: Transaction description to check
            match_text: Text to match against
            case_sensitive: Whether to match case sensitively
            
        Returns:
            bool: True if description matches the condition
        """
        if not case_sensitive:
            description = description.lower()
            match_text = match_text.lower()
        return match_text in description

    def _check_amount_condition(self, amount: Decimal, operator: str, 
                            value1: Optional[float], value2: Optional[float]) -> bool:
        """
        Check if an amount matches the amount condition
        
        Args:
            amount: Transaction amount to check
            operator: Comparison operator ("Equal to", "Greater than", etc.)
            value1: Primary comparison value
            value2: Secondary comparison value (for "Between" operator)
            
        Returns:
            bool: True if amount matches the condition
        """
        if operator == "Any" or not value1:
            return True

        amount = abs(amount)  # Work with absolute values
        value1 = Decimal(str(value1))
        value2 = Decimal(str(value2)) if value2 else None

        if operator == "Equal to":
            return abs(amount - value1) < Decimal('0.01')
        elif operator == "Greater than":
            return amount > value1
        elif operator == "Less than":
            return amount < value1
        elif operator == "Between" and value2:
            return value1 <= amount <= value2

        return False

    def _check_date_condition(self, trans_date: datetime, date_range: str) -> bool:
        """
        Check if a date falls within the specified range
        
        Args:
            trans_date: Transaction date to check
            date_range: Date range specification
            
        Returns:
            bool: True if date falls within the range
        """
        if not date_range or date_range == "Any":
            return True

        today = datetime.now()

        if date_range == "Last 30 days":
            return (today - trans_date).days <= 30
        elif date_range == "Last 90 days":
            return (today - trans_date).days <= 90
        elif date_range == "This year":
            return trans_date.year == today.year

        return True

    def apply_auto_categorisation_rules(self):
        """Apply auto-categorisation rules to uncategorised transactions"""
        try:
            # Get all active rules
            cursor = self.db.execute("""
                SELECT id, category_id, account_id, amount_operator, 
                    amount_value, amount_value2, date_range
                FROM auto_categorisation_rules
                WHERE apply_future = 1
            """)
            rules = cursor.fetchall()

            # Get uncategorised transactions
            transactions = self.get_transactions("uncategorised")

            for trans in transactions:
                for rule in rules:
                    if self._transaction_matches_rule(trans, rule):
                        category_id = rule[1]  # rule[1] is category_id
                        
                        if category_id == '0':  # Special case for internal transfers
                            # This is an internal transfer rule
                            self.db.execute("""
                                UPDATE transactions
                                SET category_id = NULL,
                                    is_internal_transfer = 1,
                                    is_matched = 1
                                WHERE id = ?
                            """, (trans.id,))
                        else:
                            # Regular category rule
                            self.db.execute("""
                                UPDATE transactions
                                SET category_id = ?,
                                    is_internal_transfer = 0,
                                    is_matched = 0
                                WHERE id = ?
                            """, (category_id, trans.id))
                        break  # Stop after first matching rule

            self.db.commit()

        except Exception as e:
            print(f"Error applying auto-categorisation rules: {e}")
            self.db.rollback()
    
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