# File: views/auto_categorisation_rules_view.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QMessageBox, QWidget
)
from PySide6.QtCore import Qt

class AutoCategorisationRulesView(QDialog):
    """Dialog for viewing and managing auto-categorisation rules"""
    
    def __init__(self, transaction_controller, parent=None):
        super().__init__(parent)
        self.controller = transaction_controller
        self.setup_ui()
        self.load_rules()
    
    def setup_ui(self):
        """Set up the user interface"""
        self.setWindowTitle("Auto-Categorisation Rules")
        self.resize(800, 400)
        
        layout = QVBoxLayout(self)
        
        # Create rules table
        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(8)
        self.rules_table.setHorizontalHeaderLabels([
            "Category", "Description", "Amount Rule", "Account",
            "Date Range", "Apply to Future", "Actions", "ID"
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
        header.setSectionResizeMode(7, QHeaderView.Fixed)  # Hide ID column
        self.rules_table.hideColumn(7)  # Hide the ID column
        
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
            
            # Description
            desc_text = rule['description_text']
            if rule['description_case_sensitive']:
                desc_text += " (Case Sensitive)"
            self.rules_table.setItem(row, 1, QTableWidgetItem(desc_text))
            
            # Amount Rule
            amount_text = rule['amount_operator']
            if rule['amount_value'] is not None:
                amount_text += f" ${rule['amount_value']:.2f}"
                if rule['amount_value2'] is not None:
                    amount_text += f" to ${rule['amount_value2']:.2f}"
            self.rules_table.setItem(row, 2, QTableWidgetItem(amount_text))
            
            # Account
            self.rules_table.setItem(row, 3, QTableWidgetItem(rule['account_text'] or "Any"))
            
            # Date Range
            self.rules_table.setItem(row, 4, QTableWidgetItem(rule['date_range']))
            
            # Apply to Future
            self.rules_table.setItem(row, 5, QTableWidgetItem(
                "Yes" if rule['apply_future'] else "No"))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            edit_button = QPushButton("Edit")
            edit_button.clicked.connect(lambda checked, r=rule: self._edit_rule(r))
            delete_button = QPushButton("Delete")
            delete_button.clicked.connect(lambda checked, r=rule: self._delete_rule(r))
            
            actions_layout.addWidget(edit_button)
            actions_layout.addWidget(delete_button)
            self.rules_table.setCellWidget(row, 6, actions_widget)
            
            # Hidden ID column
            self.rules_table.setItem(row, 7, QTableWidgetItem(str(rule['id'])))
    
    def _edit_rule(self, rule):
        """Handle editing a rule"""
        # Show the auto categorisation dialog with pre-filled data
        from views.auto_categorise_dialog import AutoCategoryRuleDialog
        dialog = AutoCategoryRuleDialog(rule['category_id'], self)
        dialog.set_rule_data(rule)
        if dialog.exec_():
            # Update the rule
            if self.controller.update_auto_categorisation_rule(
                rule['id'], dialog.get_rule_data()):
                self.load_rules()  # Refresh the table
            else:
                QMessageBox.warning(self, "Error", "Failed to update rule")
    
    def _delete_rule(self, rule):
        """Handle deleting a rule"""
        if QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this rule?"
        ) == QMessageBox.Yes:
            if self.controller.delete_auto_categorisation_rule(rule['id']):
                self.load_rules()  # Refresh the table
            else:
                QMessageBox.warning(self, "Error", "Failed to delete rule")