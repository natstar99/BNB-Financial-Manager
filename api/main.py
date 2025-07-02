"""
BNB Financial Manager API

FastAPI-based REST API for the BNB Financial Manager application.
Provides endpoints for transaction management, categorisation, and file imports.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import os

# Add the parent directory to the path so we can import existing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database_manager import DatabaseManager
from models.transaction_model import TransactionModel
from models.category_model import CategoryModel
from models.bank_account_model import BankAccountModel
from utils.qif_parser import QIFParser
from utils.csv_parser import CSVParser

app = FastAPI(title="BNB Financial Manager API", version="1.0.0")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize models with existing business logic
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "finance.db")
db_manager = DatabaseManager(db_path)
transaction_model = TransactionModel(db_manager)
category_model = CategoryModel(db_manager)
bank_account_model = BankAccountModel(db_manager)

# Pydantic models for API requests/responses
class TransactionResponse(BaseModel):
    id: int
    date: str
    account: str
    account_name: Optional[str]
    description: str
    withdrawal: float
    deposit: float
    category_id: Optional[str]
    category_name: Optional[str]
    tax_type: Optional[str]
    is_tax_deductible: bool
    is_hidden: bool
    is_matched: bool
    is_internal_transfer: bool

class CategoryResponse(BaseModel):
    id: str
    name: str
    parent_id: Optional[str]
    category_type: str
    tax_type: Optional[str]
    is_bank_account: bool

class BankAccountResponse(BaseModel):
    id: str
    name: str
    account_number: Optional[str]
    bsb: Optional[str]
    bank_name: Optional[str]
    current_balance: float
    last_import_date: Optional[str]
    notes: Optional[str]

class TransactionFilter(BaseModel):
    search_term: Optional[str] = None
    account_filter: Optional[str] = None
    category_filter: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    show_hidden: bool = False
    show_only_uncategorised: bool = False
    show_only_internal_transfers: bool = False

class AnalysisViewRequest(BaseModel):
    name: str
    selectedCategories: List[str]
    selectedPeriod: str
    customDateRange: Dict[str, str]
    aggregation: str
    chartType: str
    showIncome: bool
    showExpenses: bool
    showCumulative: bool
    showAverages: bool

class AnalysisViewResponse(BaseModel):
    id: str
    name: str
    selectedCategories: List[str]
    selectedPeriod: str
    customDateRange: Dict[str, str]
    aggregation: str
    chartType: str
    showIncome: bool
    showExpenses: bool
    showCumulative: bool
    showAverages: bool
    created_at: str
    updated_at: str

@app.get("/")
async def root():
    return {"message": "BNB Financial Manager API"}

# Transaction endpoints
@app.get("/api/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    filter: Optional[str] = "all",
    search: Optional[str] = None,
    account_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = 0
):
    """Get transactions with filtering, pagination and search - OPTIMIZED for 10x performance"""
    try:
        # Single optimized database query with all filters applied at SQL level
        query = """
            SELECT t.id, t.date, t.account, ba.name as account_name, t.description, 
                   t.withdrawal, t.deposit, t.category_id, c.name as category_name, 
                   t.tax_type, t.is_tax_deductible, t.is_hidden, t.is_matched, 
                   t.is_internal_transfer,
                   COUNT(*) OVER() as total_count
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            LEFT JOIN bank_accounts ba ON t.account = ba.id
            WHERE 1=1
        """
        params = []
        
        # Apply filter type at SQL level
        if filter == "uncategorised":
            query += " AND t.category_id IS NULL AND t.is_internal_transfer = 0 AND t.is_hidden = 0"
        elif filter == "categorised":
            query += " AND t.category_id IS NOT NULL AND t.is_internal_transfer = 0 AND t.is_hidden = 0"
        elif filter == "internal_transfers":
            query += " AND t.is_internal_transfer = 1"
        elif filter == "hidden":
            query += " AND t.is_hidden = 1"
        elif filter == "all":
            pass  # Show everything
        else:
            query += " AND t.is_hidden = 0"  # Default to showing non-hidden
        
        # Apply search at SQL level with optimized LIKE
        if search and len(search.strip()) >= 2:
            query += " AND (t.description LIKE ? OR ba.name LIKE ?)"
            search_param = f"%{search.strip()}%"
            params.extend([search_param, search_param])
        
        # Apply account filter at SQL level
        if account_filter:
            query += " AND t.account = ?"
            params.append(account_filter)
            
        # Apply category filter at SQL level
        if category_filter:
            query += " AND t.category_id = ?"
            params.append(category_filter)
            
        # Apply date filters at SQL level
        if date_from:
            query += " AND t.date >= ?"
            params.append(date_from)
            
        if date_to:
            query += " AND t.date <= ?"
            params.append(date_to)
        
        # Order at SQL level
        query += " ORDER BY t.date DESC"
        
        # Only add pagination if limit is specified
        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        
        # Execute optimized query
        cursor = db_manager.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to response format with minimal processing
        result = []
        total_count = 0
        for row in rows:
            if not total_count:
                total_count = row[14]  # total_count from window function
                
            # Format date properly - convert from ISO format to YYYY-MM-DD
            date_str = row[1]
            if 'T' in date_str:
                date_str = date_str.split('T')[0]  # Remove time component if present
            
            result.append({
                "id": row[0],
                "date": date_str,
                "account": row[2],
                "account_name": row[3],
                "description": row[4],
                "withdrawal": float(row[5]) if row[5] else 0.0,
                "deposit": float(row[6]) if row[6] else 0.0,
                "category_id": row[7],
                "category_name": row[8],
                "tax_type": row[9] if row[9] else "NONE",
                "is_tax_deductible": bool(row[10]),
                "is_hidden": bool(row[11]),
                "is_matched": bool(row[12]),
                "is_internal_transfer": bool(row[13])
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(transaction_id: int):
    """Get a specific transaction"""
    try:
        transaction = transaction_model.get_transaction_by_id(transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return transaction
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/transactions/{transaction_id}/category")
async def update_transaction_category(transaction_id: int, category_id: str):
    """Update transaction category - uses existing model logic"""
    try:
        success = transaction_model.update_transaction_category(transaction_id, category_id)
        if not success:
            raise HTTPException(status_code=404, detail="Transaction not found or update failed")
        return {"message": "Category updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/transactions/{transaction_id}/hide")
async def toggle_transaction_visibility(transaction_id: int):
    """Toggle transaction visibility (hide/show)"""
    try:
        # First get the current transaction to determine current visibility
        cursor = db_manager.execute("SELECT is_hidden FROM transactions WHERE id = ?", (transaction_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        current_hidden = bool(row[0])
        new_hidden = not current_hidden  # Toggle the value
        
        success = transaction_model.update_transaction_visibility(transaction_id, new_hidden)
        if not success:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return {"message": "Transaction visibility updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/transactions/{transaction_id}/internal_transfer")
async def toggle_transaction_internal_transfer(transaction_id: int):
    """Toggle transaction internal transfer status"""
    try:
        cursor = db_manager.execute("SELECT is_internal_transfer FROM transactions WHERE id = ?", (transaction_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        current_internal = bool(row[0])
        new_internal = not current_internal  # Toggle the value
        
        success = transaction_model.update_transaction_internal_transfer(transaction_id, new_internal)
        if not success:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return {"message": "Transaction internal transfer status updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/transactions/{transaction_id}")
async def delete_transaction(transaction_id: int):
    """Delete transaction"""
    try:
        success = transaction_model.delete_transaction(transaction_id)
        if not success:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return {"message": "Transaction deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Category endpoints
@app.get("/api/categories", response_model=List[CategoryResponse])
async def get_categories():
    """Get all categories - mirrors existing tree view"""
    try:
        categories = category_model.get_categories()
        # Convert Category objects to dictionaries for API response
        result = []
        for c in categories:
            result.append({
                "id": c.id,
                "name": c.name,
                "parent_id": c.parent_id,
                "category_type": c.category_type.value if hasattr(c.category_type, 'value') else str(c.category_type),
                "tax_type": c.tax_type,
                "is_bank_account": getattr(c, 'is_bank_account', False)
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/categories")
async def create_category(name: str, parent_id: Optional[str] = None, category_type: str = "transaction", tax_type: Optional[str] = None):
    """Create new category - uses existing model logic"""
    try:
        category_id = category_model.add_category(name, parent_id, category_type, tax_type, False)
        return {"id": category_id, "message": "Category created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Bank Account endpoints
@app.get("/api/accounts", response_model=List[BankAccountResponse])
async def get_bank_accounts():
    """Get all bank accounts"""
    try:
        accounts = bank_account_model.get_accounts()
        # Convert to dict format for API response
        result = []
        for a in accounts:
            result.append({
                "id": a.id,
                "name": a.name,
                "account_number": getattr(a, 'account_number', ''),
                "bsb": getattr(a, 'bsb', ''),
                "bank_name": getattr(a, 'bank_name', ''),
                "current_balance": float(getattr(a, 'current_balance', 0)),
                "last_import_date": getattr(a, 'last_import_date', None),
                "notes": getattr(a, 'notes', '')
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/accounts")
async def create_bank_account(
    name: str,
    account_number: Optional[str] = None,
    bsb: Optional[str] = None,
    bank_name: Optional[str] = None,
    notes: Optional[str] = None
):
    """Create new bank account"""
    try:
        account_id = bank_account_model.create_account(name, account_number, bsb, bank_name, notes)
        return {"id": account_id, "message": "Bank account created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Universal Import endpoint (supports QIF and CSV)
@app.post("/api/import")
async def import_file(file: UploadFile = File(...), account_id: str = None):
    """Import financial file - supports QIF and CSV formats"""
    try:
        if not account_id:
            raise HTTPException(status_code=400, detail="Account ID is required")
        
        # Check file extension to determine format
        filename = file.filename.lower()
        if not (filename.endswith('.qif') or filename.endswith('.csv')):
            raise HTTPException(status_code=400, detail="File must be a QIF or CSV file")
        
        # Read file content and save to temporary file
        content = await file.read()
        
        # Determine file suffix and create temporary file
        suffix = '.qif' if filename.endswith('.qif') else '.csv'
        
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False, encoding='utf-8') as temp_file:
            temp_file.write(content.decode('utf-8'))
            temp_file_path = temp_file.name
        
        try:
            if filename.endswith('.qif'):
                # Use QIF parser
                parser = QIFParser()
                transactions = parser.parse_file(temp_file_path)
                imported_count, duplicate_count = transaction_model.import_qif_transactions(transactions, account_id)
                
                return {
                    "message": f"Successfully imported {imported_count} transactions from QIF file",
                    "imported_count": imported_count,
                    "duplicate_count": duplicate_count,
                    "format": "QIF"
                }
            else:
                # Use CSV parser
                parser = CSVParser()
                transactions = parser.parse_file(temp_file_path)
                imported_count, duplicate_count = transaction_model.import_csv_transactions(transactions, account_id)
                
                # Get updated balance info
                latest_balance = parser.get_latest_balance()
                balance_warnings = parser.validate_balance_progression()
                
                response_data = {
                    "message": f"Successfully imported {imported_count} transactions from CSV file",
                    "imported_count": imported_count,
                    "duplicate_count": duplicate_count,
                    "format": "CSV"
                }
                
                if latest_balance is not None:
                    response_data["updated_balance"] = float(latest_balance)
                
                if balance_warnings:
                    response_data["balance_warnings"] = balance_warnings
                
                return response_data
                
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Transaction Preview endpoint
@app.post("/api/import/preview")
async def preview_import_file(file: UploadFile = File(...)):
    """Preview transactions from QIF or CSV file without importing"""
    try:
        # Check file extension to determine format
        filename = file.filename.lower()
        if not (filename.endswith('.qif') or filename.endswith('.csv')):
            raise HTTPException(status_code=400, detail="File must be a QIF or CSV file")
        
        # Read file content and save to temporary file
        content = await file.read()
        
        # Determine file suffix and create temporary file
        suffix = '.qif' if filename.endswith('.qif') else '.csv'
        
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False, encoding='utf-8') as temp_file:
            temp_file.write(content.decode('utf-8'))
            temp_file_path = temp_file.name
        
        try:
            transactions_data = []
            format_type = ""
            metadata = {}
            
            if filename.endswith('.qif'):
                # Use QIF parser
                parser = QIFParser()
                transactions = parser.parse_file(temp_file_path)
                format_type = "QIF"
                
                for trans in transactions:
                    transactions_data.append({
                        "date": trans.date.strftime('%Y-%m-%d'),
                        "description": trans.payee + (f" - {trans.memo}" if trans.memo else ''),
                        "amount": float(trans.amount),
                        "withdrawal": float(abs(trans.amount)) if trans.amount < 0 else 0.0,
                        "deposit": float(trans.amount) if trans.amount > 0 else 0.0,
                        "balance": None,
                        "transaction_id": None,
                        "category": trans.category
                    })
            else:
                # Use CSV parser
                parser = CSVParser()
                transactions = parser.parse_file(temp_file_path)
                format_type = "CSV"
                
                # Get CSV-specific metadata
                metadata["latest_balance"] = float(parser.get_latest_balance()) if parser.get_latest_balance() else None
                metadata["balance_warnings"] = parser.validate_balance_progression()
                metadata["column_mapping"] = parser.column_mapping
                
                for trans in transactions:
                    transactions_data.append({
                        "date": trans.date.strftime('%Y-%m-%d'),
                        "description": trans.payee,
                        "amount": float(trans.amount),
                        "withdrawal": float(abs(trans.amount)) if trans.amount < 0 else 0.0,
                        "deposit": float(trans.amount) if trans.amount > 0 else 0.0,
                        "balance": float(trans.balance) if trans.balance else None,
                        "transaction_id": trans.transaction_id,
                        "category": trans.category
                    })
            
            return {
                "format": format_type,
                "transaction_count": len(transactions_data),
                "transactions": transactions_data,
                "metadata": metadata,
                "filename": file.filename
            }
                
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Legacy QIF Import endpoint (for backward compatibility)
@app.post("/api/import/qif")
async def import_qif_file(file: UploadFile = File(...), account_id: str = None):
    """Import QIF file - legacy endpoint, use /api/import instead"""
    return await import_file(file, account_id)

# Auto-categorisation endpoints
@app.post("/api/auto-categorize")
async def run_auto_categorisation():
    """Run auto-categorisation rules - uses existing logic"""
    try:
        # Use transaction model directly since we removed controller dependencies
        categorised_count = transaction_model.apply_auto_categorisation_rules()
        return {
            "message": f"Auto-categorised {categorised_count} transactions",
            "categorised_count": categorised_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Auto-categorisation rules management
class AutoCategoriseRuleResponse(BaseModel):
    id: int
    category_id: str
    category_name: Optional[str] = None
    amount_operator: Optional[str] = None
    amount_value: Optional[float] = None
    amount_value2: Optional[float] = None
    account_id: Optional[str] = None
    account_name: Optional[str] = None
    date_range: Optional[str] = None
    apply_future: bool = True
    descriptions: List[Dict[str, Any]] = []

@app.get("/api/auto-categorisation/rules", response_model=List[AutoCategoriseRuleResponse])
async def get_auto_categorisation_rules():
    """Get all auto-categorisation rules"""
    try:
        cursor = db_manager.cursor()
        
        # First check if tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('auto_categorisation_rules', 'auto_categorisation_rule_descriptions')
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        if 'auto_categorisation_rules' not in existing_tables:
            # Return empty list if tables don't exist yet
            return []
        
        # Get rules with category and account names
        cursor.execute("""
            SELECT 
                r.id,
                r.category_id,
                r.amount_operator,
                r.amount_value,
                r.amount_value2,
                r.account_id,
                r.date_range,
                r.apply_future,
                c.name as category_name,
                a.name as account_name
            FROM auto_categorisation_rules r
            LEFT JOIN categories c ON r.category_id = c.id
            LEFT JOIN bank_accounts a ON r.account_id = a.id
            ORDER BY r.id
        """)
        rules = cursor.fetchall()
        
        result = []
        for rule in rules:
            # Get descriptions for this rule (if table exists)
            descriptions = []
            if 'auto_categorisation_rule_descriptions' in existing_tables:
                cursor.execute("""
                    SELECT operator, description_text, case_sensitive, sequence
                    FROM auto_categorisation_rule_descriptions
                    WHERE rule_id = ?
                    ORDER BY sequence
                """, (rule[0],))  # rule[0] is the id
                descriptions = cursor.fetchall()
            
            result.append({
                "id": rule[0],
                "category_id": str(rule[1]) if rule[1] else "",
                "category_name": str(rule[8]) if rule[8] else None,
                "amount_operator": str(rule[2]) if rule[2] else None,
                "amount_value": float(rule[3]) if rule[3] is not None else None,
                "amount_value2": float(rule[4]) if rule[4] is not None else None,
                "account_id": str(rule[5]) if rule[5] else None,
                "account_name": str(rule[9]) if rule[9] else None,
                "date_range": str(rule[6]) if rule[6] else None,
                "apply_future": bool(rule[7]) if rule[7] is not None else True,
                "descriptions": [
                    {
                        "operator": str(desc[0]) if desc[0] else None,
                        "description_text": str(desc[1]) if desc[1] else "",
                        "case_sensitive": bool(desc[2]) if desc[2] is not None else False,
                        "sequence": int(desc[3]) if desc[3] is not None else 0
                    }
                    for desc in descriptions
                ]
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

class CreateRuleRequest(BaseModel):
    category_id: str
    descriptions: List[Dict[str, Any]]
    amount_operator: Optional[str] = None
    amount_value: Optional[float] = None
    amount_value2: Optional[float] = None
    account_id: Optional[str] = None
    date_range: Optional[str] = None
    apply_future: bool = True

@app.post("/api/auto-categorisation/rules")
async def create_auto_categorisation_rule(request: CreateRuleRequest):
    """Create a new auto-categorisation rule"""
    try:
        cursor = db_manager.cursor()
        
        # Insert the main rule
        cursor.execute("""
            INSERT INTO auto_categorisation_rules 
            (category_id, amount_operator, amount_value, amount_value2, account_id, date_range, apply_future)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (request.category_id, request.amount_operator, request.amount_value, request.amount_value2, request.account_id, request.date_range, request.apply_future))
        
        rule_id = cursor.lastrowid
        
        # Insert description conditions
        for i, desc in enumerate(request.descriptions):
            cursor.execute("""
                INSERT INTO auto_categorisation_rule_descriptions
                (rule_id, operator, description_text, case_sensitive, sequence)
                VALUES (?, ?, ?, ?, ?)
            """, (
                rule_id,
                desc.get("operator"),
                desc["description_text"],
                desc.get("case_sensitive", False),
                i
            ))
        
        db_manager.commit()
        return {"id": rule_id, "message": "Rule created successfully"}
    except Exception as e:
        db_manager.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/auto-categorisation/rules/{rule_id}")
