# File: models/category_model.py

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

class CategoryType(Enum):
    """Enumeration of category types"""
    ROOT = "root"             # Level 0: Primary categories (Assets, Liabilities, etc.)
    GROUP = "group"          # Intermediate levels: Organisational groups
    TRANSACTION = "transaction"  # Leaf nodes: Categories for actual transactions

    def get_display_name(self) -> str:
        """Get user-friendly display name for the category type"""
        if self == CategoryType.ROOT:
            return "Primary Category"
        elif self == CategoryType.GROUP:
            return "Category Group"
        else:
            return "Transaction Category"

@dataclass
class Category:
    """Data class representing a category in the FBS"""
    id: str
    name: str
    parent_id: Optional[str] = None
    category_type: CategoryType = CategoryType.TRANSACTION  # Default to transaction type
    tax_type: Optional[str] = None
    level: int = 0

class CategoryModel:
    """Model for managing categories in the Financial Breakdown Structure"""
    def __init__(self, db_manager):
        """Initialise the category model with a database manager"""
        self.db = db_manager
        self._ensure_root_categories()

    def _ensure_root_categories(self):
        """Ensure root categories and essential groups exist in the database"""
        # First ensure root categories
        root_categories = [
            ('1', 'Assets'),
            ('2', 'Liabilities'),
            ('3', 'Equity'),
            ('4', 'Income'),
            ('5', 'Expenses')
        ]
        
        for cat_id, name in root_categories:
            self.db.execute("""
                INSERT OR IGNORE INTO categories 
                (id, name, parent_id, category_type, tax_type)
                VALUES (?, ?, NULL, ?, NULL)
            """, (cat_id, name, CategoryType.ROOT.value))

        # Then ensure the Accounts group exists under Assets
        self.db.execute("""
            INSERT OR IGNORE INTO categories
            (id, name, parent_id, category_type, tax_type)
            VALUES ('1.1', 'Accounts', '1', ?, NULL)
        """, (CategoryType.GROUP.value,))
        
        self.db.commit()
    
    def get_categories(self) -> List[Category]:
        """Retrieve all categories from the database"""
        cursor = self.db.execute("""
            SELECT id, name, parent_id, category_type, tax_type 
            FROM categories
            ORDER BY id
        """)
        categories = []
        for row in cursor:
            cat = Category(
                id=row[0],
                name=row[1],
                parent_id=row[2],
                category_type=CategoryType(row[3]) if row[3] else CategoryType.TRANSACTION,
                tax_type=row[4]
            )
            categories.append(cat)
        return categories

    def get_children(self, parent_id: str) -> List[Category]:
        """Get immediate children of a category"""
        cursor = self.db.execute("""
            SELECT id, name, parent_id, category_type, tax_type 
            FROM categories 
            WHERE parent_id = ?
            ORDER BY id
        """, (parent_id,))
        return [
            Category(
                id=row[0],
                name=row[1],
                parent_id=row[2],
                category_type=CategoryType(row[3]) if row[3] else CategoryType.TRANSACTION,
                tax_type=row[4]
            ) for row in cursor
        ]

    def add_category(self, name: str, parent_id: str, category_type: CategoryType, tax_type: Optional[str] = None) -> bool:
        """Add a new category under the specified parent"""
        try:
            # Get all children of parent to determine new ID
            cursor = self.db.execute(
                "SELECT id FROM categories WHERE parent_id = ? ORDER BY id DESC",
                (parent_id,)
            )
            existing_ids = [row[0] for row in cursor]
            
            # Determine new ID
            if not existing_ids:
                # First child - append .1 to parent ID
                new_id = f"{parent_id}.1"
            else:
                # Get last ID and increment
                last_id = existing_ids[0]
                last_number = int(last_id.split('.')[-1])
                new_id = f"{parent_id}.{last_number + 1}"
            
            # Insert new category
            self.db.execute("""
                INSERT INTO categories (id, name, parent_id, category_type, tax_type)
                VALUES (?, ?, ?, ?, ?)
            """, (new_id, name, parent_id, category_type.value, tax_type))
            
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error adding category: {e}")
            return False

    def move_category(self, category_id: str, new_parent_id: str) -> bool:
        """Move a category to a new parent, updating its ID and children's IDs"""
        try:
            # Get current category info
            cursor = self.db.execute(
                "SELECT id, parent_id FROM categories WHERE id = ?",
                (category_id,)
            )
            current = cursor.fetchone()
            if not current:
                return False
            
            old_id = current[0]
            old_prefix = old_id + "."
            
            # Calculate new ID
            siblings = self.get_children(new_parent_id)
            new_id = f"{new_parent_id}.{len(siblings) + 1}"
            new_prefix = new_id + "."
            
            # Update the category and all its descendants
            self.db.execute("""
                UPDATE categories 
                SET id = REPLACE(id, ?, ?),
                    parent_id = CASE 
                        WHEN id = ? THEN ?
                        ELSE REPLACE(parent_id, ?, ?)
                    END
                WHERE id = ? OR id LIKE ?
            """, (old_prefix, new_prefix, category_id, new_parent_id, 
                  old_prefix, new_prefix, category_id, old_id + ".%"))
            
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error moving category: {e}")
            return False

    def delete_category(self, category_id: str) -> bool:
        """Delete a category and all its children"""
        try:
            # Check for transactions using this category
            cursor = self.db.execute(
                "SELECT COUNT(*) FROM transactions WHERE category_id = ? OR category_id LIKE ?",
                (category_id, category_id + ".%")
            )
            if cursor.fetchone()[0] > 0:
                raise ValueError("Cannot delete category with associated transactions")
            
            # Delete category and all children
            self.db.execute(
                "DELETE FROM categories WHERE id = ? OR id LIKE ?",
                (category_id, category_id + ".%")
            )
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error deleting category: {e}")
            return False

    def swap_categories(self, category1_id: str, category2_id: str) -> bool:
        """Swap the ordering of two categories within the same level"""
        try:
            # Start transaction
            self.db.execute("BEGIN TRANSACTION")
            
            # Get the categories
            cursor = self.db.execute(
                "SELECT id, parent_id FROM categories WHERE id IN (?, ?)",
                (category1_id, category2_id)
            )
            cats = cursor.fetchall()
            if len(cats) != 2:
                raise ValueError("One or both categories not found")

            # Ensure they have the same parent
            if cats[0][1] != cats[1][1]:
                raise ValueError("Categories must have the same parent")

            # Store original IDs and children patterns
            id1, id2 = category1_id, category2_id
            pattern1 = f"{id1}.%"
            pattern2 = f"{id2}.%"

            # Create temporary IDs (ensure they won't conflict with any existing IDs)
            temp1 = f"TEMP1_{id1}"
            temp2 = f"TEMP2_{id2}"

            # First move to temporary IDs
            self.db.execute("""
                UPDATE categories 
                SET id = CASE
                        WHEN id = ? THEN ?
                        ELSE REPLACE(id, ?, ?)
                    END,
                    parent_id = CASE
                        WHEN parent_id = ? THEN ?
                        ELSE REPLACE(parent_id, ?, ?)
                    END
                WHERE id = ? OR id LIKE ?
            """, (id1, temp1, id1 + '.', temp1 + '.', 
                id1, temp1, id1 + '.', temp1 + '.', 
                id1, pattern1))

            self.db.execute("""
                UPDATE categories 
                SET id = CASE
                        WHEN id = ? THEN ?
                        ELSE REPLACE(id, ?, ?)
                    END,
                    parent_id = CASE
                        WHEN parent_id = ? THEN ?
                        ELSE REPLACE(parent_id, ?, ?)
                    END
                WHERE id = ? OR id LIKE ?
            """, (id2, temp2, id2 + '.', temp2 + '.', 
                id2, temp2, id2 + '.', temp2 + '.', 
                id2, pattern2))

            # Then move from temporary to final positions
            self.db.execute("""
                UPDATE categories 
                SET id = CASE
                        WHEN id = ? THEN ?
                        ELSE REPLACE(id, ?, ?)
                    END,
                    parent_id = CASE
                        WHEN parent_id = ? THEN ?
                        ELSE REPLACE(parent_id, ?, ?)
                    END
                WHERE id = ? OR id LIKE ?
            """, (temp1, id2, temp1 + '.', id2 + '.', 
                temp1, id2, temp1 + '.', id2 + '.', 
                temp1, temp1 + '.%'))

            self.db.execute("""
                UPDATE categories 
                SET id = CASE
                        WHEN id = ? THEN ?
                        ELSE REPLACE(id, ?, ?)
                    END,
                    parent_id = CASE
                        WHEN parent_id = ? THEN ?
                        ELSE REPLACE(parent_id, ?, ?)
                    END
                WHERE id = ? OR id LIKE ?
            """, (temp2, id1, temp2 + '.', id1 + '.', 
                temp2, id1, temp2 + '.', id1 + '.', 
                temp2, temp2 + '.%'))

            # Update any references in transactions table
            self.db.execute("""
                UPDATE transactions 
                SET category_id = CASE
                    WHEN category_id = ? THEN ?
                    WHEN category_id LIKE ? THEN REPLACE(category_id, ?, ?)
                    WHEN category_id = ? THEN ?
                    WHEN category_id LIKE ? THEN REPLACE(category_id, ?, ?)
                    ELSE category_id
                END
                WHERE category_id IN (?, ?) 
                OR category_id LIKE ? 
                OR category_id LIKE ?
            """, (temp1, id2, temp1 + '.%', temp1 + '.', id2 + '.',
                temp2, id1, temp2 + '.%', temp2 + '.', id1 + '.',
                temp1, temp2, temp1 + '.%', temp2 + '.%'))

            self.db.execute("COMMIT")
            return True
        except Exception as e:
            self.db.execute("ROLLBACK")
            print(f"Error swapping categories: {e}")
            return False
        
    def find_next_available_id(self, base_id: str) -> str:
        """
        Find the next available category ID at the specified level
        For example, if trying to create 4.4 but it exists, will try 4.5, 4.6, etc.
        
        Args:
            base_id: The desired base ID (e.g., '4.3' when moving to that level)
        
        Returns:
            str: The next available ID at that level
        """
        # Get all existing categories
        cursor = self.db.execute("SELECT id FROM categories WHERE id LIKE ?", 
                            (f"{base_id}.%" if '.' in base_id else f"{base_id}%",))
        existing_ids = {row[0] for row in cursor}
        
        # If base_id itself is available, use it
        if base_id not in existing_ids:
            return base_id
        
        # Split the base_id into parts
        parts = base_id.split('.')
        parent_prefix = '.'.join(parts[:-1])
        if parent_prefix:
            parent_prefix += '.'
        
        # Find the highest number at this level
        level_ids = {id for id in existing_ids if id.startswith(parent_prefix)}
        max_num = 0
        for id in level_ids:
            try:
                num = int(id.split('.')[-1])
                max_num = max(max_num, num)
            except ValueError:
                continue
        
        # Return next available number
        return f"{parent_prefix}{max_num + 1}"

    def promote_category(self, category_id: str) -> bool:
        """Move a category out one level (left shift)"""
        try:
            self.db.execute("BEGIN TRANSACTION")
            
            # Get current category and its parent
            cursor = self.db.execute(
                "SELECT id, parent_id FROM categories WHERE id = ?",
                (category_id,)
            )
            current = cursor.fetchone()
            if not current or not current[1]:  # No category or no parent
                return False
            
            # Get parent's parent (new parent)
            cursor = self.db.execute(
                "SELECT parent_id FROM categories WHERE id = ?",
                (current[1],)
            )
            new_parent = cursor.fetchone()
            if not new_parent:  # Parent not found
                return False
            
            # Find next available ID at the new level
            parent_prefix = new_parent[0] + '.' if new_parent[0] else ''
            base_id = f"{parent_prefix}{int(category_id.split('.')[-1])}"
            new_id = self.find_next_available_id(base_id)
            
            # Update the category and its children
            old_prefix = category_id + '.'
            new_prefix = new_id + '.'
            
            self.db.execute("""
                UPDATE categories 
                SET id = CASE 
                        WHEN id = ? THEN ?
                        ELSE REPLACE(id, ?, ?)
                    END,
                    parent_id = CASE 
                        WHEN id = ? THEN ?
                        ELSE REPLACE(parent_id, ?, ?)
                    END
                WHERE id = ? OR id LIKE ?
            """, (category_id, new_id, old_prefix, new_prefix, 
                category_id, new_parent[0], old_prefix, new_prefix, 
                category_id, category_id + '.%'))
            
            # Update any related records
            self.db.execute("UPDATE transactions SET category_id = ? WHERE category_id = ?",
                        (new_id, category_id))
            
            self.db.execute("COMMIT")
            return True
            
        except Exception as e:
            self.db.execute("ROLLBACK")
            print(f"Error promoting category: {e}")
            return False

    def demote_category(self, category_id: str, new_parent_id: str) -> bool:
        """Move a category in one level (right shift under specified parent)"""
        try:
            self.db.execute("BEGIN TRANSACTION")
            
            # Get current category info
            cursor = self.db.execute(
                "SELECT id, parent_id FROM categories WHERE id = ?",
                (category_id,)
            )
            current = cursor.fetchone()
            if not current:
                return False
            
            # Find next available ID under new parent
            cursor = self.db.execute(
                "SELECT id FROM categories WHERE parent_id = ? ORDER BY id DESC",
                (new_parent_id,)
            )
            existing = cursor.fetchall()
            
            if existing:
                # Get the highest number and increment
                highest_num = max(int(id[0].split('.')[-1]) for id in existing)
                new_id = f"{new_parent_id}.{highest_num + 1}"
            else:
                # First child under this parent
                new_id = f"{new_parent_id}.1"
            
            # Update the category and its children
            old_prefix = category_id + '.'
            new_prefix = new_id + '.'
            
            self.db.execute("""
                UPDATE categories 
                SET id = CASE 
                        WHEN id = ? THEN ?
                        ELSE REPLACE(id, ?, ?)
                    END,
                    parent_id = CASE 
                        WHEN id = ? THEN ?
                        ELSE REPLACE(parent_id, ?, ?)
                    END
                WHERE id = ? OR id LIKE ?
            """, (category_id, new_id, old_prefix, new_prefix, 
                category_id, new_parent_id, old_prefix, new_prefix, 
                category_id, category_id + '.%'))
            
            # Update any related records
            self.db.execute("UPDATE transactions SET category_id = ? WHERE category_id = ?",
                        (new_id, category_id))
            
            self.db.execute("COMMIT")
            return True
            
        except Exception as e:
            self.db.execute("ROLLBACK")
            print(f"Error demoting category: {e}")
            return False