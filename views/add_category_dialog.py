# File: views/add_category_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QComboBox, QRadioButton, QButtonGroup, QCheckBox
)
from models.category_model import CategoryType, Category
from models.transaction_model import TaxType

class AddCategoryDialog(QDialog):
    def __init__(self, parent_category: Category = None, parent=None, allow_bank_account: bool = False):
        super().__init__(parent)
        self.parent_category = parent_category
        self.allow_bank_account = allow_bank_account
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("Add Category")
        layout = QVBoxLayout(self)
        
        # Parent category display
        if self.parent_category:
            parent_info = QLabel(f"Parent: {self.parent_category.name} ({self.parent_category.id})")
            layout.addWidget(parent_info)
        
        # Category name input
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
    
        # Add bank account option if allowed
        if self.allow_bank_account:
            self.bank_account_checkbox = QCheckBox("Create as Bank Account")
            self.bank_account_checkbox.stateChanged.connect(self._handle_bank_account_state)
            layout.addWidget(self.bank_account_checkbox)
        
        # Category type selection
        type_layout = QVBoxLayout()
        type_layout.addWidget(QLabel("Category Type:"))
        self.type_group = QButtonGroup()
        
        # Only show GROUP option if parent is root or group
        if self.parent_category and self.parent_category.category_type != CategoryType.TRANSACTION:
            self.group_radio = QRadioButton("Category Group (for organizing categories)")
            self.type_group.addButton(self.group_radio)
            type_layout.addWidget(self.group_radio)
        
        self.transaction_radio = QRadioButton("Transaction Category (for categorizing transactions)")
        self.type_group.addButton(self.transaction_radio)
        type_layout.addWidget(self.transaction_radio)
        
        # Select transaction by default
        self.transaction_radio.setChecked(True)
        layout.addLayout(type_layout)
        
        # Tax type selection (only for transaction categories)
        tax_layout = QHBoxLayout()
        tax_layout.addWidget(QLabel("Tax Type:"))
        self.tax_type_combo = QComboBox()
        self.tax_type_combo.addItem("None")  # Add a "None" option
        for tax_type in TaxType:
            self.tax_type_combo.addItem(tax_type.value)
        tax_layout.addWidget(self.tax_type_combo)
        layout.addLayout(tax_layout)
        
        # Enable/disable tax type based on category type selection
        if hasattr(self, 'group_radio'):
            self.group_radio.toggled.connect(
                lambda checked: self.tax_type_combo.setEnabled(not checked))
        
        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
    
    def _handle_bank_account_state(self, state):
        """Handle bank account checkbox state changes"""
        if state:
            # Force TRANSACTION type when bank account is selected
            if hasattr(self, 'group_radio'):
                self.transaction_radio.setChecked(True)
                self.group_radio.setEnabled(False)
            self.tax_type_combo.setEnabled(False)
        else:
            if hasattr(self, 'group_radio'):
                self.group_radio.setEnabled(True)
            self.tax_type_combo.setEnabled(True)
    
    def get_category_data(self):
        """Get the entered category data"""
        is_transaction = not hasattr(self, 'group_radio') or not self.group_radio.isChecked()
        category_type = CategoryType.TRANSACTION if is_transaction else CategoryType.GROUP
        tax_type = self.tax_type_combo.currentText() if is_transaction else None
        
        # Check if bank account is selected
        is_bank_account = (self.allow_bank_account and 
                         hasattr(self, 'bank_account_checkbox') and 
                         self.bank_account_checkbox.isChecked())
        
        data = {
            'name': self.name_edit.text().strip(),
            'category_type': category_type,
            'tax_type': tax_type if tax_type != "None" else None,
            'is_bank_account': is_bank_account
        }
        
        return data