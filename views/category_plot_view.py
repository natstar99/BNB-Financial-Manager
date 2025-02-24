# File: views/category_plot_view.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeView, 
    QRadioButton, QButtonGroup, QComboBox, 
    QDateEdit, QLabel, QDialog
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtWebEngineWidgets import QWebEngineView  # Add this import
import pandas as pd
from datetime import datetime, timedelta
from .category_view import CategoryTreeModel
import json
import numpy as np
from models.category_model import Category, CategoryType
from typing import List
from pathlib import Path


class CategoryPlotView(QWidget):
    """Widget for plotting category-based financial analysis"""
    
    def __init__(self, category_controller, transaction_controller, category_view=None):
        """
        Initialize the category plot view
        
        Args:
            category_controller: Controller for managing categories
            transaction_controller: Controller for managing transactions
            category_view: Optional CategoryView instance to use for selection
        """
        super().__init__()
        self.category_controller = category_controller
        self.transaction_controller = transaction_controller
        self.category_view = category_view
        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        """Initialize the user interface components"""
        main_layout = QHBoxLayout(self)
        
        # Left panel for controls (same as before)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Use the main category view if provided, otherwise show message
        if self.category_view:
            left_layout.addWidget(QLabel("Select categories in the Categories tab"))
        
        # Time grouping
        group_layout = QVBoxLayout()
        group_layout.addWidget(QLabel("Group By:"))
        self.group_combo = QComboBox()
        self.group_combo.addItems([
            "Days", "Weeks", "Months", "Quarters", 
            "Years", "Financial Years"
        ])
        group_layout.addWidget(self.group_combo)
        left_layout.addLayout(group_layout)
        
        # Plot type selection
        plot_type_layout = QVBoxLayout()
        plot_type_layout.addWidget(QLabel("Plot Type:"))
        self.plot_type_group = QButtonGroup()
        self.column_radio = QRadioButton("Column Chart")
        self.line_radio = QRadioButton("Cumulative Line")
        self.plot_type_group.addButton(self.column_radio)
        self.plot_type_group.addButton(self.line_radio)
        self.column_radio.setChecked(True)
        plot_type_layout.addWidget(self.column_radio)
        plot_type_layout.addWidget(self.line_radio)
        left_layout.addLayout(plot_type_layout)
        
        # Value type selection
        value_type_layout = QVBoxLayout()
        value_type_layout.addWidget(QLabel("Show Values:"))
        self.value_type_group = QButtonGroup()
        self.deposits_radio = QRadioButton("Deposits")
        self.withdrawals_radio = QRadioButton("Withdrawals")
        self.net_radio = QRadioButton("Net")
        self.value_type_group.addButton(self.deposits_radio)
        self.value_type_group.addButton(self.withdrawals_radio)
        self.value_type_group.addButton(self.net_radio)
        self.deposits_radio.setChecked(True)
        value_type_layout.addWidget(self.deposits_radio)
        value_type_layout.addWidget(self.withdrawals_radio)
        value_type_layout.addWidget(self.net_radio)
        left_layout.addLayout(value_type_layout)
        
        # Category display mode
        display_mode_layout = QVBoxLayout()
        display_mode_layout.addWidget(QLabel("Display Mode:"))
        self.display_mode_group = QButtonGroup()
        self.independent_radio = QRadioButton("Show Independently")
        self.combined_radio = QRadioButton("Show Combined")
        self.display_mode_group.addButton(self.independent_radio)
        self.display_mode_group.addButton(self.combined_radio)
        self.independent_radio.setChecked(True)
        display_mode_layout.addWidget(self.independent_radio)
        display_mode_layout.addWidget(self.combined_radio)
        left_layout.addLayout(display_mode_layout)
        
        # Average line option (only for column chart)
        self.average_layout = QVBoxLayout()
        self.average_layout.addWidget(QLabel("Show Average:"))
        self.average_group = QButtonGroup()
        self.show_average = QRadioButton("Show")
        self.hide_average = QRadioButton("Hide")
        self.average_group.addButton(self.show_average)
        self.average_group.addButton(self.hide_average)
        self.hide_average.setChecked(True)
        self.average_layout.addWidget(self.show_average)
        self.average_layout.addWidget(self.hide_average)
        left_layout.addLayout(self.average_layout)
        
        # Date range selection
        date_range_layout = QVBoxLayout()
        date_range_layout.addWidget(QLabel("Date Range:"))
        date_layout = QHBoxLayout()
        self.start_date = QDateEdit()
        self.end_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.end_date.setCalendarPopup(True)
        # Set default date range to last year
        self.end_date.setDate(QDate.currentDate())
        self.start_date.setDate(
            QDate.currentDate().addYears(-1)
        )
        date_layout.addWidget(QLabel("From:"))
        date_layout.addWidget(self.start_date)
        date_layout.addWidget(QLabel("To:"))
        date_layout.addWidget(self.end_date)
        date_range_layout.addLayout(date_layout)
        left_layout.addLayout(date_range_layout)
        
        # Add left panel to main layout
        main_layout.addWidget(left_panel, stretch=1)
        
        # Right panel for plot
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Create web view for React component
        self.plot_widget = QWebEngineView()
        self.plot_widget.setMinimumWidth(800)
        right_layout.addWidget(self.plot_widget)
        
        main_layout.addWidget(right_panel, stretch=3)
        
        # Update average line visibility based on plot type
        self._update_average_visibility()

    def _setup_connections(self):
        """Set up signal/slot connections for UI interactions"""
        # Connect all controls to trigger plot updates
        """Set up signal/slot connections"""
        if self.category_view:
            self.category_view.categories_selected.connect(self._handle_category_selection)
        self.group_combo.currentTextChanged.connect(self._update_plot)
        self.plot_type_group.buttonClicked.connect(self._handle_plot_type_change)
        self.value_type_group.buttonClicked.connect(self._update_plot)
        self.display_mode_group.buttonClicked.connect(self._update_plot)
        self.average_group.buttonClicked.connect(self._update_plot)
        self.start_date.dateChanged.connect(self._update_plot)
        self.end_date.dateChanged.connect(self._update_plot)

    def _process_data(self):
        """
        Process transaction data for plotting.
        Handles both regular and cumulative plotting modes.
        
        Returns:
            tuple: (processed_data, selected_categories) where:
                - processed_data is a list of dictionaries containing the plot data points
                - selected_categories is a list of Category objects being plotted
        """
        selected_categories = self._get_selected_categories()
        if not selected_categories:
            return None, []

        start_date = self.start_date.date().toPython()
        end_date = self.end_date.date().toPython()
        
        # Get all transactions for selected categories
        all_transactions = []
        for category in selected_categories:
            category_transactions = self.transaction_controller.get_transactions()
            # Filter by category and date range
            filtered_transactions = [
                {
                    'date': t.date,
                    'category_id': category.id,
                    'deposit': float(t.deposit),
                    'withdrawal': float(t.withdrawal),
                    'net': float(t.deposit - t.withdrawal)
                }
                for t in category_transactions 
                if t.category_id == category.id 
                and start_date <= t.date.date() <= end_date
            ]
            all_transactions.extend(filtered_transactions)
        
        if not all_transactions:
            return None, []

        # Convert to DataFrame for easier processing
        df = pd.DataFrame(all_transactions)
        
        # Group by time period
        grouping = self.group_combo.currentText()
        if grouping == "Days":
            df['period'] = df['date'].dt.date
        elif grouping == "Weeks":
            df['period'] = df['date'].dt.to_period('W').astype(str)
        elif grouping == "Months":
            df['period'] = df['date'].dt.to_period('M').astype(str)
        elif grouping == "Quarters":
            df['period'] = df['date'].dt.to_period('Q').astype(str)
        elif grouping == "Years":
            df['period'] = df['date'].dt.year
        else:  # Financial Years
            df['period'] = np.where(
                df['date'].dt.month >= 7,
                f"FY{df['date'].dt.year + 1}",
                f"FY{df['date'].dt.year}"
            )

        # Sort by period to ensure correct cumulative calculations
        df = df.sort_values('period')

        # Determine value type and adjust sign for expenses
        if self.deposits_radio.isChecked():
            value_col = 'deposit'
        elif self.withdrawals_radio.isChecked():
            value_col = 'withdrawal'
            df[value_col] = -df[value_col]  # Make withdrawals negative
        else:
            value_col = 'net'

        # Process data based on display mode
        if self.independent_radio.isChecked():
            # Group by period and category
            grouped = df.groupby(['period', 'category_id'])[value_col].sum().reset_index()
            
            # Create periods for all category combinations
            periods = sorted(df['period'].unique())
            result_data = []
            
            if self.line_radio.isChecked():
                # For cumulative line plot, maintain running totals per category
                running_totals = {cat.id: 0.0 for cat in selected_categories}
                
                for period in periods:
                    data_point = {'date': str(period), 'values': {}}
                    period_data = grouped[grouped['period'] == period]
                    
                    for cat in selected_categories:
                        # Get value for this period
                        cat_value = period_data[period_data['category_id'] == cat.id][value_col].sum()
                        # Update running total
                        running_totals[cat.id] += cat_value
                        # Store cumulative value
                        data_point['values'][cat.id] = running_totals[cat.id]
                    
                    result_data.append(data_point)
            else:
                # Regular column chart - no cumulative totals
                for period in periods:
                    data_point = {'date': str(period), 'values': {}}
                    period_data = grouped[grouped['period'] == period]
                    
                    for cat in selected_categories:
                        cat_value = period_data[period_data['category_id'] == cat.id][value_col].sum()
                        data_point['values'][cat.id] = float(cat_value)
                    
                    result_data.append(data_point)
        else:
            # Combined view - sum all categories together
            grouped = df.groupby('period')[value_col].sum().reset_index()
            
            if self.line_radio.isChecked():
                # For cumulative line plot
                running_total = 0.0
                result_data = []
                
                for _, row in grouped.iterrows():
                    running_total += float(row[value_col])
                    result_data.append({
                        'date': str(row['period']),
                        'combinedValue': running_total
                    })
            else:
                # Regular column chart
                result_data = [
                    {
                        'date': str(period),
                        'combinedValue': float(value)
                    }
                    for period, value in zip(grouped['period'], grouped[value_col])
                ]

        return result_data, selected_categories

    @property
    def category_plot_component(self) -> str:
        """
        Load and return the React component code from the AnalysisPlot.js file.
        
        Returns:
            str: The React component code, or a basic error component if file not found
        """
        try:
            js_path = Path(__file__).parent / 'analysis_plot.js'
            with js_path.open('r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading AnalysisPlot.js: {e}")
            return '''
                () => React.createElement('div', {
                    style: {
                        padding: '20px',
                        backgroundColor: '#ffebee',
                        border: '1px solid #ffcdd2',
                        borderRadius: '4px'
                    }
                }, 'Error: Failed to load analysis plot component');
            '''

    def _load_html_template(self) -> str:
        """
        Load the HTML template for the analysis plot.
        
        Returns:
            str: The HTML template content, or a basic error template if file not found
        """
        try:
            template_path = Path(__file__).parent / 'analysis_plot_template.html'
            with template_path.open('r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading analysis plot template: {e}")
            return '<html><body>Error loading plot template</body></html>'

    def _update_plot(self):
        """Update the plot with current data and settings"""
        data, categories = self._process_data()
        if not data:
            # Show a message when there's no data
            html_content = """
                <html><body>
                    <div style="text-align: center; padding: 20px;">
                        No data to display. Please select categories and ensure transactions exist.
                    </div>
                </body></html>
            """
            self.plot_widget.setHtml(html_content)
            return

        # Prepare plot configuration
        plot_config = {
            'data': data,
            'plotType': 'line' if self.line_radio.isChecked() else 'column',
            'valueType': ('deposits' if self.deposits_radio.isChecked() else
                        'withdrawals' if self.withdrawals_radio.isChecked() else
                        'net'),
            'displayMode': 'independent' if self.independent_radio.isChecked() else 'combined',
            'showAverage': self.show_average.isChecked(),
            'categories': [
                {'id': cat.id, 'name': cat.name}
                for cat in categories
            ]
        }

        # Load template and component code
        template = self._load_html_template()
        component = self.category_plot_component

        # Create the complete HTML content
        html_content = template.replace(
            "{plot_config}",
            json.dumps(plot_config, default=str)
        ).replace(
            "{analysis_plot}",
            component
        )

        # Set the HTML content in the web view
        self.plot_widget.setHtml(html_content)

        # Debug output
        print("Updated plot with configuration:", json.dumps(plot_config, indent=2, default=str))

    def _update_average_visibility(self):
        """Update the visibility of average line options based on plot type"""
        # Show average options only for column charts
        show_average = self.column_radio.isChecked()
        
        # Update visibility of all widgets in the average layout
        for i in range(self.average_layout.count()):
            widget = self.average_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(show_average)
                
    def _handle_plot_type_change(self):
        """Handle changes to the plot type selection"""
        self._update_average_visibility()
        self._update_plot()

    def _handle_category_selection(self, selected_categories: List[Category]):
        """Handle changes in category selection from main category view"""
        self._process_data()  # Update the plot with new selection

    def _get_selected_categories(self) -> List[Category]:
        """Get the currently selected categories"""
        if self.category_view:
            return self.category_view._get_selected_transaction_categories()
        return []