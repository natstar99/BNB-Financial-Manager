# File: views/transaction_view.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTableView, QDialog)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QTimer
from controllers.transaction_controller import TransactionController
from views.category_picker_dialog import CategoryPickerDialog
from views.auto_categorise_dialog import AutoCategoryRuleDialog
from views.auto_categorisation_rules_view import AutoCategorisationRulesView
from views.transaction_filter import FilterBar
from datetime import datetime
from models.bank_account_model import BankAccountModel
from typing import Dict, List
from decimal import Decimal
import decimal

class TransactionTableModel(QAbstractTableModel):
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
        self.current_filter = "all" 
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
            
            # Special handling for internal transfers and hidden transactions first
            if transaction.is_internal_transfer:
                if column == 5:  # Category column
                    return "Internal Transfer"
                elif column == 6:  # Tax Type column
                    return "N/A"
                elif column == 7:  # Tax Deductible column
                    return "N/A"
            elif transaction.is_hidden:
                if column == 5:  # Category column
                    return "Hidden"
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

    def refresh_data(self, filter_type=None):
        """
        Refresh the model's data while maintaining filter state
        
        Args:
            filter_type: Optional filter type to apply. If None, uses current filter
        """
        self.beginResetModel()
        # Use provided filter_type or maintain current filter
        if filter_type is not None:
            self.current_filter = filter_type
        self.transactions = self.controller.get_transactions(self.current_filter)
        self.endResetModel()

    def flags(self, index):
        """Return item flags for the given index"""
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() == 5:  # Category column
            flags |= Qt.ItemIsEditable
        return flags
    
    def setData(self, index, value, role=Qt.EditRole):
        """
        Handle data changes in the model
        
        Args:
            index: The QModelIndex of the cell being changed
            value: The new value (in this case, the selected category or internal transfer status)
            role: The role being used for the change
            
        Returns:
            bool: True if the change was successful, False otherwise
        """
        if role == Qt.EditRole and index.column() == 5:  # Category column
            transaction = self.transactions[index.row()]
            
            # Check if this is a CategoryPickerDialog result with internal transfer info
            if isinstance(value, tuple) and len(value) == 2:
                category, is_internal = value
                success = self.controller.categorise_transaction(
                    transaction.id, 
                    category.id if category else None,
                    is_internal
                )
            else:
                # Handle regular category selection
                success = self.controller.categorise_transaction(
                    transaction.id,
                    value.id if value else None,
                    False
                )
                
            if success:
                self.refresh_data()
                return True
                
        return False
    
    def refresh_data(self, filter_type=None):
        """
        Refresh the model's data while maintaining filter state
        
        Args:
            filter_type: Optional filter type to apply. If None, uses current filter
        """
        self.beginResetModel()
        # Use provided filter_type or maintain current filter
        if filter_type is not None:
            self.current_filter = filter_type
        self.transactions = self.controller.get_transactions(self.current_filter)
        self.endResetModel()

    def apply_filters(self, filters: Dict) -> List:
        """
        Apply filters to transactions
        
        Args:
            filters: Dictionary containing filter logic and conditions
            
        Returns:
            List of transactions that match the filters
        """
        # If no filters or conditions, use the base transaction list
        if not filters or not filters['conditions']:
            return self.controller.get_transactions(self.current_filter)
        
        # Start with the current filter's transactions
        base_transactions = self.controller.get_transactions(self.current_filter)
        filtered = []
        
        for transaction in base_transactions:
            matches = []
            
            for condition in filters['conditions']:
                field = condition['field']
                operator = condition['operator']
                value = condition['value']
                match = False
                
                if field == "Description":
                    text = transaction.description.lower()
                    filter_text = str(value).lower()
                    
                    if operator == "Contains":
                        match = filter_text in text
                    elif operator == "Does not contain":
                        match = filter_text not in text
                    elif operator == "Equals":
                        match = text == filter_text
                    elif operator == "Does not equal":
                        match = text != filter_text
                        
                elif field == "Amount":
                    # Get the absolute value for comparison
                    amount = abs(transaction.withdrawal or transaction.deposit)
                    try:
                        filter_value = abs(Decimal(str(value)))
                        if operator == "Greater than":
                            match = amount > filter_value
                        elif operator == "Less than":
                            match = amount < filter_value
                        elif operator == "Equal to":
                            match = abs(amount - filter_value) < Decimal('0.01')
                        elif operator == "Between":
                            # Handle between range if second value exists
                            value2 = condition.get('value2')
                            if value2:
                                filter_value2 = abs(Decimal(str(value2)))
                                match = filter_value <= amount <= filter_value2
                    except (TypeError, ValueError, decimal.InvalidOperation):
                        match = False
                        
                elif field == "Date":
                    trans_date = transaction.date.date()
                    try:
                        filter_date = value.date() if isinstance(value, datetime) else value
                        if operator == "After":
                            match = trans_date > filter_date
                        elif operator == "Before":
                            match = trans_date < filter_date
                        elif operator == "On":
                            match = trans_date == filter_date
                        elif operator == "Between":
                            # Handle between range if second value exists
                            value2 = condition.get('value2')
                            if value2:
                                filter_date2 = value2.date() if isinstance(value2, datetime) else value2
                                match = filter_date <= trans_date <= filter_date2
                    except (AttributeError, TypeError):
                        match = False
                        
                elif field == "Account":
                    if operator == "Is":
                        match = transaction.account == value
                    elif operator == "Is not":
                        match = transaction.account != value
                
                matches.append(match)
            
            # Apply logical operator
            if filters['logic'] == 'AND':
                if all(matches):
                    filtered.append(transaction)
            else:  # OR
                if any(matches):
                    filtered.append(transaction)
        
        return filtered

    def apply_filter_and_refresh(self, filters: Dict):
        """
        Apply filters and refresh the model, ensuring proper view updates
        
        Args:
            filters: Dictionary containing:
                - logic: str, 'AND' or 'OR' for combining conditions
                - conditions: List of filter conditions, each containing:
                    - field: str, the field to filter on (Description, Amount, Date, Account)
                    - operator: str, the comparison operator
                    - value: The filter value
                    - value2: Optional second value for 'Between' operators
        """
        # Begin model reset - tells views to prepare for data change
        self.beginResetModel()
        
        try:
            # Store current scroll position if needed
            current_scroll = self.parent().table_view.verticalScrollBar().value() if self.parent() else 0
            
            # Apply the filters to get updated transaction list
            self.transactions = self.apply_filters(filters)
            
            # Emit layout changed signal to ensure views update properly
            # This is crucial for complex models where data structure might change
            self.layoutChanged.emit()
            
            # Update any summary or status information
            if self.parent():
                status_text = f"Showing {len(self.transactions)} transactions"
                self.parent().parent().statusBar().showMessage(status_text, 3000)  # Show for 3 seconds
                
        except Exception as e:
            # Log any errors during filter application
            print(f"Error applying filters: {e}")
            # Revert to unfiltered state
            self.transactions = self.controller.get_transactions(self.current_filter)
            
        finally:
            # Always ensure model reset is completed
            self.endResetModel()
            
            # Restore scroll position if possible
            if self.parent():
                self.parent().table_view.verticalScrollBar().setValue(current_scroll)
    
