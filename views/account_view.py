# File: views/account_view.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt
from views.bank_account_dialog import AddBankAccountDialog
from models.bank_account_model import BankAccountModel
from decimal import Decimal

class AccountView(QWidget):
    """Widget for displaying bank accounts"""
    def __init__(self, bank_account_model: BankAccountModel):
        super().__init__()
        self.bank_account_model = bank_account_model
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        
        # Create accounts table
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(7)
        self.accounts_table.setHorizontalHeaderLabels([
            "Account Name", 
            "Bank Name",
            "BSB",
            "Account Number",
            "Current Balance",
            "Last Import",
            "Notes"
        ])
        
        # Configure table
        header = self.accounts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Account name stretches
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.Stretch)  # Notes stretches
        
        # Set table properties
        self.accounts_table.setAlternatingRowColors(True)
        self.accounts_table.verticalHeader().setVisible(False)
        self.accounts_table.setEditTriggers(QTableWidget.NoEditTriggers)  # Make read-only
        
        layout.addWidget(self.accounts_table)
        
        # Initial data load
        self.refresh_accounts()
    
    def refresh_accounts(self):
        """Refresh the accounts table data"""
        accounts = self.bank_account_model.get_accounts()
        self.accounts_table.setRowCount(len(accounts))
        
        for row, account in enumerate(accounts):
            # Account Name
            self.accounts_table.setItem(row, 0, QTableWidgetItem(account.name))
            # Bank Name
            self.accounts_table.setItem(row, 1, QTableWidgetItem(account.bank_name))
            # BSB
            bsb = account.bsb[:3] + "-" + account.bsb[3:] if account.bsb else ""
            self.accounts_table.setItem(row, 2, QTableWidgetItem(bsb))
            # Account Number
            self.accounts_table.setItem(row, 3, QTableWidgetItem(account.account_number))
            # Current Balance
            balance_item = QTableWidgetItem(f"${account.current_balance:,.2f}")
            balance_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.accounts_table.setItem(row, 4, balance_item)
            # Last Import
            self.accounts_table.setItem(row, 5, QTableWidgetItem(
                account.last_import_date or "Never"))
            # Notes
            self.accounts_table.setItem(row, 6, QTableWidgetItem(account.notes or ""))