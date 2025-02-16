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
    def __init__(self, file_duplicates: List[Dict], db_duplicates: List[Dict], parent=None):
        super().__init__(parent)
        self.file_duplicates = file_duplicates
        self.db_duplicates = db_duplicates
        self.selected_transactions: Set[tuple] = set()  # Store selected transactions
        self._setup_ui()
    
    def _setup_ui(self):
        """Initialise the user interface"""
        self.setWindowTitle("Duplicate Transaction Manager")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tabs = QTabWidget()
        
        # File duplicates tab
        file_tab = QWidget()
        file_layout = QVBoxLayout(file_tab)
        file_layout.addWidget(QLabel("Duplicates found within import file:"))
        self.file_table = self._create_duplicate_table(self.file_duplicates)
        file_layout.addWidget(self.file_table)
        tabs.addTab(file_tab, "Import File Duplicates")
        
        # Database duplicates tab
        db_tab = QWidget()
        db_layout = QVBoxLayout(db_tab)
        db_layout.addWidget(QLabel("Duplicates found in existing database:"))
        self.db_table = self._create_duplicate_table(self.db_duplicates)
        db_layout.addWidget(self.db_table)
        tabs.addTab(db_tab, "Database Duplicates")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        import_selected = QPushButton("Import Selected")
        import_selected.clicked.connect(self.accept)
        skip_all = QPushButton("Skip All Duplicates")
        skip_all.clicked.connect(self.reject)
        button_layout.addWidget(import_selected)
        button_layout.addWidget(skip_all)
        layout.addLayout(button_layout)
    
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
        
        # Get selections from file duplicates table
        for row in range(self.file_table.rowCount()):
            checkbox = self.file_table.cellWidget(row, 0)
            if checkbox.isChecked():
                dup = self.file_duplicates[row]
                selected.add((
                    dup['transaction'].date,
                    dup['transaction'].amount,
                    dup['transaction'].payee,
                    dup['transaction'].memo
                ))
        
        # Get selections from database duplicates table
        for row in range(self.db_table.rowCount()):
            checkbox = self.db_table.cellWidget(row, 0)
            if checkbox.isChecked():
                dup = self.db_duplicates[row]
                selected.add((
                    dup['transaction'].date,
                    dup['transaction'].amount,
                    dup['transaction'].payee,
                    dup['transaction'].memo
                ))
        
        return selected