class TransactionView(QWidget):
    def __init__(self, controller: TransactionController, category_controller, bank_account_model: BankAccountModel):
        super().__init__()
        self.controller = controller
        self.category_controller = category_controller
        self.bank_account_model = bank_account_model
        self.pending_filters = None # Add instance variable for storing pending filters
        self._setup_ui()
    
    def _setup_ui(self):
        """Initialise the user interface"""
        layout = QVBoxLayout(self)

        # Add FilterBar near the top
        self.filter_bar = FilterBar(
            accounts=self.bank_account_model.get_accounts()
        )
        # Update signal connection to store_pending_filters
        self.filter_bar.filters_changed.connect(self._store_pending_filters)
        layout.addWidget(self.filter_bar)
        
        # Create filter action buttons layout
        filter_action_layout = QHBoxLayout()
        
        # Add refresh button
        self.refresh_button = QPushButton("Apply Filters")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.refresh_button.clicked.connect(self._apply_pending_filters)
        filter_action_layout.addWidget(self.refresh_button)
        
        # Add clear filters button
        self.clear_filters_button = QPushButton("Clear Filters")
        self.clear_filters_button.clicked.connect(self._clear_filters)
        filter_action_layout.addWidget(self.clear_filters_button)
        
        # Add stretch to push buttons to the right
        filter_action_layout.addStretch()
        
        layout.addLayout(filter_action_layout)
        
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
        
        # Add Categorise Selected button
        self.categorise_selected_button = QPushButton("Categorise Selected")
        self.categorise_selected_button.clicked.connect(self._categorise_selected)
        self.categorise_selected_button.setEnabled(False)  # Initially disabled
        cat_button_layout.addWidget(self.categorise_selected_button)
        
        auto_cat_button = QPushButton("Create Auto-Categorisation Rule")
        auto_cat_button.clicked.connect(self._create_auto_rule)
        cat_button_layout.addWidget(auto_cat_button)
        
        view_rules_button = QPushButton("View Auto-Categorisation Rules")
        view_rules_button.clicked.connect(self._view_auto_rules)
        cat_button_layout.addWidget(view_rules_button)
        
        run_all_rules_button = QPushButton("Run All Auto-Categorisation Rules")
        run_all_rules_button.clicked.connect(self._run_all_rules)
        cat_button_layout.addWidget(run_all_rules_button)

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
        
        # Enable multi-selection
        self.table_view.setSelectionMode(QTableView.ExtendedSelection)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        
        # Connect selection changed signal
        self.table_view.selectionModel().selectionChanged.connect(self._handle_selection_changed)
        
        # Connect double-click handler for category selection
        self.table_view.doubleClicked.connect(self._handle_cell_double_click)
        
        layout.addWidget(self.table_view)

    def _store_pending_filters(self, filters: Dict):
        """
        Store filters when they change but don't apply them yet
        
        Args:
            filters: Dictionary containing filter logic and conditions
        """
        print("Storing pending filters:", filters)  # Debug print
        self.pending_filters = filters
        # Enable/disable refresh button based on whether there are filters with actual conditions
        has_filters = bool(filters and filters.get('conditions') and any(
            condition.get('value') for condition in filters['conditions']
        ))
        self.refresh_button.setEnabled(has_filters)
        self.clear_filters_button.setEnabled(has_filters)

    def _apply_pending_filters(self):
        """Apply the stored pending filters to the transaction view"""
        print("Applying pending filters:", self.pending_filters)  # Debug print
        if self.pending_filters is not None:
            try:
                # Store current scroll position
                scroll_pos = self._store_scroll_position()
                
                # Apply the filters
                self.table_model.apply_filter_and_refresh(self.pending_filters)
                
                # Update status bar with count of filtered transactions
                filtered_count = len(self.table_model.transactions)
                self.window().statusBar().showMessage(
                    f"Showing {filtered_count} filtered transactions", 3000)
                
            except Exception as e:
                print(f"Error applying filters: {e}")  # Debug print
                self.window().statusBar().showMessage(
                    f"Error applying filters: {str(e)}", 5000)
            
            # Restore scroll position after brief delay
            QTimer.singleShot(50, lambda: self._restore_scroll_position(scroll_pos))

    def _clear_filters(self):
        """Clear all active filters and reset the view"""
        # Clear the filter bar
        self.filter_bar.clear_all()
        
        # Clear pending filters
        self.pending_filters = None
        
        # Reset the model to show all transactions
        self.table_model.refresh_data(self.table_model.current_filter)
        
        # Update status bar
        self.window().statusBar().showMessage("Filters cleared", 3000)
        
        # Disable the filter action buttons
        self.refresh_button.setEnabled(False)
        self.clear_filters_button.setEnabled(False)

    def _handle_filters_changed(self, filters: Dict):
        """
        Handle changes in filter conditions
        
        Args:
            filters: Dictionary containing filter logic and conditions
        """
        # Store current scroll position
        scroll_pos = self._store_scroll_position()
        
        # Apply filters
        self.table_model.apply_filter_and_refresh(filters)
        
        # Restore scroll position after brief delay
        QTimer.singleShot(50, lambda: self._restore_scroll_position(scroll_pos))
    
    def _handle_cell_double_click(self, index):
        """
        Handle double-click on table cells for category selection and internal transfer marking
        Maintains current filter and scroll position
        """
        if index.column() == 5:  # Category column
            # Store current scroll position
            scroll_pos = self._store_scroll_position()
            
            dialog = CategoryPickerDialog(self.category_controller, self)
            if dialog.exec_() == QDialog.Accepted:
                transaction = self.table_model.transactions[index.row()]
                success = self.controller.categorise_transaction(
                    transaction_id=transaction.id,
                    category_id=dialog.selected_category.id if dialog.selected_category else None,
                    is_internal_transfer=dialog.is_internal_transfer,
                    is_hidden=dialog.is_hidden
                )
                if success:
                    # Refresh using current filter
                    self.table_model.refresh_data()
                    # Restore scroll position after brief delay to ensure view is updated
                    QTimer.singleShot(50, lambda: self._restore_scroll_position(scroll_pos))
    
    def _create_auto_rule(self):
        """Handle creating an auto-categorisation rule"""
        # First, select a category to create rules for
        dialog = CategoryPickerDialog(self.category_controller, self)
        if dialog.exec_() == QDialog.Accepted:
            # Check if user selected internal transfer or category
            if dialog.is_internal_transfer:
                # Show rule dialog for internal transfer
                rule_dialog = AutoCategoryRuleDialog(
                    None,  # No category for internal transfers
                    self.bank_account_model,
                    True,  # is_internal_transfer flag
                    self
                )
            elif dialog.selected_category:
                # Show rule dialog for regular category
                rule_dialog = AutoCategoryRuleDialog(
                    dialog.selected_category,
                    self.bank_account_model,
                    False,  # is_internal_transfer flag
                    self
                )
            else:
                return  # No selection made
                
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

    def _handle_selection_changed(self):
        """
        Handle changes in row selection.
        Enables/disables the Categorise Selected button based on selection state.
        """
        selected_rows = self.table_view.selectionModel().selectedRows()
        self.categorise_selected_button.setEnabled(len(selected_rows) > 0)
    
    def _store_scroll_position(self):
        """Store the current vertical scroll position"""
        return self.table_view.verticalScrollBar().value()
    
    def _restore_scroll_position(self, position):
        """Restore the vertical scroll position"""
        self.table_view.verticalScrollBar().setValue(position)
    
    def _categorise_selected(self):
        """
        Handle categorisation of multiple selected transactions
        Maintains current filter and scroll position
        """
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            return
        
        # Store current scroll position
        scroll_pos = self._store_scroll_position()
        
        # Get the selected transactions
        selected_transactions = [
            self.table_model.transactions[index.row()]
            for index in selected_indexes
        ]
        
        # Show category picker dialog
        dialog = CategoryPickerDialog(self.category_controller, self)
        if dialog.exec_() == QDialog.Accepted:
            # Apply the category to all selected transactions
            for transaction in selected_transactions:
                self.controller.categorise_transaction(
                    transaction_id=transaction.id,
                    category_id=dialog.selected_category.id if dialog.selected_category else None,
                    is_internal_transfer=dialog.is_internal_transfer,
                    is_hidden=dialog.is_hidden
                )
            
            # Refresh using current filter
            self.table_model.refresh_data()
            # Restore scroll position after brief delay
            QTimer.singleShot(50, lambda: self._restore_scroll_position(scroll_pos))

    def _run_all_rules(self):
        """
        Apply all auto-categorisation rules to transactions
        and refresh the view to show the changes
        """
        # Store current scroll position
        scroll_pos = self._store_scroll_position()
        
        # Apply all auto-categorisation rules
        self.controller.apply_auto_categorisation_rules()
        
        # Refresh the transaction view
        self.table_model.refresh_data()
        
        # Show status message
        self.window().statusBar().showMessage("Applied all auto-categorisation rules", 3000)
        
        # Restore scroll position after brief delay
        QTimer.singleShot(50, lambda: self._restore_scroll_position(scroll_pos))