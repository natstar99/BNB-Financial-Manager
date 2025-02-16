# File: utils/qif_parser.py

from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class QIFTransaction:
    """Represents a transaction from a QIF file"""
    date: datetime
    amount: Decimal
    payee: str
    memo: Optional[str] = None
    category: Optional[str] = None
    account: Optional[str] = None

class QIFParser:
    """Parser for QIF (Quicken Interchange Format) files"""
    
    def __init__(self):
        self.transactions: List[QIFTransaction] = []
        self._current_transaction: Dict = {}
    
    def parse_file(self, file_path: str) -> List[QIFTransaction]:
        """Parse a QIF file and return list of transactions"""
        self.transactions = []
        self._current_transaction = {}
        
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        # Skip header if present
        start_idx = 0
        if lines and lines[0].startswith('!Type:'):
            start_idx = 1
        
        for line in lines[start_idx:]:
            line = line.strip()
            if not line:
                continue
            
            if line == '^':  # End of transaction
                if self._current_transaction:
                    self._process_transaction()
                    self._current_transaction = {}
                continue
            
            code = line[0]
            value = line[1:].strip()
            
            self._process_field(code, value)
        
        # Process last transaction if exists
        if self._current_transaction:
            self._process_transaction()
        
        return self.transactions
    
    def _process_field(self, code: str, value: str):
        """Process a single QIF field"""
        if code == 'D':  # Date
            self._current_transaction['date'] = self._parse_date(value)
        elif code == 'T':  # Amount
            self._current_transaction['amount'] = self._parse_amount(value)
        elif code == 'P':  # Payee
            self._current_transaction['payee'] = value
        elif code == 'M':  # Memo
            self._current_transaction['memo'] = value
        elif code == 'L':  # Category
            self._current_transaction['category'] = value
        elif code == 'A':  # Account
            self._current_transaction['account'] = value
    
    def _process_transaction(self):
        """Process the current transaction and add it to the list"""
        # Required fields
        if 'date' not in self._current_transaction or 'amount' not in self._current_transaction:
            return
        
        transaction = QIFTransaction(
            date=self._current_transaction['date'],
            amount=self._current_transaction['amount'],
            payee=self._current_transaction.get('payee', ''),
            memo=self._current_transaction.get('memo'),
            category=self._current_transaction.get('category'),
            account=self._current_transaction.get('account')
        )
        self.transactions.append(transaction)
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse QIF date format"""
        try:
            # Handle common QIF date formats
            formats = [
                '%d/%m/%Y', '%m/%d/%Y',  # Standard formats
                '%d/%m/%y', '%m/%d/%y',  # Two-digit year formats
                '%Y-%m-%d'               # ISO format
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            raise ValueError(f"Unrecognised date format: {date_str}")
        except ValueError as e:
            print(f"Error parsing date {date_str}: {e}")
            return datetime.now()  # Fallback to current date
    
    def _parse_amount(self, amount_str: str) -> Decimal:
        """Parse QIF amount format"""
        try:
            # Remove any currency symbols and handle thousands separators
            clean_amount = amount_str.replace('$', '').replace(',', '')
            return Decimal(clean_amount)
        except Exception as e:
            print(f"Error parsing amount {amount_str}: {e}")
            return Decimal('0')