async def update_auto_categorisation_rule(rule_id: int, request: CreateRuleRequest):
    """Update an auto-categorisation rule"""
    try:
        cursor = db_manager.cursor()
        
        # Update the main rule
        cursor.execute("""
            UPDATE auto_categorisation_rules 
            SET category_id = ?, amount_operator = ?, amount_value = ?, amount_value2 = ?,
                account_id = ?, date_range = ?, apply_future = ?
            WHERE id = ?
        """, (request.category_id, request.amount_operator, request.amount_value, request.amount_value2, request.account_id, request.date_range, request.apply_future, rule_id))
        
        # Delete existing descriptions
        cursor.execute("DELETE FROM auto_categorisation_rule_descriptions WHERE rule_id = ?", (rule_id,))
        
        # Insert new descriptions
        for i, desc in enumerate(request.descriptions):
            cursor.execute("""
                INSERT INTO auto_categorisation_rule_descriptions
                (rule_id, operator, description_text, case_sensitive, sequence)
                VALUES (?, ?, ?, ?, ?)
            """, (
                rule_id,
                desc.get("operator"),
                desc["description_text"],
                desc.get("case_sensitive", False),
                i
            ))
        
        db_manager.commit()
        return {"message": "Rule updated successfully"}
    except Exception as e:
        db_manager.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/auto-categorisation/rules/{rule_id}")
