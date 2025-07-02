# BNB Financial Manager - Application Context & Architecture

## Project Overview
BNB Financial Manager is a comprehensive personal finance application designed for Australian users. It evolved from a Python desktop application to a modern web-based solution while preserving all existing data and business logic.

## Current Architecture (Post-Migration)

### System Structure
```
BNB-Financial-Manager/
├── api/                              # FastAPI Backend
│   ├── main.py                       # REST API with comprehensive endpoints
│   └── requirements.txt              # Backend dependencies
├── frontend/                         # React Frontend
│   ├── src/components/
│   │   ├── AnalysisView.tsx          # Advanced financial analysis with charts
│   │   ├── TransactionViewStandalone.tsx  # Transaction management
│   │   ├── CategoryView.tsx          # Hierarchical category management
│   │   ├── AccountView.tsx           # Bank account overview
│   │   ├── AutoCategorizeRulesView.tsx  # Rule management
│   │   ├── MainLayout.tsx            # Navigation and routing
│   │   └── dialogs/                  # Modal components
│   └── package.json                  # Frontend dependencies (React, TypeScript, Tailwind)
├── models/                           # Core Business Logic (Unchanged)
│   ├── database_manager.py           # SQLite connection and schema management
│   ├── transaction_model.py          # Transaction CRUD and business rules
│   ├── category_model.py             # Hierarchical category management
│   ├── bank_account_model.py         # Account management and reconciliation
│   └── bank_account_reconciliation.py  # Balance matching logic
├── controllers/                      # Legacy Controllers (Partially Used)
├── utils/                           # Utilities (QIF parsing, etc.)
└── finance.db                       # SQLite Database (Unchanged Schema)
```

### Technology Stack

#### Backend - FastAPI
- **Purpose**: Thin API layer exposing existing Python business logic
- **Database**: Direct integration with existing SQLite schema
- **Authentication**: None (single-user desktop application)
- **CORS**: Enabled for React frontend communication

#### Frontend - React/TypeScript
- **Framework**: React 18 with TypeScript for type safety
- **Styling**: Tailwind CSS for modern, responsive design
- **Charts**: Recharts library for interactive financial visualizations
- **HTTP**: Axios for API communication
- **Icons**: Lucide React for consistent iconography

## Core Data Concepts

### Transaction Categories
The application uses a **hierarchical category system** similar to a Financial Breakdown Structure (FBS):

#### Structure Types:
1. **Root Categories**: Top-level groupings (e.g., "Expenses", "Income", "Business")
2. **Group Categories**: Mid-level classifications (e.g., "Food & Dining", "Utilities")
3. **Transaction Categories**: Leaf nodes where actual transactions are categorized (e.g., "Groceries", "Coffee Shops")

#### Category Properties:
- **Hierarchical Path**: Categories have parent-child relationships (e.g., "Business/Equipment/Computer Hardware")
- **Tax Types**: Australian tax classification (GST, FRE - Fringe Benefits, NT - No Tax)
- **Category Types**: Different types for different purposes (transaction, bank account, etc.)
- **Selection Logic**: Selecting a parent category includes all child transactions

### Transaction Management
Transactions have multiple classification states:

#### Transaction Types:
1. **Regular Transactions**: Standard income/expense entries
2. **Internal Transfers**: Money movement between user's own accounts
3. **Hidden Transactions**: Transactions excluded from analysis (errors, duplicates)
4. **Uncategorized**: Transactions without assigned categories

#### Transaction Properties:
- **Dual Amount System**: Separate deposit/withdrawal fields (not negative amounts)
- **Account Association**: Each transaction belongs to a specific bank account
- **Category Assignment**: Can be manually assigned or auto-categorized via rules
- **Tax Classification**: Inherits from assigned category
- **Matching Status**: For reconciliation with bank statements

### Auto-Categorization Rules
Sophisticated rule engine for automatic transaction categorization:

#### Rule Components:
1. **Description Patterns**: Text matching with operators (contains, starts with, regex)
2. **Amount Conditions**: Range-based or exact amount matching
3. **Account Filters**: Rules specific to certain bank accounts
4. **Date Ranges**: Time-based rule application
5. **Future Application**: Whether rules apply to new transactions

#### Rule Logic:
- **Sequence-Based**: Multiple description conditions evaluated in order
- **Operator Support**: AND/OR logic between conditions
- **Case Sensitivity**: Configurable text matching
- **Priority System**: Rules processed in creation order

## Enhanced Analysis Features (Recently Implemented)

### Advanced Chart Interface
The AnalysisView component now provides comprehensive financial analysis:

#### Date & Time Controls:
- **Period Presets**: Week, Month, Quarter, Year options
- **Custom Date Ranges**: User-defined start/end dates with date pickers
- **Dynamic Aggregation**: Daily, Weekly, Monthly, Quarterly grouping
- **Timeline Brush**: Interactive zoom/pan for large datasets

#### Visualization Options:
- **Chart Types**: Grouped bars, stacked bars, line charts
- **Display Controls**: Toggle income/expenses/both independently
- **Cumulative Views**: Running totals over time
- **Reference Lines**: Average indicators for trend analysis
- **Category Breakdown**: Stacked charts showing individual expense categories

