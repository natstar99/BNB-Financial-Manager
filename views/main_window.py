# File: views/main_window.py

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QMenuBar, QMenu, 
    QToolBar, QStatusBar, QFileDialog, QMessageBox, QDialog, QTabWidget, QVBoxLayout
)
from PySide6.QtGui import QIcon, QKeySequence, QAction
from PySide6.QtCore import Qt, Slot
from .category_view import CategoryView
from .transaction_view import TransactionView
from utils.qif_parser import QIFParser
from views.duplicate_manager import DuplicateManagerDialog
from views.multi_import_dialog import MultiFileImportDialog
from models.bank_account_model import BankAccountModel
from views.account_view import AccountView
from models.bank_account_reconciliation import BankAccountReconciliation
from views.category_plot_view import CategoryPlotView

class MainWindow(QMainWindow):
    """Main application window that contains all views"""
    def __init__(self, category_controller, transaction_controller, 
                 bank_account_model: BankAccountModel,
                 bank_reconciliation: BankAccountReconciliation):
        """
        Initialise the main window with controllers and models
        
        Args:
            category_controller: Controller for managing categories
            transaction_controller: Controller for managing transactions
            bank_account_model: Model for managing bank accounts
            bank_reconciliation: Model for reconciling the values in the bank accounts
        """
        super().__init__()
        self.category_controller = category_controller
        self.transaction_controller = transaction_controller
        self.bank_account_model = bank_account_model
        self.bank_reconciliation = bank_reconciliation
        
        self.setWindowTitle("Bear No Broked - Financial Manager")
        self._create_menu_bar()
        self._create_tool_bar()
        self._create_status_bar()
        self._setup_main_layout()
        
        # Set window properties
        self.setMinimumSize(1200, 800)
        self.setWindowState(Qt.WindowMaximized)  # Start maximised
    
    def _create_menu_bar(self):
        """Create the application menu bar"""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("&File")
        
        # Import action
        import_action = QAction("&Import QIF...", self)
        import_action.setShortcut(QKeySequence.Open)
        import_action.setStatusTip("Import transactions from QIF file")
        import_action.triggered.connect(self._import_qif)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        # Export action
        export_action = QAction("&Export...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.setStatusTip("Export transactions to file")
        export_action.triggered.connect(self._export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View Menu
        view_menu = menubar.addMenu("&View")
        
        # Toggle transaction view
        self.toggle_trans_action = QAction("&Transactions", self)
        self.toggle_trans_action.setCheckable(True)
        self.toggle_trans_action.setChecked(True)
        self.toggle_trans_action.triggered.connect(
            lambda checked: self._toggle_view('transactions', checked))
        view_menu.addAction(self.toggle_trans_action)
        
        # Toggle category view
        self.toggle_cat_action = QAction("&Categories", self)
        self.toggle_cat_action.setCheckable(True)
        self.toggle_cat_action.setChecked(True)
        self.toggle_cat_action.triggered.connect(
            lambda checked: self._toggle_view('categories', checked))
        view_menu.addAction(self.toggle_cat_action)
        
        # Toggle analysis view
        self.toggle_analysis_action = QAction("&Analysis", self)
        self.toggle_analysis_action.setCheckable(True)
        self.toggle_analysis_action.setChecked(False)  # Initially hidden
        self.toggle_analysis_action.triggered.connect(
            lambda checked: self._toggle_view('analysis', checked))
        view_menu.addAction(self.toggle_analysis_action)
        
        # Tools Menu
        tools_menu = menubar.addMenu("&Tools")
        
        # Reconcile action
        reconcile_action = QAction("&Reconcile Accounts...", self)
        reconcile_action.setStatusTip("Match and reconcile transactions")
        reconcile_action.triggered.connect(self._reconcile_accounts)
        tools_menu.addAction(reconcile_action)
        
        # Help Menu
        help_menu = menubar.addMenu("&Help")
        
        # About action
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _toggle_view(self, view_type: str, visible: bool):
        """
        Toggle the visibility of a specific view
        
        Args:
            view_type: Type of view to toggle ('transactions', 'categories', 'analysis')
            visible: Whether the view should be visible
        """
        if view_type == 'transactions':
            self.transaction_view.setVisible(visible)
            # Ensure at least one view is visible
            if not visible and not (self.category_view.isVisible() or self.analysis_view.isVisible()):
                self.toggle_cat_action.setChecked(True)
                self.category_view.setVisible(True)
        
        elif view_type == 'categories':
            self.category_view.setVisible(visible)
            # Ensure at least one view is visible
            if not visible and not (self.transaction_view.isVisible() or self.analysis_view.isVisible()):
                self.toggle_trans_action.setChecked(True)
                self.transaction_view.setVisible(True)
        
        elif view_type == 'analysis':
            self.analysis_view.setVisible(visible)
            # Ensure at least one view is visible
            if not visible and not (self.transaction_view.isVisible() or self.category_view.isVisible()):
                self.toggle_trans_action.setChecked(True)
                self.transaction_view.setVisible(True)
        
        # Adjust layout stretches based on visible widgets
        self._adjust_layout_stretches()

    def _adjust_layout_stretches(self):
        """Adjust layout stretches based on visible widgets"""
        visible_count = sum([
            self.transaction_view.isVisible(),
            self.category_view.isVisible(),
            self.analysis_view.isVisible()
        ])
        
        if visible_count == 0:
            return  # Should never happen due to _toggle_view logic
        
        # Set stretches based on visible widgets
        self.main_layout.setStretch(self.main_layout.indexOf(self.transaction_view),
                                2 if self.transaction_view.isVisible() else 0)
        self.main_layout.setStretch(self.main_layout.indexOf(self.category_view),
                                1 if self.category_view.isVisible() else 0)
        self.main_layout.setStretch(self.main_layout.indexOf(self.analysis_view),
                                1 if self.analysis_view.isVisible() else 0)
    
    def _create_tool_bar(self):
        """Create the main toolbar"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # Add import button
        import_action = QAction("Import", self)
        import_action.setStatusTip("Import transactions from QIF file")
        import_action.triggered.connect(self._import_qif)
        toolbar.addAction(import_action)
        
        toolbar.addSeparator()
        
        # Add reconcile button
        reconcile_action = QAction("Reconcile", self)
        reconcile_action.setStatusTip("Match and reconcile transactions")
        reconcile_action.triggered.connect(self._reconcile_accounts)
        toolbar.addAction(reconcile_action)
    
    def _create_status_bar(self):
        """Create the status bar"""
        status = QStatusBar()
        self.setStatusBar(status)
        status.showMessage("Ready")
    
    def _setup_main_layout(self):
        """Set up the main widget layout"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Create main layout
        self.main_layout = QHBoxLayout(main_widget)
        
        # Create and add the transaction view
        self.transaction_view = TransactionView(
            self.transaction_controller, 
            self.category_controller,
            self.bank_account_model
        )
        self.main_layout.addWidget(self.transaction_view, stretch=2)
        
        # Create category view
        self.category_view = CategoryView(
            self.category_controller,
            self.transaction_controller
        )
        self.main_layout.addWidget(self.category_view, stretch=1)
        
        # Create analysis view (initially hidden)
        self.analysis_view = CategoryPlotView(
            self.category_controller,
            self.transaction_controller,
            category_view=self.category_view
        )
        self.main_layout.addWidget(self.analysis_view, stretch=1)
        self.analysis_view.hide()
    
    @Slot()
    def _import_qif(self):
        """Handle QIF file import"""
        # Show multi-file import dialog
        dialog = MultiFileImportDialog(self.bank_account_model, self)
        
        if dialog.exec_() == QDialog.Accepted:
            import_files = dialog.get_import_files()
            
            if import_files:
                try:
                    self.statusBar().showMessage("Importing files...")
                    
                    # Import files
                    results = self.transaction_controller.import_qif_files(
                        import_files)
                    
                    # Process results
                    total_imported = 0
                    total_duplicates = 0
                    failed_files = []
                    
                    for file_name, result in results.items():
                        if result['success']:
                            total_imported += result['imported_count']
                            total_duplicates += result['duplicate_count']
                        else:
                            failed_files.append(file_name)
                    
                    # Show results message
                    message = (
                        f"Import completed: {total_imported} transactions imported, "
                        f"{total_duplicates} duplicates skipped"
                    )
                    
                    if failed_files:
                        message += f"\n\nFailed to import: {', '.join(failed_files)}"
                    
                    self.statusBar().showMessage(message, 5000)
                    
                    QMessageBox.information(
                        self,
                        "Import Complete",
                        message
                    )
                    
                    # Refresh transaction view
                    self.transaction_view.table_model.refresh_data()
                    
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Import Error",
                        f"Error importing files: {str(e)}"
                    )
                    self.statusBar().showMessage("Import failed", 5000)
    
    @Slot()
    def _export_data(self):
        """Handle data export"""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Export Data",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_name:
            try:
                # TODO: Implement export logic
                self.statusBar().showMessage(f"Exporting to {file_name}...")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Error",
                    f"Error exporting data: {str(e)}"
                )
    
    @Slot()
    def _reconcile_accounts(self):
        """Handle account reconciliation"""
        # TODO: Implement reconciliation dialog
        self.statusBar().showMessage("Reconciling accounts...")
    
    @Slot()
    def _show_about(self):
        """Show the about dialog"""
        QMessageBox.about(
            self,
            "About Financial Management",
            "Financial Management Application\n\n"
            "A tool for managing personal and business finances."
        )