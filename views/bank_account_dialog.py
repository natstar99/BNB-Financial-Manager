# File: views/bank_account_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFormLayout, QMessageBox
)
from models.bank_account_model import BankAccount

class AddBankAccountDialog(QDialog):
    """Dialog for adding a new bank account"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the dialog's user interface"""
        self.setWindowTitle("Add Bank Account")
        layout = QVBoxLayout(self)
        
        # Create form layout for inputs
        form_layout = QFormLayout()
        
        # Account name input
        self.name_edit = QLineEdit()
        form_layout.addRow("Account Name:", self.name_edit)
        
        # BSB number input with validation
        self.bsb_edit = QLineEdit()
        self.bsb_edit.setMaxLength(6)
        self.bsb_edit.setPlaceholderText("000-000")
        form_layout.addRow("BSB Number:", self.bsb_edit)
        
        # Account number input
        self.account_edit = QLineEdit()
        self.account_edit.setPlaceholderText("Enter account number")
        form_layout.addRow("Account Number:", self.account_edit)
        
        # Bank name input
        self.bank_edit = QLineEdit()
        self.bank_edit.setPlaceholderText("Enter bank name")
        form_layout.addRow("Bank Name:", self.bank_edit)
        
        # Notes input (optional)
        self.notes_edit = QLineEdit()
        self.notes_edit.setPlaceholderText("Optional notes")
        form_layout.addRow("Notes:", self.notes_edit)
        
        layout.addLayout(form_layout)
        
        # Add buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.validate_and_accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
    
    def validate_and_accept(self):
        """Validate the input before accepting"""
        # Check required fields
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Account name is required")
            return
        
        # Validate BSB format (XXX-XXX or XXXXXX)
        bsb = self.bsb_edit.text().replace("-", "")
        if not bsb.isdigit() or len(bsb) != 6:
            QMessageBox.warning(self, "Validation Error", 
                              "BSB must be 6 digits (XXX-XXX)")
            return
        
        # Validate account number
        if not self.account_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", 
                              "Account number is required")
            return
        
        if not self.bank_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Bank name is required")
            return
        
        self.accept()
    
    def get_account_data(self) -> dict:
        """Get the entered account data"""
        return {
            'name': self.name_edit.text().strip(),
            'bsb': self.bsb_edit.text().replace("-", ""),  # Store without hyphens
            'account_number': self.account_edit.text().strip(),
            'bank_name': self.bank_edit.text().strip(),
            'notes': self.notes_edit.text().strip() or None
        }