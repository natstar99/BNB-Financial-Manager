# File: views/auto_categorise_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QCheckBox,
    QFormLayout, QGroupBox, QSpinBox
)
from decimal import Decimal
from models.bank_account_model import BankAccountModel

class AutoCategoryRuleDialog(QDialog):
    """Dialog for creating automatic categorisation rules"""
    def __init__(self, category, bank_account_model: BankAccountModel, parent=None):
        super().__init__(parent)
        self.category = category
        self.bank_account_model = bank_account_model
        self.description_conditions = []  # List to store multiple description conditions
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle(f"Auto-Categorisation Rules - {self.category.name}")
        layout = QVBoxLayout(self)
        
        # Description matching
        desc_group = QGroupBox("Description Matching")
        desc_layout = QVBoxLayout(desc_group)
        
        # Container for description conditions
        self.desc_container = QVBoxLayout()
        
        # Add initial description condition
        self._add_description_condition()
        
        # Add button for new condition
        add_condition_button = QPushButton("Add Another Description Condition")
        add_condition_button.clicked.connect(self._add_description_condition)
        
        desc_layout.addLayout(self.desc_container)
        desc_layout.addWidget(add_condition_button)
        
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
        
        # Account matching with dropdown
        account_group = QGroupBox("Account Matching")
        account_layout = QVBoxLayout(account_group)

        self.account_combo = QComboBox()
        self.account_combo.addItem("Any Account", None)  # Default option

        # Get accounts from bank_account_model (using the one passed to the dialog)
        accounts = self.bank_account_model.get_accounts()
        for account in accounts:
            display_text = f"{account.name} ({account.bank_name})"
            self.account_combo.addItem(display_text, account.id)

        account_layout.addWidget(QLabel("Select Account:"))
        account_layout.addWidget(self.account_combo)

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
    
    def _add_description_condition(self):
        """Add a new description condition row"""
        condition_layout = QHBoxLayout()
        
        # If not the first condition, add AND/OR operator
        if self.description_conditions:
            operator = QComboBox()
            operator.addItems(["AND", "OR"])
            condition_layout.addWidget(operator)
        
        desc_contains = QLineEdit()
        desc_contains.setPlaceholderText("Contains text...")
        condition_layout.addWidget(desc_contains)
        
        case_sensitive = QCheckBox("Case sensitive")
        condition_layout.addWidget(case_sensitive)
        
        # Add remove button (except for first condition)
        if self.description_conditions:
            remove_button = QPushButton("Remove")
            remove_button.clicked.connect(lambda: self._remove_description_condition(condition_layout))
            condition_layout.addWidget(remove_button)
        
        self.desc_container.addLayout(condition_layout)
        self.description_conditions.append({
            'layout': condition_layout,
            'operator': operator if self.description_conditions else None,
            'text': desc_contains,
            'case_sensitive': case_sensitive
        })
    
    def _remove_description_condition(self, layout):
        """Remove a description condition"""
        # Remove all widgets from the layout
        while layout.count():
            widget = layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        
        # Remove from our list of conditions
        self.description_conditions = [c for c in self.description_conditions if c['layout'] != layout]
    
    def get_rule_data(self):
        """Get the rule configuration data"""
        # Process description conditions
        description_conditions = []
        for condition in self.description_conditions:
            if condition['operator']:
                operator = condition['operator'].currentText()
            else:
                operator = None  # First condition doesn't have an operator
            
            description_conditions.append({
                'operator': operator,
                'text': condition['text'].text(),
                'case_sensitive': condition['case_sensitive'].isChecked()
            })
        
        # Process amount values
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
                'conditions': description_conditions
            },
            'amount': {
                'operator': self.amount_operator.currentText(),
                'value': amount_value,
                'value2': amount_value_2
            },
            'account': {
                'id': self.account_combo.currentData()
            },
            'date_range': self.date_range.currentText(),
            'apply_to': {
                'existing': self.apply_existing.isChecked(),
                'future': self.apply_future.isChecked()
            }
        }

    def set_rule_data(self, rule: dict):
        """
        Pre-fill the dialog with existing rule data
        
        Args:
            rule: Dictionary containing the rule data:
            {
                'description_conditions': List of conditions with operator, text, and case_sensitive
                'amount_operator': str,
                'amount_value': float,
                'amount_value2': float,
                'account_id': str,
                'date_range': str,
                'apply_future': bool
            }
        """
        try:
            # Clear existing description conditions
            while self.desc_container.count():
                layout_item = self.desc_container.takeAt(0)
                if layout_item.layout():
                    while layout_item.layout().count():
                        widget = layout_item.layout().takeAt(0).widget()
                        if widget:
                            widget.deleteLater()
                layout_item.layout().deleteLater()
            self.description_conditions.clear()

            # Add description conditions
            for condition in rule['description_conditions']:
                self._add_description_condition()
                current_condition = self.description_conditions[-1]
                
                # Set the operator if it exists (not for first condition)
                if condition['operator'] and current_condition.get('operator'):
                    current_condition['operator'].setCurrentText(condition['operator'])
                
                # Set the text and case sensitivity
                current_condition['text'].setText(condition['text'])
                current_condition['case_sensitive'].setChecked(condition['case_sensitive'])

            # Set amount conditions
            if rule['amount_operator']:
                self.amount_operator.setCurrentText(rule['amount_operator'])
            if rule['amount_value'] is not None:
                self.amount_value.setText(str(rule['amount_value']))
            if rule['amount_value2'] is not None:
                self.amount_value_2.setText(str(rule['amount_value2']))
                self.amount_value_2.setVisible(rule['amount_operator'] == "Between")

            # Set account
            if rule['account_id']:
                index = self.account_combo.findData(rule['account_id'])
                if index >= 0:
                    self.account_combo.setCurrentIndex(index)

            # Set date range
            if rule['date_range']:
                index = self.date_range.findText(rule['date_range'])
                if index >= 0:
                    self.date_range.setCurrentIndex(index)

            # Set apply flags
            self.apply_future.setChecked(rule['apply_future'])

        except Exception as e:
            print(f"Error setting rule data: {e}")