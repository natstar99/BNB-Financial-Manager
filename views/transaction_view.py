# File: views/transaction_view.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTableView, QDialog)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from controllers.transaction_controller import TransactionController
from views.category_picker_dialog import CategoryPickerDialog
from views.auto_categorise_dialog import AutoCategoryRuleDialog
from views.auto_categorisation_rules_view import AutoCategorisationRulesView
from datetime import datetime
from models.bank_account_model import BankAccountModel

class TransactionTableModel(QAbstractTableModel):  # Changed to QAbstractTableModel
    """Model for displaying transactions in a table view"""
    
    # Define column indices for easier reference
    COLUMNS = [
        'Date',
        'Account',
        'Description',
        'Withdrawal',
        'Deposit',
        'Category',
        'Tax Type',
        'Tax Deductible'
    ]
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.transactions = self.controller.get_transactions()

    def rowCount(self, parent=QModelIndex()):
        """Return the number of rows in the model"""
        if parent.isValid():
            return 0
        return len(self.transactions)

    def columnCount(self, parent=QModelIndex()):
        """Return the number of columns in the model"""
        if parent.isValid():
            return 0
        return len(self.COLUMNS)

    def data(self, index, role=Qt.DisplayRole):
        """Return the data for a given index and role"""
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            transaction = self.transactions[index.row()]
            column = index.column()
            
            # Special handling for internal transfers first
            if transaction.is_internal_transfer:
                if column == 5:  # Category column
                    return "Internal Transfer"
                elif column == 6:  # Tax Type column
                    return "N/A"
                elif column == 7:  # Tax Deductible column
                    return "N/A"
            
            # Then handle regular transaction data
            if column == 0:  # Date
                return transaction.date.strftime("%Y-%m-%d")
            elif column == 1:  # Account
                return transaction.account
            elif column == 2:  # Description
                return transaction.description
            elif column == 3:  # Withdrawal
                return f"${transaction.withdrawal:.2f}" if transaction.withdrawal else ""
            elif column == 4:  # Deposit
                return f"${transaction.deposit:.2f}" if transaction.deposit else ""
            elif column == 5:  # Category
                return transaction.category_id or "Uncategorised"
            elif column == 6:  # Tax Type
                return transaction.tax_type.value
            elif column == 7:  # Tax Deductible
                return "Yes" if transaction.is_tax_deductible else "No"

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Return the header data for the view"""
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.COLUMNS[section]
        return None

    def flags(self, index):
        """Return item flags for the given index"""
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def refresh_data(self, filter_type="all"):
        """Refresh the model's data"""
        # Begin model reset to notify views
        self.beginResetModel()
        self.transactions = self.controller.get_transactions(filter_type)
        self.endResetModel()

    def flags(self, index):
        """Return item flags for the given index"""
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() == 5:  # Category column
            flags |= Qt.ItemIsEditable
        return flags
    
    def setData(self, index, value, role=Qt.EditRole):
        """Handle data changes"""
        if role == Qt.EditRole and index.column() == 5:  # Category column
            transaction = self.transactions[index.row()]
            success = self.controller.categorise_transaction(
                transaction.id, value.id if value else None)
            if success:
                self.refresh_data()
                return True
        return False
    
class TransactionView(QWidget):
    def __init__(self, controller: TransactionController, category_controller, bank_account_model: BankAccountModel):
        super().__init__()
        self.controller = controller
        self.category_controller = category_controller
        self.bank_account_model = bank_account_model
        self._setup_ui()
    
    def _setup_ui(self):
        """Initialise the user interface"""
        layout = QVBoxLayout(self)
        
        # Create button container for all buttons
        all_buttons_layout = QVBoxLayout()
        
        # Create filter buttons
        filter_button_layout = QHBoxLayout()
        filter_buttons = {
            "All": "all",
            "Uncategorised": "uncategorised",
            "Categorised": "categorised",
            "Internal Transfers": "internal_transfers",
            "Hidden": "hidden"
        }
        
        for button_text, filter_type in filter_buttons.items():
            button = QPushButton(button_text)
            button.clicked.connect(
                lambda checked, ft=filter_type: self._filter_transactions(ft))
            filter_button_layout.addWidget(button)
        
        all_buttons_layout.addLayout(filter_button_layout)
        
        # Create categorisation buttons
        cat_button_layout = QHBoxLayout()
        
        # Add stretch to push buttons to the left
        cat_button_layout.addStretch()
        
        auto_cat_button = QPushButton("Create Auto-Categorisation Rule")
        auto_cat_button.clicked.connect(self._create_auto_rule)
        cat_button_layout.addWidget(auto_cat_button)
        
        view_rules_button = QPushButton("View Auto-Categorisation Rules")
        view_rules_button.clicked.connect(self._view_auto_rules)
        cat_button_layout.addWidget(view_rules_button)
        
        # Add stretch to keep buttons centered
        cat_button_layout.addStretch()
        
        all_buttons_layout.addLayout(cat_button_layout)
        
        # Add all buttons to main layout
        layout.addLayout(all_buttons_layout)
        
        # Create table view
        self.table_view = QTableView()
        self.table_model = TransactionTableModel(self.controller)
        self.table_view.setModel(self.table_model)
        
        # Configure table view
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSortingEnabled(True)
        
        # Connect double-click handler for category selection
        self.table_view.doubleClicked.connect(self._handle_cell_double_click)
        
        layout.addWidget(self.table_view)
    
    def _handle_cell_double_click(self, index):
        """Handle double-click on table cells"""
        if index.column() == 5:  # Category column
            dialog = CategoryPickerDialog(self.category_controller, self)
            if dialog.exec_() == QDialog.Accepted and dialog.selected_category:
                self.table_model.setData(index, dialog.selected_category, Qt.EditRole)
    
    def _create_auto_rule(self):
        """Handle creating an auto-categorisation rule"""
        # First, select a category to create rules for
        dialog = CategoryPickerDialog(self.category_controller, self)
        if dialog.exec_() == QDialog.Accepted and dialog.selected_category:
            # Then show the rule creation dialog
            rule_dialog = AutoCategoryRuleDialog(
                dialog.selected_category,
                self.bank_account_model,
                self
            )
            if rule_dialog.exec_() == QDialog.Accepted:
                rule_data = rule_dialog.get_rule_data()
                success = self.controller.create_auto_categorisation_rule(rule_data)
                if success and rule_data['apply_to']['existing']:
                    # Apply rules to existing transactions
                    self.controller.apply_auto_categorisation_rules()
                    self.table_model.refresh_data()
    
    def _filter_transactions(self, filter_type: str):
        """Handle transaction filtering including internal transfers"""
        self.table_model.refresh_data(filter_type)

    def _view_auto_rules(self):
        """Show the auto-categorisation rules management dialog"""
        dialog = AutoCategorisationRulesView(self.controller, self)
        dialog.exec_()