async def delete_auto_categorisation_rule(rule_id: int):
    """Delete an auto-categorisation rule"""
    try:
        cursor = db_manager.cursor()
        
        # Delete descriptions first (due to foreign key)
        cursor.execute("DELETE FROM auto_categorisation_rule_descriptions WHERE rule_id = ?", (rule_id,))
        
        # Delete the main rule
        cursor.execute("DELETE FROM auto_categorisation_rules WHERE id = ?", (rule_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        db_manager.commit()
        return {"message": "Rule deleted successfully"}
    except Exception as e:
        db_manager.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Analysis Views endpoints
@app.get("/api/analysis-views", response_model=List[AnalysisViewResponse])
async def get_analysis_views():
    """Get all saved analysis views"""
    try:
        cursor = db_manager.cursor()
        cursor.execute("""
            SELECT id, name, selected_categories, selected_period, custom_date_start, 
                   custom_date_end, aggregation, chart_type, show_income, show_expenses, 
                   show_cumulative, show_averages, created_at, updated_at
            FROM analysis_views 
            ORDER BY updated_at DESC
        """)
        
        views = []
        for row in cursor.fetchall():
            import json
            views.append({
                "id": row[0],
                "name": row[1],
                "selectedCategories": json.loads(row[2]) if row[2] else [],
                "selectedPeriod": row[3],
                "customDateRange": {"start": row[4] or "", "end": row[5] or ""},
                "aggregation": row[6],
                "chartType": row[7],
                "showIncome": bool(row[8]),
                "showExpenses": bool(row[9]),
                "showCumulative": bool(row[10]),
                "showAverages": bool(row[11]),
                "created_at": row[12],
                "updated_at": row[13]
            })
        
        return views
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analysis-views", response_model=AnalysisViewResponse)
async def create_analysis_view(view: AnalysisViewRequest):
    """Create a new analysis view"""
    try:
        import uuid
        import json
        from datetime import datetime
        
        view_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        cursor = db_manager.cursor()
        cursor.execute("""
            INSERT INTO analysis_views (
                id, name, selected_categories, selected_period, custom_date_start,
                custom_date_end, aggregation, chart_type, show_income, show_expenses,
                show_cumulative, show_averages, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            view_id, view.name, json.dumps(view.selectedCategories), view.selectedPeriod,
            view.customDateRange.get("start") or None, view.customDateRange.get("end") or None,
            view.aggregation, view.chartType, view.showIncome, view.showExpenses,
            view.showCumulative, view.showAverages, now, now
        ))
        
        db_manager.commit()
        
        return {
            "id": view_id,
            "name": view.name,
            "selectedCategories": view.selectedCategories,
            "selectedPeriod": view.selectedPeriod,
            "customDateRange": view.customDateRange,
            "aggregation": view.aggregation,
            "chartType": view.chartType,
            "showIncome": view.showIncome,
            "showExpenses": view.showExpenses,
            "showCumulative": view.showCumulative,
            "showAverages": view.showAverages,
            "created_at": now,
            "updated_at": now
        }
    except Exception as e:
        db_manager.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/analysis-views/{view_id}")
async def delete_analysis_view(view_id: str):
    """Delete an analysis view"""
    try:
        cursor = db_manager.cursor()
        cursor.execute("DELETE FROM analysis_views WHERE id = ?", (view_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="View not found")
        
        db_manager.commit()
        return {"message": "View deleted successfully"}
    except Exception as e:
        db_manager.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Statistics endpoint
@app.get("/api/statistics")
async def get_statistics():
    """Get transaction statistics for dashboard"""
    try:
        stats = transaction_model.get_transaction_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)