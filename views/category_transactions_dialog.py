# File: views/category_transactions_dialog.py

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTableView, 
                             QLabel, QPushButton, QHBoxLayout)
from PySide6.QtCore import Qt
from .transaction_view import TransactionTableModel

class CategoryTransactionsDialog(QDialog):
    """Dialog for displaying transactions associated with a specific category"""
    def __init__(self, category, transaction_controller, parent=None):
        """
        Initialise the category transactions dialog
        
        Args:
            category: The category whose transactions to display
            transaction_controller: The transaction controller instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.category = category
        self.controller = transaction_controller
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog's user interface"""
        self.setWindowTitle(f"Transactions - {self.category.name}")
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Add header with category details
        header_layout = QHBoxLayout()
        category_path = " → ".join([cat.name for cat in 
            self.controller.category_controller.get_category_path(self.category.id)])
        header_label = QLabel(f"Category: {category_path}")
        header_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(header_label)
        layout.addLayout(header_layout)
        
        # Create transaction table
        self.table_view = QTableView()
        self.table_model = CategoryTransactionModel(self.controller, self.category)
        self.table_view.setModel(self.table_model)
        
        # Configure table view
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSortingEnabled(True)
        
        layout.addWidget(self.table_view)
        
        # Add close button
        button_layout = QHBoxLayout()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)


class CategoryTransactionModel(TransactionTableModel):
    """Model for displaying transactions for a specific category"""
    def __init__(self, controller, category):
        """
        Initialise the category transaction model
        
        Args:
            controller: The transaction controller instance
            category: The category whose transactions to display
        """
        super().__init__(controller)
        self.category = category
        self.refresh_data()
    
    def refresh_data(self, filter_type="category"):
        """
        Refresh the model's transaction data
        
        Args:
            filter_type: The type of filter to apply (ignored in this subclass)
        """
        self.beginResetModel()
        # Filter transactions to only show those for this category
        self.transactions = [t for t in self.controller.get_transactions()
                           if t.category_id == self.category.id]
        self.endResetModel()