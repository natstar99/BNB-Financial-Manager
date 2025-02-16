# File: controllers/category_controller.py

from typing import List, Optional
from models.category_model import CategoryModel, Category, CategoryType

class CategoryController:
    """Controller for managing category operations"""
    def __init__(self, model: CategoryModel):
        self.model = model
    
    def get_categories(self):
        """Retrieve all categories"""
        return self.model.get_categories()

    def add_category(self, name: str, parent_id: str, category_type: CategoryType, 
                    tax_type: Optional[str] = None, is_bank_account: bool = False) -> bool:
        """Add a new category under the specified parent"""
        try:
            # Get all children of parent to determine new ID
            cursor = self.model.db.execute(
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
            self.model.db.execute("""
                INSERT INTO categories (id, name, parent_id, category_type, tax_type, is_bank_account)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (new_id, name, parent_id, category_type.value, tax_type, is_bank_account))
            
            self.model.db.commit()
            return True
        except Exception as e:
            print(f"Error adding category: {e}")
            return False
        
    def add_bank_account(self, name: str, parent_id: str, **bank_data) -> bool:
        """Add a new bank account category with associated bank details"""
        try:
            # Start transaction
            self.model.db.execute("BEGIN TRANSACTION")
            
            # Add category first
            category_success = self.add_category(
                name=name,
                parent_id=parent_id,
                category_type=CategoryType.TRANSACTION,
                tax_type=None,
                is_bank_account=True
            )
            
            if category_success:
                # Get the new category ID
                cursor = self.model.db.execute(
                    "SELECT id FROM categories WHERE parent_id = ? AND name = ?",
                    (parent_id, name)
                )
                category_id = cursor.fetchone()[0]
                
                # Add bank account details
                self.model.db.execute("""
                    INSERT INTO bank_accounts (
                        id, name, account_number, bsb, bank_name, notes
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (category_id, name, bank_data['account_number'], 
                    bank_data['bsb'], bank_data['bank_name'], 
                    bank_data.get('notes')))
                
                self.model.db.execute("COMMIT")
                return True
            
            self.model.db.execute("ROLLBACK")
            return False
            
        except Exception as e:
            self.model.db.execute("ROLLBACK")
            print(f"Error adding bank account: {e}")
            return False

    def move_category(self, category_id: str, new_parent_id: str) -> bool:
        """Move a category to a new parent"""
        try:
            self.model.move_category(category_id, new_parent_id)
            return True
        except Exception as e:
            print(f"Error moving category: {e}")
            return False

    def delete_category(self, category_id: str) -> bool:
        """Delete a category and its children if it has no transactions"""
        return self.model.delete_category(category_id)

    def get_category_path(self, category_id: str) -> List[Category]:
        """Get the full path of categories from root to given category"""
        path = []
        current_id = category_id
        
        while current_id:
            categories = self.model.get_all_categories()
            current = next((c for c in categories if c.id == current_id), None)
            if current:
                path.insert(0, current)
                current_id = current.parent_id
            else:
                break
        
        return path