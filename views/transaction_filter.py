# File: views/transaction_filter.py

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QComboBox, 
    QLineEdit, QPushButton, QLabel, QDateEdit
)
from PySide6.QtCore import Qt, Signal, QDate
from decimal import Decimal
from typing import List, Dict
from datetime import datetime
import decimal

class FilterCondition(QWidget):
    """
    A widget representing a single filter condition with operator and value.
    Supports different types of filters (text, amount, date, account)
    """
    # Signal emitted when the condition changes
    changed = Signal()
    # Signal emitted when remove is requested
    remove_requested = Signal(object)  # Passes self reference
    
    def __init__(self, accounts=None, parent=None):
        """
        Initialise the filter condition widget
        
        Args:
            accounts: Optional list of account objects for account filtering
            parent: Parent widget
        """
        super().__init__(parent)
        self.accounts = accounts or []
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the filter condition user interface"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Field selection
        self.field_combo = QComboBox()
        self.field_combo.addItems([
            "Description",
            "Amount",
            "Date",
            "Account"
        ])
        self.field_combo.currentTextChanged.connect(self._update_operator_options)
        layout.addWidget(self.field_combo)
        
        # Operator selection
        self.operator_combo = QComboBox()
        layout.addWidget(self.operator_combo)
        
        # Value input (will be switched based on field type)
        self.value_stack = QWidget()
        self.value_layout = QHBoxLayout(self.value_stack)
        self.value_layout.setContentsMargins(0, 0, 0, 0)
        
        # Text input for description
        self.text_input = QLineEdit()
        self.text_input.textChanged.connect(self.changed)
        
        # Amount input
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("0.00")
        self.amount_input.textChanged.connect(self.changed)
        
        # Date input
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.dateChanged.connect(self.changed)
        
        # Account selection
        self.account_combo = QComboBox()
        self.account_combo.addItem("Any")
        for account in self.accounts:
            self.account_combo.addItem(account.name, account.id)
        self.account_combo.currentIndexChanged.connect(self.changed)
        
        layout.addWidget(self.value_stack)
        
        # Remove button
        remove_btn = QPushButton("×")
        remove_btn.setFixedWidth(30)
        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))
        layout.addWidget(remove_btn)
        
        # Initial setup
        self._update_operator_options()
    
    def _setup_between_inputs(self):
        """Setup inputs for 'Between' operator"""
        # Create second value input based on field type
        field = self.field_combo.currentText()
        
        if field == "Amount":
            self.value2_input = QLineEdit()
            self.value2_input.setPlaceholderText("0.00")
            self.value2_input.textChanged.connect(self.changed)
        elif field == "Date":
            self.value2_input = QDateEdit()
            self.value2_input.setCalendarPopup(True)
            self.value2_input.setDate(QDate.currentDate())
            self.value2_input.dateChanged.connect(self.changed)
        
        # Add 'to' label and second input
        self.value_layout.addWidget(QLabel("to"))
        self.value_layout.addWidget(self.value2_input)

    def _update_operator_options(self):
        """Update operator options based on selected field"""
        self.operator_combo.clear()
        field = self.field_combo.currentText()
        
        # Remove current value widget and clean up
        for i in reversed(range(self.value_layout.count())): 
            widget = self.value_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
        
        if field == "Description":
            self.operator_combo.addItems([
                "Contains",
                "Does not contain",
                "Equals",
                "Does not equal"
            ])
            self.value_layout.addWidget(self.text_input)
        elif field == "Amount":
            self.operator_combo.addItems([
                "Greater than",
                "Less than",
                "Equal to",
                "Between"
            ])
            self.value_layout.addWidget(self.amount_input)
        elif field == "Date":
            self.operator_combo.addItems([
                "After",
                "Before",
                "On",
                "Between"
            ])
            self.value_layout.addWidget(self.date_input)
        elif field == "Account":
            self.operator_combo.addItems([
                "Is",
                "Is not"
            ])
            self.value_layout.addWidget(self.account_combo)
        
        # Connect operator change signal
        self.operator_combo.currentTextChanged.connect(self._handle_operator_changed)
        self.operator_combo.currentTextChanged.connect(self.changed)

    def _handle_operator_changed(self, operator: str):
        """Handle changes to the operator selection"""
        # Clean up any existing 'between' inputs
        while self.value_layout.count() > 1:
            widget = self.value_layout.itemAt(1).widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
        
        # Add second input for 'Between' operator
        if operator == "Between":
            self._setup_between_inputs()

    def get_filter_data(self) -> Dict:
        """
        Get the current filter condition data
        
        Returns:
            Dictionary containing field, operator, and value(s)
        """
        field = self.field_combo.currentText()
        operator = self.operator_combo.currentText()
        
        # Initialize the filter data
        filter_data = {
            'field': field,
            'operator': operator,
            'value': None,
            'value2': None  # For 'Between' operator
        }
        
        # Get the primary value based on field type
        if field == "Description":
            filter_data['value'] = self.text_input.text()
        elif field == "Amount":
            try:
                filter_data['value'] = Decimal(self.amount_input.text())
                if operator == "Between" and hasattr(self, 'value2_input'):
                    filter_data['value2'] = Decimal(self.value2_input.text())
            except (decimal.InvalidOperation, ValueError):
                pass
        elif field == "Date":
            filter_data['value'] = self.date_input.date().toPython()
            if operator == "Between" and hasattr(self, 'value2_input'):
                filter_data['value2'] = self.value2_input.date().toPython()
        else:  # Account
            filter_data['value'] = self.account_combo.currentData()
        
        return filter_data

