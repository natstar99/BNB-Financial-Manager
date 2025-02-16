# File: views/duplicate_manager.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QTabWidget, QWidget, QCheckBox, QHeaderView
)
from PySide6.QtCore import Qt
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Set
from utils.qif_parser import QIFTransaction

class DuplicateManagerDialog(QDialog):
    """Dialog for managing duplicate transactions during import"""
    def __init__(self, new_transactions: List[QIFTransaction], db_duplicates: List[Dict], parent=None):
        super().__init__(parent)
        self.new_transactions = new_transactions  # Renamed from file_duplicates
        self.db_duplicates = db_duplicates
        self.selected_transactions: Set[tuple] = set()
        self._setup_ui()
    
    def _setup_ui(self):
        """Initialise the user interface"""
        self.setWindowTitle("Transaction Import Manager")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tabs = QTabWidget()
        
        # New transactions tab (formerly file duplicates tab)
        new_tab = QWidget()
        new_layout = QVBoxLayout(new_tab)
        new_layout.addWidget(QLabel("New Transactions to Import:"))
        self.new_table = self._create_transaction_table(self.new_transactions)
        new_layout.addWidget(self.new_table)
        tabs.addTab(new_tab, "New Transactions")
        
        # Database duplicates tab
        db_tab = QWidget()
        db_layout = QVBoxLayout(db_tab)
        db_layout.addWidget(QLabel("Potential Duplicate Transactions:"))
        self.db_table = self._create_duplicate_table(self.db_duplicates)
        db_layout.addWidget(self.db_table)
        tabs.addTab(db_tab, "Potential Duplicates")
        
        layout.addWidget(tabs)
        
        # Add select all / deselect all buttons
        button_bar = QHBoxLayout()
        select_all = QPushButton("Select All New")
        select_all.clicked.connect(self._select_all_new)
        deselect_all = QPushButton("Deselect All")
        deselect_all.clicked.connect(self._deselect_all)
        button_bar.addWidget(select_all)
        button_bar.addWidget(deselect_all)
        layout.addLayout(button_bar)
        
        # Import/Cancel buttons
        button_layout = QHBoxLayout()
        import_selected = QPushButton("Import Selected")
        import_selected.clicked.connect(self.accept)
        skip_all = QPushButton("Cancel Import")
        skip_all.clicked.connect(self.reject)
        button_layout.addWidget(import_selected)
        button_layout.addWidget(skip_all)
        layout.addLayout(button_layout)

    def _create_transaction_table(self, transactions: List[QIFTransaction]) -> QTableWidget:
        """Create a table widget for displaying new transactions"""
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Import", "Date", "Description", "Withdrawal", "Deposit", "Account"
        ])
        
        # Configure table
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        table.setRowCount(len(transactions))
        
        for row, trans in enumerate(transactions):
            # Checkbox for selection
            checkbox = QCheckBox()
            checkbox.setChecked(True)  # Default to selected for new transactions
            table.setCellWidget(row, 0, checkbox)
            
            # Transaction details
            table.setItem(row, 1, QTableWidgetItem(
                trans.date.strftime("%Y-%m-%d")))
            table.setItem(row, 2, QTableWidgetItem(
                trans.payee + 
                (f" - {trans.memo}" if trans.memo else '')))
            
            amount = trans.amount
            withdrawal = abs(amount) if amount < 0 else 0
            deposit = amount if amount > 0 else 0
            
            table.setItem(row, 3, QTableWidgetItem(
                f"${withdrawal:.2f}" if withdrawal else ""))
            table.setItem(row, 4, QTableWidgetItem(
                f"${deposit:.2f}" if deposit else ""))
            table.setItem(row, 5, QTableWidgetItem(trans.account))
        
        return table

    def _select_all_new(self):
        """Select all new transactions"""
        for row in range(self.new_table.rowCount()):
            checkbox = self.new_table.cellWidget(row, 0)
            checkbox.setChecked(True)

    def _deselect_all(self):
        """Deselect all transactions"""
        for row in range(self.new_table.rowCount()):
            checkbox = self.new_table.cellWidget(row, 0)
            checkbox.setChecked(False)
    
    def _create_duplicate_table(self, duplicates: List[Dict]) -> QTableWidget:
        """Create a table widget for displaying duplicates"""
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "Import", "Date", "Description", "Withdrawal", "Deposit", 
            "Duplicate Count", "Group ID"
        ])
        
        # Configure table
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        
        table.setRowCount(len(duplicates))
        
        for row, dup in enumerate(duplicates):
            # Checkbox for selection
            checkbox = QCheckBox()
            table.setCellWidget(row, 0, checkbox)
            
            # Transaction details
            table.setItem(row, 1, QTableWidgetItem(
                dup['transaction'].date.strftime("%Y-%m-%d")))
            table.setItem(row, 2, QTableWidgetItem(
                dup['transaction'].payee + 
                (f" - {dup['transaction'].memo}" if dup['transaction'].memo else '')))
            
            amount = dup['transaction'].amount
            withdrawal = abs(amount) if amount < 0 else 0
            deposit = amount if amount > 0 else 0
            
            table.setItem(row, 3, QTableWidgetItem(
                f"${withdrawal:.2f}" if withdrawal else ""))
            table.setItem(row, 4, QTableWidgetItem(
                f"${deposit:.2f}" if deposit else ""))
            
            table.setItem(row, 5, QTableWidgetItem(str(dup['count'])))
            table.setItem(row, 6, QTableWidgetItem(str(dup['group_id'])))
        
        return table
    
    def get_selected_transactions(self) -> Set[tuple]:
        """Get the transactions selected for import"""
        selected = set()
        
        # Get selections from new transactions table
        for row in range(self.new_table.rowCount()):
            checkbox = self.new_table.cellWidget(row, 0)
            if checkbox.isChecked():
                trans = self.new_transactions[row]
                selected.add((
                    trans.date,
                    trans.amount,
                    trans.payee,
                    trans.memo
                ))
        
        # Get selections from database duplicates table
        for row in range(self.db_table.rowCount()):
            checkbox = self.db_table.cellWidget(row, 0)
            if checkbox.isChecked():
                dup = self.db_duplicates[row]
                trans = dup['transaction']
                selected.add((
                    trans.date,
                    trans.amount,
                    trans.payee,
                    trans.memo
                ))
        
        return selected