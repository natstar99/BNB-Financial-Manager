# File: views/multi_import_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QFileDialog, QComboBox,
    QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt
from views.bank_account_dialog import AddBankAccountDialog
from typing import List, Dict, Optional
import os

class MultiFileImportDialog(QDialog):
    """Dialog for importing multiple QIF files with account association"""
    def __init__(self, bank_account_model, parent=None):
        super().__init__(parent)
        self.bank_account_model = bank_account_model
        self.import_files: List[Dict] = []  # List of files to import
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the dialog's user interface"""
        self.setWindowTitle("Import QIF Files")
        self.resize(800, 400)
        layout = QVBoxLayout(self)
        
        # Add file button
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add QIF Files...")
        add_button.clicked.connect(self.add_files)
        button_layout.addWidget(add_button)
        
        layout.addLayout(button_layout)
        
        # Create table for showing files and account selection
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(3)
        self.file_table.setHorizontalHeaderLabels([
            "File Name", "Bank Account", "Remove"
        ])
        
        # Configure table
        header = self.file_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.file_table)
        
        # Add import and cancel buttons
        button_layout = QHBoxLayout()
        import_button = QPushButton("Import Files")
        import_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(import_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
    
    def add_files(self):
        """Add QIF files for import"""
        file_names, _ = QFileDialog.getOpenFileNames(
            self,
            "Select QIF Files",
            "",
            "QIF Files (*.qif);;All Files (*)"
        )
        
        if file_names:
            current_row = self.file_table.rowCount()
            for file_name in file_names:
                # Check if file is already in the list
                existing = False
                for row in range(self.file_table.rowCount()):
                    if self.file_table.item(row, 0).data(Qt.UserRole) == file_name:
                        existing = True
                        break
                
                if not existing:
                    self.file_table.insertRow(current_row)
                    
                    # Add filename
                    file_item = QTableWidgetItem(os.path.basename(file_name))
                    file_item.setData(Qt.UserRole, file_name)  # Store full path
                    self.file_table.setItem(current_row, 0, file_item)
                    
                    # Add account combo box
                    account_combo = QComboBox()
                    self.update_account_combo(account_combo)
                    self.file_table.setCellWidget(current_row, 1, account_combo)
                    
                    # Add remove button
                    remove_button = QPushButton("Remove")
                    remove_button.clicked.connect(
                        lambda _, row=current_row: self.remove_file(row))
                    self.file_table.setCellWidget(current_row, 2, remove_button)
                    
                    current_row += 1
    
    def add_bank_account(self):
        """Show dialog to add a new bank account"""
        dialog = AddBankAccountDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            account_data = dialog.get_account_data()
            if self.bank_account_model.add_account(**account_data):
                # Update all account combo boxes
                for row in range(self.file_table.rowCount()):
                    combo = self.file_table.cellWidget(row, 1)
                    self.update_account_combo(combo)
    
    def update_account_combo(self, combo: QComboBox):
        """Update the account selection combo box with valid bank accounts"""
        current_text = combo.currentText()
        combo.clear()
        
        # Get only valid bank accounts
        accounts = self.bank_account_model.get_accounts()
        if not accounts:
            combo.addItem("No accounts found - Please create a bank account in the Assets category", None)
            combo.setEnabled(False)
        else:
            combo.setEnabled(True)
            for account in accounts:
                display_text = f"{account.name} ({account.bank_name} - {account.account_number})"
                combo.addItem(display_text, account.id)
            
            # Restore previous selection if possible
            if current_text:
                index = combo.findText(current_text)
                if index >= 0:
                    combo.setCurrentIndex(index)
    
    def remove_file(self, row: int):
        """Remove a file from the import list"""
        self.file_table.removeRow(row)
    
    def get_import_files(self) -> List[Dict]:
        """Get the list of files to import with their associated accounts"""
        import_files = []
        
        for row in range(self.file_table.rowCount()):
            file_path = self.file_table.item(row, 0).data(Qt.UserRole)
            account_combo = self.file_table.cellWidget(row, 1)
            account_id = account_combo.currentData()
            
            if account_id:  # Only include if an account is selected
                import_files.append({
                    'file_path': file_path,
                    'account_id': account_id
                })
        
        return import_files
    
    def validate(self) -> bool:
        """Validate the import configuration"""
        if self.file_table.rowCount() == 0:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please add at least one file to import."
            )
            return False
        
        for row in range(self.file_table.rowCount()):
            account_combo = self.file_table.cellWidget(row, 1)
            if not account_combo.currentData():
                QMessageBox.warning(
                    self,
                    "Validation Error",
                    "Please add and select a bank account for each file."
                )
                return False
        
        return True
    
    def accept(self):
        """Override accept to validate first"""
        if self.validate():
            super().accept()