class FilterBar(QWidget):
    """Widget for managing multiple filter conditions"""
    # Signal emitted when filters change
    filters_changed = Signal(dict)  # List of filter conditions
    
    def __init__(self, accounts=None, parent=None):
        """
        Initialise the filter bar
        
        Args:
            accounts: Optional list of account objects for account filtering
            parent: Parent widget
        """
        super().__init__(parent)
        self.accounts = accounts or []
        self.conditions: List[FilterCondition] = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the filter bar user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Top bar with add condition button
        top_bar = QHBoxLayout()
        
        # Add filter condition button
        add_button = QPushButton("Add Filter")
        add_button.clicked.connect(self.add_condition)
        top_bar.addWidget(add_button)
        
        # Logical operator selection
        self.logic_combo = QComboBox()
        self.logic_combo.addItems(["Match ALL (AND)", "Match ANY (OR)"])
        self.logic_combo.currentTextChanged.connect(
            lambda: self.filters_changed.emit(self.get_filters()))
        top_bar.addWidget(self.logic_combo)
        
        top_bar.addStretch()
        
        # Clear all button
        clear_button = QPushButton("Clear All")
        clear_button.clicked.connect(self.clear_all)
        top_bar.addWidget(clear_button)
        
        layout.addLayout(top_bar)
        
        # Container for filter conditions
        self.conditions_widget = QWidget()
        self.conditions_layout = QVBoxLayout(self.conditions_widget)
        self.conditions_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.conditions_widget)
        
        # Add initial condition
        self.add_condition()
    
    def add_condition(self):
        """Add a new filter condition"""
        condition = FilterCondition(self.accounts)
        condition.changed.connect(
            lambda: self.filters_changed.emit(self.get_filters()))
        condition.remove_requested.connect(self.remove_condition)
        self.conditions.append(condition)
        self.conditions_layout.addWidget(condition)
    
    def remove_condition(self, condition):
        """
        Remove a filter condition
        
        Args:
            condition: The FilterCondition widget to remove
        """
        if len(self.conditions) > 1:  # Keep at least one condition
            self.conditions.remove(condition)
            condition.setParent(None)
            condition.deleteLater()
            self.filters_changed.emit(self.get_filters())
    
    def clear_all(self):
        """Clear all filter conditions"""
        # Remove all but first condition
        while len(self.conditions) > 1:
            condition = self.conditions[-1]
            self.remove_condition(condition)
        
        # Reset first condition
        if self.conditions:
            first = self.conditions[0]
            first.field_combo.setCurrentIndex(0)
            first.operator_combo.setCurrentIndex(0)
            if first.text_input.isVisible():
                first.text_input.clear()
            elif first.amount_input.isVisible():
                first.amount_input.clear()
            elif first.date_input.isVisible():
                first.date_input.setDate(QDate.currentDate())
            elif first.account_combo.isVisible():
                first.account_combo.setCurrentIndex(0)
        
        # Update the filter data and emit
        filters = self.get_filters()
        self.filters_changed.emit(filters)
    
    def get_filters(self) -> Dict:
        """
        Get all current filter conditions
        
        Returns:
            Dictionary containing logic operator and list of filter conditions
        """
        return {
            'logic': 'AND' if 'ALL' in self.logic_combo.currentText() else 'OR',
            'conditions': [c.get_filter_data() for c in self.conditions]
        }