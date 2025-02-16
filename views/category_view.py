# File: views/category_view.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeView, QHeaderView,
    QPushButton, QHBoxLayout, QMenu, QMessageBox, QDialog
)
from typing import List, Set
from PySide6.QtCore import Qt, QAbstractItemModel, QModelIndex, Slot
from controllers.category_controller import CategoryController
from views.add_category_dialog import AddCategoryDialog
from views.bank_account_dialog import AddBankAccountDialog

class CategoryTreeModel(QAbstractItemModel):
    """Model for displaying categories in a tree view"""
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.categories = self.controller.get_categories()
        self._build_tree()
    
    def _build_tree(self):
        """Build tree structure from flat category list"""
        self.root_items = []
        self.category_map = {}  # Maps category IDs to their objects
        
        # First, map all categories by their ID
        for category in self.categories:
            self.category_map[category.id] = {
                'item': category,
                'children': []
            }
        
        # Then build the tree structure
        for category in self.categories:
            if category.parent_id is None:
                self.root_items.append(self.category_map[category.id])
            else:
                parent = self.category_map.get(category.parent_id)
                if parent:
                    parent['children'].append(self.category_map[category.id])

    def index(self, row, column, parent=QModelIndex()):
        """Create index for accessing data"""
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        
        if not parent.isValid():
            if row < len(self.root_items):
                return self.createIndex(row, column, self.root_items[row])
        else:
            parent_item = parent.internalPointer()
            if row < len(parent_item['children']):
                return self.createIndex(row, column, parent_item['children'][row])
        
        return QModelIndex()

    def parent(self, index):
        """Get parent index of given index"""
        if not index.isValid():
            return QModelIndex()
        
        item = index.internalPointer()
        parent_id = item['item'].parent_id
        
        if parent_id is None:
            return QModelIndex()
        
        parent = self.category_map.get(parent_id)
        if parent is None:
            return QModelIndex()
        
        # Find the parent's position in its parent's children
        if parent['item'].parent_id is None:
            parent_row = self.root_items.index(parent)
            return self.createIndex(parent_row, 0, parent)
        
        grandparent = self.category_map.get(parent['item'].parent_id)
        if grandparent:
            parent_row = grandparent['children'].index(parent)
            return self.createIndex(parent_row, 0, parent)
        return QModelIndex()

    def rowCount(self, parent=QModelIndex()):
        """Return number of rows under given parent"""
        if not parent.isValid():
            return len(self.root_items)
        
        item = parent.internalPointer()
        return len(item['children'])

    def columnCount(self, parent=QModelIndex()):
        """Return number of columns for the children of given parent"""
        return 2  # Column 0: ID, Column 1: Name

    def data(self, index, role=Qt.DisplayRole):
        """Return data for given index and role"""
        if not index.isValid():
            return None
        
        item = index.internalPointer()['item']
        
        if role == Qt.DisplayRole:
            if index.column() == 0:
                return item.id
            elif index.column() == 1:
                return item.name
        
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Return header data for the view"""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return ["ID", "Category Name"][section]
        return None

    def flags(self, index):
        """Return item flags"""
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def refresh_data(self):
        """Refresh the model data"""
        # Store expanded states before refresh
        expanded_categories = self._get_expanded_categories()
        
        # Perform refresh
        self.beginResetModel()
        self.categories = self.controller.get_categories()
        self._build_tree()
        self.endResetModel()
        
        # Return expanded states for restoration
        return expanded_categories
    
    def _get_expanded_categories(self) -> List[str]:
        """Get list of currently expanded category IDs"""
        expanded = []
        def traverse(index):
            if not index.isValid():
                return
            item = index.internalPointer()['item']
            view = self.treeView
            if view and view.isExpanded(index):
                expanded.append(item.id)
            for row in range(self.rowCount(index)):
                child_index = self.index(row, 0, index)
                traverse(child_index)
        traverse(QModelIndex())
        return expanded

class CategoryView(QWidget):
    """Widget for displaying and managing categories"""
    def __init__(self, controller: CategoryController):
        super().__init__()
        self.controller = controller
        self.expanded_states = []
        self._setup_ui()
        self._setup_connections()
    
    def _setup_ui(self):
        """Initialise the user interface"""
        layout = QVBoxLayout(self)
        
        # Add button toolbar
        button_layout = QHBoxLayout()
        
        # Add Category button
        self.add_button = QPushButton("Add Category")
        self.add_button.clicked.connect(self._add_category)
        button_layout.addWidget(self.add_button)
        
        # Delete Category button
        self.delete_button = QPushButton("Delete Category")
        self.delete_button.clicked.connect(self._delete_category)
        button_layout.addWidget(self.delete_button)
        
        layout.addLayout(button_layout)
        
        # Add navigation toolbar
        nav_layout = QHBoxLayout()
        
        # Move Up button
        self.move_up_button = QPushButton("↑")
        self.move_up_button.setToolTip("Move category up")
        self.move_up_button.clicked.connect(self._move_category_up)
        nav_layout.addWidget(self.move_up_button)
        
        # Move Down button
        self.move_down_button = QPushButton("↓")
        self.move_down_button.setToolTip("Move category down")
        self.move_down_button.clicked.connect(self._move_category_down)
        nav_layout.addWidget(self.move_down_button)
        
        # Promote button (move left)
        self.promote_button = QPushButton("←")
        self.promote_button.setToolTip("Promote category (move out one level)")
        self.promote_button.clicked.connect(self._promote_category)
        nav_layout.addWidget(self.promote_button)
        
        # Demote button (move right)
        self.demote_button = QPushButton("→")
        self.demote_button.setToolTip("Demote category (move in one level)")
        self.demote_button.clicked.connect(self._demote_category)
        nav_layout.addWidget(self.demote_button)
        
        layout.addLayout(nav_layout)
        
        # Create tree view
        self.tree_view = QTreeView()
        self.tree_model = CategoryTreeModel(self.controller)
        self.tree_model.treeView = self.tree_view
        self.tree_view.setModel(self.tree_model)
        
        # Configure tree view
        self.tree_view.setAlternatingRowColors(True)
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.expandAll()  # Start with all nodes expanded
        
        # Configure header
        header = self.tree_view.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        
        layout.addWidget(self.tree_view)
        
        # Connect selection changed signal
        self.tree_view.selectionModel().selectionChanged.connect(self._update_button_states)
    
    def _setup_connections(self):
        """Set up signal/slot connections"""
        self.add_button.clicked.connect(self._add_category)
        self.delete_button.clicked.connect(self._delete_category)
        self.tree_view.customContextMenuRequested.connect(self._show_context_menu)
    
    @Slot()
    def _add_category(self):
        """
        Handle adding a new category or bank account.
        If creating a bank account, shows additional dialog for bank details.
        """
        current = self.tree_view.currentIndex()
        if not current.isValid():
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a parent category first."
            )
            return

        parent_item = current.internalPointer()['item']
        
        # Check if we're under the Assets category (id starts with '1')
        is_under_assets = parent_item.id.startswith('1')
        
        # Show appropriate dialog
        if is_under_assets:
            dialog = AddCategoryDialog(parent_item, self, allow_bank_account=True)
        else:
            dialog = AddCategoryDialog(parent_item, self, allow_bank_account=False)
            
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_category_data()
            
            if data.get('is_bank_account'):
                # Show bank account dialog to get additional details
                bank_dialog = AddBankAccountDialog(self)
                if bank_dialog.exec_() == QDialog.Accepted:
                    bank_data = bank_dialog.get_account_data()
                    
                    # Add bank account with all necessary details
                    # Remove name from bank_data since we pass it separately
                    account_name = bank_data.pop('name')  # Remove and store name
                    success = self.controller.add_bank_account(
                        name=account_name,
                        parent_id=parent_item.id,
                        **bank_data  # Now bank_data won't include name
                    )
                    if success:
                        self.refresh_tree()
                        # Emit signal to update account view if needed
                        if hasattr(self, 'account_added'):
                            self.account_added.emit()
                    else:
                        QMessageBox.warning(
                            self,
                            "Error",
                            "Failed to create bank account. Please check the details and try again."
                        )
            else:
                # Regular category addition
                success = self.controller.add_category(
                    name=data['name'],
                    parent_id=parent_item.id,
                    category_type=data['category_type'],
                    tax_type=data['tax_type'],
                    is_bank_account=False
                )
                
                if success:
                    self.refresh_tree()
                else:
                    QMessageBox.warning(
                        self,
                        "Error",
                        "Failed to add category. Please check the details and try again."
                    )

    def _add_account(self):
        """Handle adding a new bank account"""
        current = self.tree_view.currentIndex()
        if not current.isValid():
            QMessageBox.warning(
                self,
                "Selection Required",
                "Please select a category under Assets to add the account to."
            )
            return
            
        parent_item = current.internalPointer()['item']
        
        # Check if we're under the Assets tree
        if not parent_item.id.startswith('1'):
            QMessageBox.warning(
                self,
                "Invalid Location",
                "Bank accounts can only be created under the Assets category."
            )
            return
        
        # Show bank account dialog
        dialog = AddBankAccountDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            account_data = dialog.get_account_data()
            # Add parent_id to the account data
            account_data['parent_id'] = parent_item.id
            
            # Try to add the account
            if self.controller.add_bank_account(**account_data):
                # Refresh the tree view while maintaining expanded states
                self.refresh_tree()
                
                # Notify any registered observers (e.g., AccountView)
                self.account_added.emit()  # New signal to notify of account addition
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Failed to add account. Please check the details and try again."
                )

    @Slot()
    def _delete_category(self):
        """Handle deleting a category"""
        current = self.tree_view.currentIndex()
        if current.isValid():
            item = current.internalPointer()['item']
            if item.parent_id is None:
                QMessageBox.warning(
                    self,
                    "Cannot Delete",
                    "Root categories cannot be deleted."
                )
                return
            
            if self.controller.delete_category(item.id):
                self.refresh_tree()
    
    @Slot()
    def _show_context_menu(self, position):
        """Show context menu for tree view"""
        menu = QMenu()
        
        # Add actions based on selected item
        current = self.tree_view.indexAt(position)
        if current.isValid():
            menu.addAction("Add Subcategory", self._add_category)
            
            item = current.internalPointer()['item']
            if item.parent_id is not None:  # Not a root category
                menu.addAction("Delete", self._delete_category)
        
        if menu.actions():
            menu.exec_(self.tree_view.viewport().mapToGlobal(position))

    def _update_button_states(self):
        """Update navigation button states based on current selection"""
        current = self.tree_view.currentIndex()
        if not current.isValid():
            # Disable all buttons if nothing is selected
            self.move_up_button.setEnabled(False)
            self.move_down_button.setEnabled(False)
            self.promote_button.setEnabled(False)
            self.demote_button.setEnabled(False)
            return
        
        item = current.internalPointer()['item']
        
        # Don't allow moving root categories
        if item.parent_id is None:
            self.move_up_button.setEnabled(False)
            self.move_down_button.setEnabled(False)
            self.promote_button.setEnabled(False)
            self.demote_button.setEnabled(False)
            return
        
        # Check if we can move up/down
        parent = self.tree_view.model().parent(current)
        siblings = self.controller.model.get_children(item.parent_id)
        current_idx = siblings.index(item)
        
        self.move_up_button.setEnabled(current_idx > 0)
        self.move_down_button.setEnabled(current_idx < len(siblings) - 1)
        
        # Check if we can promote/demote
        parent_item = parent.internalPointer()['item'] if parent.isValid() else None
        can_promote = parent_item and parent_item.parent_id is not None
        can_demote = current_idx > 0  # Can demote if not first sibling
        
        self.promote_button.setEnabled(can_promote)
        self.demote_button.setEnabled(can_demote)

    def _move_category_up(self):
        """Move the selected category up in its current level"""
        current = self.tree_view.currentIndex()
        if not current.isValid():
            return
            
        item = current.internalPointer()['item']
        siblings = self.controller.model.get_children(item.parent_id)
        current_idx = siblings.index(item)
        
        if current_idx > 0:
            # Swap IDs with the previous sibling
            prev_sibling = siblings[current_idx - 1]
            self.controller.model.swap_categories(item.id, prev_sibling.id)
            self.tree_model.refresh_data()
            
            # Restore selection
            self._select_category_by_id(item.id)

    def _move_category_down(self):
        """Move the selected category down in its current level"""
        current = self.tree_view.currentIndex()
        if not current.isValid():
            return
            
        item = current.internalPointer()['item']
        siblings = self.controller.model.get_children(item.parent_id)
        current_idx = siblings.index(item)
        
        if current_idx < len(siblings) - 1:
            # Swap IDs with the next sibling
            next_sibling = siblings[current_idx + 1]
            self.controller.model.swap_categories(item.id, next_sibling.id)
            self.tree_model.refresh_data()
            
            # Restore selection
            self._select_category_by_id(item.id)

    def _promote_category(self):
        """Move the category out one level (to its parent's level)"""
        current = self.tree_view.currentIndex()
        if not current.isValid():
            return
            
        item = current.internalPointer()['item']
        if self.controller.model.promote_category(item.id):
            self.refresh_tree()
            self._select_category_by_id(item.id)
        else:
            QMessageBox.warning(
                self,
                "Operation Failed",
                "Could not promote category. Please check if this operation is allowed."
            )

    def _demote_category(self):
        """Move the category in one level (under previous sibling)"""
        current = self.tree_view.currentIndex()
        if not current.isValid():
            return
            
        item = current.internalPointer()['item']
        siblings = self.controller.model.get_children(item.parent_id)
        current_idx = siblings.index(item)
        
        if current_idx > 0:
            # Move under previous sibling
            prev_sibling = siblings[current_idx - 1]
            if self.controller.model.demote_category(item.id, prev_sibling.id):
                self.refresh_tree()
                self._select_category_by_id(item.id)
            else:
                QMessageBox.warning(
                    self,
                    "Operation Failed",
                    "Could not demote category. Please check if this operation is allowed."
                )

    def _select_category_by_id(self, category_id):
        """Helper method to select a category by its ID"""
        def find_index(parent_index, target_id):
            rows = self.tree_model.rowCount(parent_index)
            for row in range(rows):
                index = self.tree_model.index(row, 0, parent_index)
                item = index.internalPointer()['item']
                if item.id == target_id:
                    return index
                # Check children
                found = find_index(index, target_id)
                if found.isValid():
                    return found
            return QModelIndex()
        
        index = find_index(QModelIndex(), category_id)
        if index.isValid():
            self.tree_view.setCurrentIndex(index)
            self.tree_view.scrollTo(index)

    def refresh_tree(self):
        """
        Refresh the tree while maintaining expanded states and current selection
        """
        # Store current expanded states and selection
        expanded_states = self._get_expanded_states()
        current_index = self.tree_view.currentIndex()
        current_id = None
        if current_index.isValid():
            current_id = current_index.internalPointer()['item'].id
        
        # Refresh data
        self.tree_model.refresh_data()
        
        # Restore expanded states
        self._restore_expanded_states(expanded_states)
        
        # Restore selection if possible
        if current_id:
            self._select_item_by_id(current_id)

    def _get_expanded_states(self) -> Set[str]:
        """Get the IDs of currently expanded categories"""
        expanded = set()
        
        def collect_expanded(index):
            if self.tree_view.isExpanded(index):
                item = index.internalPointer()['item']
                expanded.add(item.id)
            
            for row in range(self.tree_model.rowCount(index)):
                child_index = self.tree_model.index(row, 0, index)
                collect_expanded(child_index)
        
        collect_expanded(QModelIndex())
        return expanded

    def _restore_expanded_states(self, expanded_states: Set[str]):
        """Restore previously expanded categories"""
        def expand_items(index):
            if not index.isValid():
                # Handle root level
                for row in range(self.tree_model.rowCount()):
                    child_index = self.tree_model.index(row, 0, QModelIndex())
                    expand_items(child_index)
                return

            item_data = index.internalPointer()
            if item_data is None:
                return
                
            try:
                item = item_data['item']
                if item.id in expanded_states:
                    self.tree_view.setExpanded(index, True)
                
                for row in range(self.tree_model.rowCount(index)):
                    child_index = self.tree_model.index(row, 0, index)
                    expand_items(child_index)
            except (TypeError, KeyError):
                # Handle any potential errors with item data
                pass
        
        expand_items(QModelIndex())

    def _select_item_by_id(self, item_id: str):
        """Select an item in the tree by its ID"""
        def find_and_select(index):
            if not index.isValid():
                for row in range(self.tree_model.rowCount()):
                    child_index = self.tree_model.index(row, 0, QModelIndex())
                    if find_and_select(child_index):
                        return True
                return False

            item_data = index.internalPointer()
            if item_data is None:
                return False
                
            try:
                item = item_data['item']
                if item.id == item_id:
                    self.tree_view.setCurrentIndex(index)
                    return True
                
                for row in range(self.tree_model.rowCount(index)):
                    child_index = self.tree_model.index(row, 0, index)
                    if find_and_select(child_index):
                        return True
                return False
            except (TypeError, KeyError):
                return False
        
        find_and_select(QModelIndex())