#### Category Filtering:
- **Hierarchical Tree View**: Expandable category selection
- **Smart Selection**: Parent categories automatically include children
- **Visual Indicators**: Selected categories highlighted with status dots
- **Collapsible Panel**: Space-efficient filtering interface

#### View Management:
- **Saved Views**: Store complete filter/display configurations
- **Quick Access**: Saved views available as buttons
- **View Persistence**: Named configurations for different analysis scenarios
- **CRUD Operations**: Create, load, and delete custom views

### Chart Data Processing:
- **Real-time Filtering**: Charts update immediately when filters change
- **Category Aggregation**: Groups transactions by selected categories
- **Date Range Processing**: Efficient filtering for any time period
- **Multi-level Analysis**: Can analyze individual categories or grouped data

## API Architecture

### RESTful Endpoints:
```
Transaction Management:
GET    /api/transactions              # Filtered transaction listing
PUT    /api/transactions/{id}/category # Update category assignment
PUT    /api/transactions/{id}/hide     # Toggle visibility
DELETE /api/transactions/{id}          # Delete transaction

Category Management:
GET    /api/categories                 # Hierarchical category tree
POST   /api/categories                 # Create new category

Account Management:
GET    /api/accounts                   # Bank account listing
POST   /api/accounts                   # Create new account

Auto-Categorization:
GET    /api/auto-categorisation/rules  # List all rules
POST   /api/auto-categorisation/rules  # Create new rule
PUT    /api/auto-categorisation/rules/{id}  # Update rule
DELETE /api/auto-categorisation/rules/{id}  # Delete rule
POST   /api/auto-categorize            # Execute all rules

Data Import:
POST   /api/import/qif                 # QIF file upload and processing

Statistics:
GET    /api/statistics                 # Dashboard metrics
```

### Data Flow:
1. **React Frontend** → HTTP requests → **FastAPI Backend**
2. **FastAPI** → Direct calls → **Python Models**
3. **Models** → SQLite queries → **Database**
4. **Response** ← JSON serialization ← **API** ← **Models**

## User Interface Philosophy

### Design Principles:
1. **Australian-Focused**: BSB/account numbers, AUD currency, Australian tax types
2. **Professional Appearance**: Clean, modern interface suitable for financial data
3. **Data Density**: Efficient use of screen space for large datasets
4. **Responsive Design**: Works across desktop, tablet, and mobile
5. **Keyboard Accessibility**: Full keyboard navigation support

### Navigation Structure:
- **Sidebar Navigation**: Quick access to all major functions
- **Tab-based Views**: Logical organization within sections
- **Modal Dialogs**: Non-disruptive workflows for secondary actions
- **Contextual Actions**: Relevant operations available where needed

## Data Integrity & Business Rules

### Transaction Rules:
- **No Negative Amounts**: Uses separate deposit/withdrawal fields
- **Internal Transfer Detection**: Automatic matching of transfers between accounts
- **Duplicate Prevention**: QIF import includes duplicate detection
- **Balance Calculation**: Real-time account balance updates

### Category Rules:
- **Hierarchical Integrity**: Parent-child relationships maintained
- **Tax Inheritance**: Child categories inherit parent tax settings
- **Deletion Protection**: Cannot delete categories with assigned transactions
- **Unique Naming**: Category names unique within same parent level

### Security & Data Protection:
- **Local Database**: All data stored locally in SQLite
- **No Cloud Dependency**: Fully offline-capable application
- **Data Export**: QIF export capability for data portability
- **Backup Support**: Database file can be copied for backup

## Current Development Status

### Completed Features ✅:
- Full React frontend with TypeScript
- Comprehensive API layer
- Advanced chart interface with filtering
- Category tree management with selection
- View management system
- Auto-categorization rule engine
- QIF import/export functionality
- Responsive design implementation

### Operational Status:
- **Database**: Fully compatible with existing schema
- **Business Logic**: 100% preserved from original application
- **Data Migration**: None required - uses existing data
- **Feature Parity**: Exceeds original functionality with enhanced analysis

### Access Points:
- **Frontend Development**: `npm run dev` in /frontend
- **Backend API**: `python api/main.py` from root directory
- **API Documentation**: http://localhost:8000/docs (automatic OpenAPI)
- **Database**: Direct SQLite access via existing tools

## Future Enhancement Opportunities

### Potential Additions:
1. **Budget Management**: Budget creation and tracking against categories
2. **Reporting**: PDF report generation for specific periods
3. **Data Sync**: Optional cloud synchronization for multi-device access
4. **Mobile App**: Native mobile applications using same API
5. **Advanced Analytics**: Forecasting and trend analysis
6. **Integration**: Bank API connections for automatic transaction import
7. **Multi-Currency**: Support for multiple currencies and exchange rates

### Architecture Benefits:
- **Scalable**: Web architecture supports multiple concurrent users
- **Extensible**: React components easily extended or replaced
- **Maintainable**: Clear separation between frontend and business logic
- **Testable**: API endpoints can be independently tested
- **Modern**: Up-to-date technology stack with active community support

This application successfully combines the reliability of the original financial logic with a modern, powerful user interface that enhances the user experience while maintaining complete data compatibility.