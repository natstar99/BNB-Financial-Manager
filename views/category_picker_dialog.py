# File: views/category_picker_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTreeView, QPushButton, 
    QHBoxLayout, QRadioButton, QFrame, QMessageBox,
    QLineEdit, QLabel, QHeaderView, QButtonGroup
)
from PySide6.QtCore import Qt, QSortFilterProxyModel, QModelIndex

class CategoryPickerDialog(QDialog):
    """Dialog for picking a transaction category with search functionality"""
    def __init__(self, category_controller, parent=None):
        super().__init__(parent)
        self.controller = category_controller
        self.selected_category = None
        self.is_internal_transfer = False
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the dialog's user interface"""
        self.setWindowTitle("Select Category")
        self.resize(400, 500)
        layout = QVBoxLayout(self)
        
        # Add radio buttons group at the top
        radio_layout = QHBoxLayout()
        
        # Create button group to make options mutually exclusive
        self.status_group = QButtonGroup(self)
        
        # Internal Transfer radio button
        self.internal_transfer_radio = QRadioButton("Internal Transfer")
        self.internal_transfer_radio.toggled.connect(self._handle_special_state_toggle)
        self.status_group.addButton(self.internal_transfer_radio)
        radio_layout.addWidget(self.internal_transfer_radio)
        
        # Hidden Transaction radio button
        self.hidden_radio = QRadioButton("Mark as Hidden")
        self.hidden_radio.toggled.connect(self._handle_special_state_toggle)
        self.status_group.addButton(self.hidden_radio)
        radio_layout.addWidget(self.hidden_radio)
        
        layout.addLayout(radio_layout)

        # Add separator line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # Add search box
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Type to filter categories...")
        self.search_box.textChanged.connect(self._filter_categories)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_box)
        layout.addLayout(search_layout)

        # Create tree view with proxy model for filtering
        self.tree_view = QTreeView()
        from views.category_view import CategoryTreeModel  # Import here to avoid circular import
        self.tree_model = CategoryTreeModel(self.controller)
        
        # Create proxy model for filtering
        self.proxy_model = CategoryFilterProxyModel(self.tree_view)
        self.proxy_model.setSourceModel(self.tree_model)
        self.tree_view.setModel(self.proxy_model)
        
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
        
        # Set focus to search box and select all text
        self.search_box.setFocus()
        
        # Handle Enter key in search box
        self.search_box.returnPressed.connect(self._handle_enter_key)
    
    def _handle_enter_key(self):
        """Handle Enter key in search box - select single visible item if available"""
        if self.internal_transfer_radio.isChecked():
            return
            
        # Count visible transaction categories
        visible_items = []
        for row in range(self.proxy_model.rowCount(QModelIndex())):
            self._collect_visible_transaction_categories(
                self.proxy_model.index(row, 0, QModelIndex()),
                visible_items
            )
            
        # If exactly one transaction category is visible, select it
        if len(visible_items) == 1:
            self.tree_view.setCurrentIndex(visible_items[0])
            self.handle_selection()
    
    def _collect_visible_transaction_categories(self, index, visible_items):
        """Recursively collect visible transaction categories"""
        if not index.isValid():
            return
            
        # Check if this is a transaction category
        source_index = self.proxy_model.mapToSource(index)
        item = source_index.internalPointer()['item']
        if item.category_type.value == 'transaction':
            visible_items.append(index)
            
        # Check children
        for row in range(self.proxy_model.rowCount(index)):
            child_index = self.proxy_model.index(row, 0, index)
            self._collect_visible_transaction_categories(child_index, visible_items)
    
    def _filter_categories(self, text):
        """Filter categories based on search text and handle single results"""
        # Update proxy model filter
        self.proxy_model.setFilterWildcard(text)
        
        if text:
            # Expand all items when filtering
            self.tree_view.expandAll()
            
            # Count visible transaction categories
            visible_items = []
            for row in range(self.proxy_model.rowCount(QModelIndex())):
                self._collect_visible_transaction_categories(
                    self.proxy_model.index(row, 0, QModelIndex()),
                    visible_items
                )
            
            # If exactly one transaction category is visible, select it
            if len(visible_items) == 1:
                self.tree_view.setCurrentIndex(visible_items[0])
        else:
            # Keep expanded to maintain consistency
            self.tree_view.expandAll()
    
    def _handle_special_state_toggle(self, checked):
        """Handle toggling of special state radio buttons"""
        is_special_state = self.internal_transfer_radio.isChecked() or self.hidden_radio.isChecked()
        
        # Disable/enable the tree view and search based on special state selection
        self.tree_view.setEnabled(not is_special_state)
        self.search_box.setEnabled(not is_special_state)
        
        # Update internal transfer state
        self.is_internal_transfer = self.internal_transfer_radio.isChecked()
        self.is_hidden = self.hidden_radio.isChecked()
        
    def __init__(self, category_controller, parent=None):
        super().__init__(parent)
        self.controller = category_controller
        self.selected_category = None
        self.is_internal_transfer = False
        self.is_hidden = False  # Add hidden state tracking
        self.setup_ui()
    
    def handle_selection(self):
        """Handle category selection, including special states"""
        if self.internal_transfer_radio.isChecked() or self.hidden_radio.isChecked():
            self.selected_category = None
            self.accept()
        else:
            # Get the actual model index from the proxy model
            proxy_index = self.tree_view.currentIndex()
            if proxy_index.isValid():
                # Convert proxy index to source index
                source_index = self.proxy_model.mapToSource(proxy_index)
                item = source_index.internalPointer()['item']
                # Only allow selecting transaction categories, not groups
                if item.category_type.value == 'transaction':
                    self.selected_category = item
                    self.is_internal_transfer = False
                    self.is_hidden = False
                    self.accept()
                else:
                    QMessageBox.warning(
                        self,
                        "Invalid Selection",
                        "Please select a transaction category, not a group."
                    )

class CategoryFilterProxyModel(QSortFilterProxyModel):
    """Proxy model for filtering categories"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filter_text = ""
    
    def filterAcceptsRow(self, source_row, source_parent):
        """
        Determine if a row should be shown based on the filter
        Shows a row if it or any of its children match the filter
        """
        if not self.filter_text:
            return True
            
        # Get the index for this row
        source_index = self.sourceModel().index(source_row, 1, source_parent)
        if not source_index.isValid():
            return False
            
        # Check if this item matches
        item_data = source_index.internalPointer()['item']
        if self.filter_text.lower() in item_data.name.lower():
            return True
            
        # Check all children recursively
        return self._any_children_match(source_index)
    
    def _any_children_match(self, parent_index):
        """Recursively check if any children match the filter"""
        for row in range(self.sourceModel().rowCount(parent_index)):
            child_index = self.sourceModel().index(row, 1, parent_index)
            if not child_index.isValid():
                continue
                
            item_data = child_index.internalPointer()['item']
            if self.filter_text.lower() in item_data.name.lower():
                return True
                
            if self._any_children_match(child_index):
                return True
                
        return False
    
    def setFilterWildcard(self, text):
        """Set the filter text and trigger filtering"""
        self.filter_text = text
        self.invalidateFilter()
