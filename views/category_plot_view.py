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

class CategoryPlotView(QWidget):
    """Widget for plotting category-based financial analysis"""
    
    def __init__(self, category_controller, transaction_controller):
        """
        Initialize the category plot view
        
        Args:
            category_controller: Controller for managing categories
            transaction_controller: Controller for managing transactions
        """
        super().__init__()
        self.category_controller = category_controller
        self.transaction_controller = transaction_controller
        self._setup_ui()
        self._setup_connections()

    @property
    def category_plot_component(self):
        """Get the JavaScript code for the React component"""
        return '''
        ({data, plotType, valueType, displayMode, showAverage, categories}) => {
            console.log('Component rendering with props:', {
                plotType, valueType, displayMode, showAverage,
                categoriesCount: categories.length,
                dataPoints: data.length
            });

            if (!window.Recharts) {
                console.error('Recharts library not loaded');
                return React.createElement('div', {
                    style: {
                        padding: '20px',
                        backgroundColor: '#ffebee',
                        border: '1px solid #ffcdd2',
                        borderRadius: '4px'
                    }
                }, 'Error: Chart library not loaded');
            }

            // Extract Recharts components
            const {
                BarChart, Bar, LineChart, Line, XAxis, YAxis, 
                CartesianGrid, Tooltip, Legend, ReferenceLine
            } = window.Recharts;

            console.log('Creating chart with type:', plotType);
            
            const width = 800;
            const height = 400;
            
            // Format tooltip values
            const formatValue = (value) => `$${Number(value).toFixed(2)}`;
            
            // Calculate average if needed
            const average = showAverage && plotType === 'column' ? 
                data.reduce((sum, item) => {
                    if (displayMode === 'independent') {
                        return sum + Object.values(item.values || {}).reduce((a, b) => a + b, 0);
                    }
                    return sum + (item.combinedValue || 0);
                }, 0) / data.length : null;

            console.log('Rendering chart with:', {
                width,
                height,
                dataLength: data.length,
                hasAverage: Boolean(average)
            });
            
            try {
                if (plotType === 'line') {
                    return React.createElement(LineChart, 
                        { width, height, data },
                        React.createElement(CartesianGrid, { strokeDasharray: "3 3" }),
                        React.createElement(XAxis, { dataKey: "date" }),
                        React.createElement(YAxis),
                        React.createElement(Tooltip, { formatter: formatValue }),
                        React.createElement(Legend),
                        displayMode === 'independent' 
                            ? categories.map((category, index) => 
                                React.createElement(Line, {
                                    key: category.id,
                                    type: "monotone",
                                    dataKey: `values.${category.id}`,
                                    name: category.name,
                                    stroke: `hsl(${(index * 137.5) % 360}, 70%, 50%)`,
                                    dot: false
                                })
                            )
                            : React.createElement(Line, {
                                type: "monotone",
                                dataKey: "combinedValue",
                                name: "Combined",
                                stroke: "#8884d8",
                                dot: false
                            })
                    );
                }
                
                return React.createElement(BarChart,
                    { width, height, data },
                    React.createElement(CartesianGrid, { strokeDasharray: "3 3" }),
                    React.createElement(XAxis, { dataKey: "date" }),
                    React.createElement(YAxis),
                    React.createElement(Tooltip, { formatter: formatValue }),
                    React.createElement(Legend),
                    displayMode === 'independent'
                        ? categories.map((category, index) =>
                            React.createElement(Bar, {
                                key: category.id,
                                dataKey: `values.${category.id}`,
                                name: category.name,
                                fill: `hsl(${(index * 137.5) % 360}, 70%, 50%)`
                            })
                        )
                        : React.createElement(Bar, {
                            dataKey: "combinedValue",
                            name: "Combined",
                            fill: "#8884d8"
                        }),
                    showAverage && React.createElement(ReferenceLine, {
                        y: average,
                        stroke: "#666",
                        strokeDasharray: "3 3",
                        label: "Average"
                    })
                );
            } catch (error) {
                console.error('Error rendering chart:', error);
                return React.createElement('div', {
                    style: {
                        padding: '20px',
                        backgroundColor: '#ffebee',
                        border: '1px solid #ffcdd2',
                        borderRadius: '4px'
                    }
                }, `Error rendering chart: ${error.message}`);
            }
        }
        '''

    def _setup_ui(self):
        """Initialize the user interface components"""
        main_layout = QHBoxLayout(self)
        
        # Left panel for controls (same as before)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Category selection tree
        self.category_tree = QTreeView()
        self.tree_model = CategoryTreeModel(self.category_controller)
        self.category_tree.setModel(self.tree_model)
        self.category_tree.setSelectionMode(QTreeView.ExtendedSelection)
        left_layout.addWidget(QLabel("Select Categories:"))
        left_layout.addWidget(self.category_tree)
        
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
        
        main_layout.addWidget(right_panel, stretch=2)
        
        # Update average line visibility based on plot type
        self._update_average_visibility()

    def _setup_connections(self):
        """Set up signal/slot connections for UI interactions"""
        # Connect all controls to trigger plot updates
        self.category_tree.selectionModel().selectionChanged.connect(
            self._update_plot)
        self.group_combo.currentTextChanged.connect(self._update_plot)
        self.plot_type_group.buttonClicked.connect(self._handle_plot_type_change)
        self.value_type_group.buttonClicked.connect(self._update_plot)
        self.display_mode_group.buttonClicked.connect(self._update_plot)
        self.average_group.buttonClicked.connect(self._update_plot)
        self.start_date.dateChanged.connect(self._update_plot)
        self.end_date.dateChanged.connect(self._update_plot)

    def _process_data(self):
        """Process transaction data for plotting"""
        selected_categories = self._get_selected_categories()
        if not selected_categories:
            return None, []

        start_date = self.start_date.date().toPython()
        end_date = self.end_date.date().toPython()
        
        # Get all transactions for selected categories
        transactions = []
        for category in selected_categories:
            category_transactions = self.transaction_controller.get_transactions()
            # Filter by category and date range
            filtered_transactions = [
                t for t in category_transactions 
                if t.category_id == category.id 
                and start_date <= t.date.date() <= end_date
            ]
            transactions.extend(filtered_transactions)
        
        if not transactions:
            return None, []

        # Convert to DataFrame for easier processing
        df = pd.DataFrame([
            {
                'date': t.date,
                'category_id': t.category_id,
                'deposit': float(t.deposit),
                'withdrawal': float(t.withdrawal),
                'net': float(t.deposit - t.withdrawal)
            }
            for t in transactions
        ])

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

        # Determine value type
        if self.deposits_radio.isChecked():
            value_col = 'deposit'
        elif self.withdrawals_radio.isChecked():
            value_col = 'withdrawal'
        else:
            value_col = 'net'

        # Group data
        if self.independent_radio.isChecked():
            grouped = df.groupby(['period', 'category_id'])[value_col].sum().reset_index()
            # Pivot to get categories as columns
            plot_data = grouped.pivot(
                index='period', 
                columns='category_id', 
                values=value_col
            ).fillna(0)
        else:
            grouped = df.groupby('period')[value_col].sum().reset_index()
            plot_data = grouped.set_index('period')

        # Handle cumulative sum for line plots
        if self.line_radio.isChecked():
            plot_data = plot_data.cumsum()

        # Convert to list of dicts for React
        result_data = []
        for period in plot_data.index:
            row_data = {'date': str(period)}
            if self.independent_radio.isChecked():
                row_data['values'] = {
                    cat.id: float(plot_data.loc[period, cat.id])
                    for cat in selected_categories
                }
            else:
                row_data['combinedValue'] = float(plot_data.loc[period, value_col])
            result_data.append(row_data)

        return result_data, selected_categories

    def _update_plot(self):
        """Update the plot with current data and settings"""
        data, categories = self._process_data()
        if not data:
            # Clear the plot if no data
            self.plot_widget.setHtml("<div>No data to display</div>")
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

        # Create HTML with the React component
        html_content = f"""
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="UTF-8">
                <script crossorigin src="https://unpkg.com/react@17/umd/react.development.js"></script>
                <script crossorigin src="https://unpkg.com/react-dom@17/umd/react-dom.development.js"></script>
                <script crossorigin src="https://unpkg.com/prop-types@15.7.2/prop-types.js"></script>
                <script crossorigin src="https://unpkg.com/recharts@2.1.12/umd/Recharts.js"></script>
                <style>
                    body {{
                        margin: 0;
                        padding: 0;
                        overflow: hidden;
                    }}
                    #root {{ 
                        width: 100vw;
                        height: 100vh;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        background-color: white;
                    }}
                    .chart-container {{
                        padding: 20px;
                        border-radius: 8px;
                    }}
                </style>
            </head>
            <body>
                <div id="root">
                    <div class="chart-container">
                        Loading chart...
                    </div>
                </div>
                <script>
                    function initChart() {{
                        if (!window.React || !window.ReactDOM || !window.Recharts) {{
                            console.log('Waiting for libraries...', {{
                                React: !!window.React,
                                ReactDOM: !!window.ReactDOM,
                                Recharts: !!window.Recharts
                            }});
                            setTimeout(initChart, 100);
                            return;
                        }}

                        try {{
                            console.log('Libraries loaded, initializing chart...');
                            const plotConfig = {json.dumps(plot_config)};
                            const CategoryPlot = {self.category_plot_component};
                            
                            ReactDOM.render(
                                React.createElement(CategoryPlot, plotConfig),
                                document.getElementById('root')
                            );
                            console.log('Chart rendered successfully');
                        }} catch (error) {{
                            console.error('Error rendering chart:', error);
                            document.getElementById('root').innerHTML = `
                                <div style="color: red; padding: 20px;">
                                    Error rendering chart: ${{error.message}}
                                </div>
                            `;
                        }}
                    }}

                    window.onload = initChart;
                </script>
            </body>
        </html>
        """
        
        self.plot_widget.setHtml(html_content)
        
        # Debug output
        print("Updated plot with data:", json.dumps(plot_config, indent=2))

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

    def _get_selected_categories(self):
        """
        Get the currently selected categories from the tree view
        
        Returns:
            list: List of selected Category objects that are transaction categories
        """
        selected_indexes = self.category_tree.selectionModel().selectedIndexes()
        categories = []
        
        for index in selected_indexes:
            if index.column() == 0:  # Only process first column to avoid duplicates
                item = index.internalPointer()['item']
                # Only include transaction categories (leaf nodes)
                if item.category_type.value == 'transaction':
                    categories.append(item)
        
        return categories
    
class CategoryPlotDialog(QDialog):
    """Dialog for displaying the category plot"""
    
    def __init__(self, category_controller, transaction_controller, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Category Analysis Plot")
        self.resize(1200, 800)
        
        # Create the plot view
        self.plot_view = CategoryPlotView(
            category_controller,
            transaction_controller
        )
        
        # Set up dialog layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.plot_view)
        
        # Set dialog properties
        self.setModal(True)
        
    def closeEvent(self, event):
        """Handle dialog close event"""
        # Clean up the web view
        if hasattr(self.plot_view, 'plot_widget'):
            self.plot_view.plot_widget.setHtml("")
            self.plot_view.plot_widget.deleteLater()
        super().closeEvent(event)