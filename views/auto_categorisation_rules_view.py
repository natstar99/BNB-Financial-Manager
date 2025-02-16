# File: views/auto_categorisation_rules_view.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QMessageBox, QWidget
)
from views.auto_categorise_dialog import AutoCategoryRuleDialog

class AutoCategorisationRulesView(QDialog):
    """Dialog for viewing and managing auto-categorisation rules"""
    
    def __init__(self, transaction_controller, parent=None):
        super().__init__(parent)
        self.controller = transaction_controller
        self.category_controller = transaction_controller.category_controller
        self.bank_account_model = transaction_controller.bank_account_model
        self.setup_ui()
        self.load_rules()
    
    def setup_ui(self):
        """Set up the user interface"""
        self.setWindowTitle("Auto-Categorisation Rules")
        self.resize(800, 400)
        
        layout = QVBoxLayout(self)
        
        # Create rules table
        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(7)
        self.rules_table.setHorizontalHeaderLabels([
            "Category",
            "Description Conditions",
            "Amount Rule",
            "Account",
            "Date Range",
            "Apply to Future",
            "Actions"
        ])
        
        # Configure table
        header = self.rules_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.rules_table)
        
        # Button bar
        button_layout = QHBoxLayout()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
    
    def load_rules(self):
        """Load and display all auto-categorisation rules"""
        rules = self.controller.get_auto_categorisation_rules()
        self.rules_table.setRowCount(len(rules))
        
        for row, rule in enumerate(rules):
            # Category
            self.rules_table.setItem(row, 0, QTableWidgetItem(rule['category_name']))
            
            # Description Conditions
            desc_conditions = self._format_description_conditions(rule['description_conditions'])
            self.rules_table.setItem(row, 1, QTableWidgetItem(desc_conditions))
            
            # Amount Rule
            amount_text = self._format_amount_rule(
                rule['amount_operator'],
                rule['amount_value'],
                rule['amount_value2']
            )
            self.rules_table.setItem(row, 2, QTableWidgetItem(amount_text))
            
            # Account
            self.rules_table.setItem(row, 3, QTableWidgetItem(rule['account_name']))
            
            # Date Range
            self.rules_table.setItem(row, 4, QTableWidgetItem(rule['date_range'] or "Any"))
            
            # Apply to Future
            self.rules_table.setItem(row, 5, QTableWidgetItem(
                "Yes" if rule['apply_future'] else "No"))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 0, 4, 0)
            
            edit_button = QPushButton("Edit")
            edit_button.clicked.connect(lambda checked, r=rule: self._edit_rule(r))
            delete_button = QPushButton("Delete")
            delete_button.clicked.connect(lambda checked, r=rule: self._delete_rule(r))
            
            actions_layout.addWidget(edit_button)
            actions_layout.addWidget(delete_button)
            self.rules_table.setCellWidget(row, 6, actions_widget)
    
    def _format_description_conditions(self, conditions):
        """Format description conditions for display"""
        if not conditions:
            return "Any"
            
        parts = []
        for condition in conditions:
            text = f'"{condition["text"]}"'
            if condition['case_sensitive']:
                text += " (Case Sensitive)"
            if condition['operator']:
                parts.append(f"{condition['operator']} {text}")
            else:
                parts.append(text)
        return " ".join(parts)
    
    def _format_amount_rule(self, operator, value1, value2):
        """Format amount rule for display"""
        if operator == "Any" or not value1:
            return "Any"
            
        amount_text = f"{operator}"
        if value1 is not None:
            amount_text += f" ${value1:.2f}"
            if operator == "Between" and value2 is not None:
                amount_text += f" to ${value2:.2f}"
        
        return amount_text
    
    def _edit_rule(self, rule):
        """Handle editing a rule"""
        try:
            # Get the category object first
            category = self.controller.category_controller.model.get_categories()
            category_obj = next((c for c in category if c.id == rule['category_id']), None)
            
            if not category_obj:
                QMessageBox.warning(self, "Error", "Could not find associated category")
                return

            # Create dialog with actual category object
            dialog = AutoCategoryRuleDialog(
                category=category_obj,
                bank_account_model=self.controller.bank_account_model,
                parent=self
            )
            
            # Pre-fill existing rule data
            dialog.set_rule_data(rule)
            
            if dialog.exec_():
                if self.controller.update_auto_categorisation_rule(
                    rule['id'], dialog.get_rule_data()):
                    self.load_rules()  # Refresh the table
                else:
                    QMessageBox.warning(self, "Error", "Failed to update rule")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error editing rule: {str(e)}")
    
    def _delete_rule(self, rule):
        """Handle deleting a rule"""
        if QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this rule?",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            if self.controller.delete_auto_categorisation_rule(rule['id']):
                self.load_rules()  # Refresh the table
            else:
                QMessageBox.warning(self, "Error", "Failed to delete rule")