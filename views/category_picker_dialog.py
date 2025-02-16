# File: views/category_picker_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTreeView, QPushButton,
    QHBoxLayout, QHeaderView
)
from PySide6.QtCore import Qt, QAbstractItemModel, QModelIndex

class CategoryPickerDialog(QDialog):
    """Dialog for picking a transaction category"""
    def __init__(self, category_controller, parent=None):
        super().__init__(parent)
        self.controller = category_controller
        self.selected_category = None
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("Select Category")
        self.resize(400, 500)
        layout = QVBoxLayout(self)
        
        # Create tree view
        self.tree_view = QTreeView()
        from views.category_view import CategoryTreeModel  # Import here to avoid circular import
        self.tree_model = CategoryTreeModel(self.controller)
        self.tree_view.setModel(self.tree_model)
        
        # Configure tree view
        self.tree_view.setAlternatingRowColors(True)
        self.tree_view.expandAll()
        header = self.tree_view.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        
        layout.addWidget(self.tree_view)
        
        # Buttons
        button_layout = QHBoxLayout()
        select_button = QPushButton("Select")
        select_button.clicked.connect(self.handle_selection)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(select_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
    
    def handle_selection(self):
        """Handle category selection"""
        index = self.tree_view.currentIndex()
        if index.isValid():
            item = index.internalPointer()['item']
            # Only allow selecting transaction categories, not groups
            if item.category_type.value == 'transaction':
                self.selected_category = item
                self.accept()
            else:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "Invalid Selection",
                    "Please select a transaction category, not a group."
                )