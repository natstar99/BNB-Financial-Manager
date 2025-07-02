"""
CSV Parser Module

This module provides functionality to parse CSV bank export files and convert
them into transaction objects for import into the financial manager.
"""

import csv
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class CSVTransaction:
    """Represents a transaction from a CSV file"""
    date: datetime
    amount: Decimal
    payee: str
    memo: Optional[str] = None
    category: Optional[str] = None
    account: Optional[str] = None
    balance: Optional[Decimal] = None
    transaction_id: Optional[str] = None

class CSVParser:
    """Parser for CSV (Comma Separated Values) bank export files"""
    
    def __init__(self):
        self.transactions: List[CSVTransaction] = []
        self.column_mapping: Dict[str, str] = {}
        
    def parse_file(self, file_path: str) -> List[CSVTransaction]:
        """Parse a CSV file and return list of transactions"""
        self.transactions = []
        
        with open(file_path, 'r', encoding='utf-8') as file:
            # Try to detect delimiter
            sample = file.read(1024)
            file.seek(0)
            
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            
            # Read CSV with detected delimiter
            reader = csv.DictReader(file, delimiter=delimiter)
            
            # Auto-detect column mapping from headers
            self._detect_column_mapping(reader.fieldnames)
            
            for row in reader:
                transaction = self._parse_row(row)
                if transaction:
                    self.transactions.append(transaction)
        
        return self.transactions
    
    def _detect_column_mapping(self, fieldnames: List[str]) -> None:
        """Auto-detect column mapping based on header names"""
        self.column_mapping = {}
        
        # Convert headers to lowercase for easier matching
        headers = [name.lower().strip() for name in fieldnames]
        original_headers = {name.lower().strip(): name for name in fieldnames}
        
        for i, header in enumerate(headers):
            # Date column detection
            if any(date_word in header for date_word in ['date', 'transaction date', 'posting date']):
                self.column_mapping['date'] = original_headers[header]
            
            # Description/Payee column detection
            elif any(desc_word in header for desc_word in ['description', 'payee', 'narrative', 'details', 'transaction details']):
                self.column_mapping['description'] = original_headers[header]
            
            # Amount columns - handle single amount or debit/credit split
            elif header in ['amount', 'transaction amount']:
                self.column_mapping['amount'] = original_headers[header]
            elif any(debit_word in header for debit_word in ['debit', 'withdrawal', 'out']):
                self.column_mapping['debit'] = original_headers[header]
            elif any(credit_word in header for credit_word in ['credit', 'deposit', 'in']):
                self.column_mapping['credit'] = original_headers[header]
            
            # Balance column detection
            elif any(balance_word in header for balance_word in ['balance', 'running balance', 'account balance']):
                self.column_mapping['balance'] = original_headers[header]
            
            # Reference/ID column detection
            elif any(ref_word in header for ref_word in ['reference', 'transaction id', 'ref', 'id']):
                self.column_mapping['reference'] = original_headers[header]
            
            # Category column detection (less common in bank exports)
            elif header in ['category', 'type', 'transaction type']:
                self.column_mapping['category'] = original_headers[header]
    
    def _parse_row(self, row: Dict[str, str]) -> Optional[CSVTransaction]:
        """Parse a single CSV row into a CSVTransaction"""
        try:
            # Parse date
            date_str = row.get(self.column_mapping.get('date', ''), '').strip()
            if not date_str:
                return None
            
            date = self._parse_date(date_str)
            
            # Parse amount - handle single amount or debit/credit columns
            amount = self._parse_amount(row)
            if amount is None:
                return None
            
            # Parse description/payee
            description = row.get(self.column_mapping.get('description', ''), '').strip()
            
            # Parse balance
            balance = None
            balance_str = row.get(self.column_mapping.get('balance', ''), '').strip()
            if balance_str:
                balance = self._parse_decimal(balance_str)
            
            # Parse reference/transaction ID
            transaction_id = row.get(self.column_mapping.get('reference', ''), '').strip() or None
            
            # Parse category if available
            category = row.get(self.column_mapping.get('category', ''), '').strip() or None
            
            return CSVTransaction(
                date=date,
                amount=amount,
                payee=description,
                memo=None,  # CSV typically combines description and memo
                category=category,
                account=None,  # Will be set during import
                balance=balance,
                transaction_id=transaction_id
            )
            
        except Exception:
            return None
    
    def _parse_amount(self, row: Dict[str, str]) -> Optional[Decimal]:
        """Parse amount from either single amount column or debit/credit columns"""
        # Try single amount column first
        if 'amount' in self.column_mapping:
            amount_str = row.get(self.column_mapping['amount'], '').strip()
            if amount_str:
                return self._parse_decimal(amount_str)
        
        # Try debit/credit columns
        debit_amount = Decimal('0')
        credit_amount = Decimal('0')
        
        if 'debit' in self.column_mapping:
            debit_str = row.get(self.column_mapping['debit'], '').strip()
            if debit_str:
                debit_amount = self._parse_decimal(debit_str) or Decimal('0')
        
        if 'credit' in self.column_mapping:
            credit_str = row.get(self.column_mapping['credit'], '').strip()
            if credit_str:
                credit_amount = self._parse_decimal(credit_str) or Decimal('0')
        
        # Calculate net amount (credits positive, debits negative)
        if debit_amount != Decimal('0') or credit_amount != Decimal('0'):
            return credit_amount - debit_amount
        
        return None
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse CSV date format"""
        try:
            # Handle common CSV date formats
            formats = [
                '%d/%m/%Y',    # DD/MM/YYYY (Australian standard)
                '%d-%m-%Y',    # DD-MM-YYYY
                '%Y-%m-%d',    # YYYY-MM-DD (ISO format)
                '%m/%d/%Y',    # MM/DD/YYYY (US format)
                '%d/%m/%y',    # DD/MM/YY
                '%d-%m-%y',    # DD-MM-YY
                '%Y/%m/%d',    # YYYY/MM/DD
                '%d %b %Y',    # DD Mon YYYY (e.g., "01 Jan 2024")
                '%d %B %Y',    # DD Month YYYY (e.g., "01 January 2024")
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            raise ValueError(f"Unrecognised date format: {date_str}")
        except ValueError:
            return datetime.now()  # Fallback to current date
    
    def _parse_decimal(self, amount_str: str) -> Optional[Decimal]:
        """Parse decimal amount from string"""
        try:
            # Remove currency symbols, spaces, and handle different formats
            clean_amount = amount_str.replace('$', '').replace(',', '').replace(' ', '')
            
            # Handle parentheses for negative amounts (e.g., "(25.50)" = -25.50)
            if clean_amount.startswith('(') and clean_amount.endswith(')'):
                clean_amount = '-' + clean_amount[1:-1]
            
            # Handle empty strings
            if not clean_amount or clean_amount == '-':
                return None
            
            return Decimal(clean_amount)
        except Exception:
            return None
    
    def get_latest_balance(self) -> Optional[Decimal]:
        """Get the balance from the most recent transaction"""
        if not self.transactions:
            return None
        
        # Find transaction with latest date that has a balance
        latest_transaction = max(
            (t for t in self.transactions if t.balance is not None),
            key=lambda t: t.date,
            default=None
        )
        
        return latest_transaction.balance if latest_transaction else None
    
    def validate_balance_progression(self) -> List[str]:
        """Validate that balance progression makes mathematical sense"""
        warnings = []
        
        # Sort transactions by date
        sorted_transactions = sorted(self.transactions, key=lambda t: t.date)
        
        for i in range(1, len(sorted_transactions)):
            current = sorted_transactions[i]
            previous = sorted_transactions[i-1]
            
            # Skip if either transaction doesn't have balance
            if current.balance is None or previous.balance is None:
                continue
            
            # Calculate expected balance
            expected_balance = previous.balance + current.amount
            
            # Allow for small rounding differences
            if abs(expected_balance - current.balance) > Decimal('0.01'):
                warnings.append(
                    f"Balance discrepancy on {current.date.strftime('%Y-%m-%d')}: "
                    f"Expected {expected_balance}, got {current.balance}"
                )
        
        return warnings