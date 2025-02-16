# File: views/auto_categorise_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QCheckBox,
    QFormLayout, QGroupBox, QSpinBox
)
from decimal import Decimal

class AutoCategoryRuleDialog(QDialog):
    """Dialog for creating automatic categorisation rules"""
    def __init__(self, category, parent=None):
        super().__init__(parent)
        self.category = category
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle(f"Auto-Categorisation Rules - {self.category.name}")
        layout = QVBoxLayout(self)
        
        # Description matching
        desc_group = QGroupBox("Description Matching")
        desc_layout = QVBoxLayout(desc_group)
        
        self.desc_contains = QLineEdit()
        desc_layout.addWidget(QLabel("Contains text:"))
        desc_layout.addWidget(self.desc_contains)
        
        self.desc_case_sensitive = QCheckBox("Case sensitive")
        desc_layout.addWidget(self.desc_case_sensitive)
        
        layout.addWidget(desc_group)
        
        # Amount matching
        amount_group = QGroupBox("Amount Matching")
        amount_layout = QFormLayout(amount_group)
        
        self.amount_operator = QComboBox()
        self.amount_operator.addItems(["Any", "Equal to", "Greater than", "Less than", "Between"])
        amount_layout.addRow("Amount is:", self.amount_operator)
        
        self.amount_value = QLineEdit()
        self.amount_value.setPlaceholderText("0.00")
        amount_layout.addRow("Value:", self.amount_value)
        
        self.amount_value_2 = QLineEdit()
        self.amount_value_2.setPlaceholderText("0.00")
        self.amount_value_2.setVisible(False)
        amount_layout.addRow("To:", self.amount_value_2)
        
        self.amount_operator.currentTextChanged.connect(
            lambda text: self.amount_value_2.setVisible(text == "Between"))
        
        layout.addWidget(amount_group)
        
        # Account matching
        account_group = QGroupBox("Account Matching")
        account_layout = QVBoxLayout(account_group)
        
        self.account_contains = QLineEdit()
        account_layout.addWidget(QLabel("Account contains:"))
        account_layout.addWidget(self.account_contains)
        
        layout.addWidget(account_group)
        
        # Date matching
        date_group = QGroupBox("Date Matching")
        date_layout = QFormLayout(date_group)
        
        self.date_range = QComboBox()
        self.date_range.addItems(["Any", "Last 30 days", "Last 90 days", "This year", "Custom"])
        date_layout.addRow("Date range:", self.date_range)
        
        layout.addWidget(date_group)
        
        # Rule application
        apply_group = QGroupBox("Rule Application")
        apply_layout = QVBoxLayout(apply_group)
        
        self.apply_existing = QCheckBox("Apply to existing transactions")
        self.apply_future = QCheckBox("Apply to future transactions")
        self.apply_future.setChecked(True)
        
        apply_layout.addWidget(self.apply_existing)
        apply_layout.addWidget(self.apply_future)
        
        layout.addWidget(apply_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save Rule")
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
    
    def get_rule_data(self):
        """Get the rule configuration data"""
        amount_value = None
        amount_value_2 = None
        try:
            if self.amount_value.text():
                amount_value = Decimal(self.amount_value.text())
            if self.amount_value_2.isVisible() and self.amount_value_2.text():
                amount_value_2 = Decimal(self.amount_value_2.text())
        except ValueError:
            pass
        
        return {
            'category_id': self.category.id,
            'description': {
                'text': self.desc_contains.text(),
                'case_sensitive': self.desc_case_sensitive.isChecked()
            },
            'amount': {
                'operator': self.amount_operator.currentText(),
                'value': amount_value,
                'value2': amount_value_2
            },
            'account': {
                'text': self.account_contains.text()
            },
            'date_range': self.date_range.currentText(),
            'apply_to': {
                'existing': self.apply_existing.isChecked(),
                'future': self.apply_future.isChecked()
            }
        }