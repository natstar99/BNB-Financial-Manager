import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart, Pie, Cell, ResponsiveContainer, LineChart, Line, Brush, ReferenceLine } from 'recharts';
import { DollarSign, TrendingUp, TrendingDown, Filter, BarChart3, LineChart as LineChartIcon, Target, ChevronDown, ChevronRight, Eye, EyeOff, Save, Trash2, Plus } from 'lucide-react';
import axios from 'axios';

interface ChartDataPoint {
  period: string;
  income: number;
  expenses: number;
  net: number;
  date: Date;
  cumulativeIncome?: number;
  cumulativeExpenses?: number;
  cumulativeNet?: number;
  avgIncome?: number;
  avgExpenses?: number;
  avgNet?: number;
  [key: string]: any; // For dynamic category data
}

interface Category {
  id: string;
  name: string;
  parent_id: string | null;
  category_type: string;
  is_bank_account: boolean;
  children?: Category[];
}

interface AnalysisView {
  id: string;
  name: string;
  selectedCategories: string[];
  selectedPeriod: string;
  customDateRange: { start: string; end: string };
  aggregation: 'day' | 'week' | 'month' | 'quarter';
  chartType: 'grouped' | 'stacked' | 'line';
  showIncome: boolean;
  showExpenses: boolean;
  showCumulative: boolean;
  showAverages: boolean;
}

const AnalysisView: React.FC = () => {
  const [selectedPeriod, setSelectedPeriod] = useState('month');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Data states
  const [categoryData, setCategoryData] = useState<any[]>([]);
  const [incomeCategoryData, setIncomeCategoryData] = useState<any[]>([]);
  const [expenseCategoriesData, setExpenseCategoriesData] = useState<any[]>([]);
  const [monthlyData, setMonthlyData] = useState<ChartDataPoint[]>([]);
  const [accountBalances, setAccountBalances] = useState<any[]>([]);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [categoryTree, setCategoryTree] = useState<Category[]>([]);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const [showCategoryPanel, setShowCategoryPanel] = useState(false);
  
  // View management
  const [savedViews, setSavedViews] = useState<AnalysisView[]>([]);
  const [currentViewName, setCurrentViewName] = useState('');
  const [showViewManager, setShowViewManager] = useState(false);
  
  // Filter states
  const [customDateRange, setCustomDateRange] = useState({ start: '', end: '' });
  const [aggregation, setAggregation] = useState<'day' | 'week' | 'month' | 'quarter'>('month');
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [chartType, setChartType] = useState<'grouped' | 'stacked' | 'line'>('grouped');
  const [showIncome, setShowIncome] = useState(true);
  const [showExpenses, setShowExpenses] = useState(true);
  const [showCumulative, setShowCumulative] = useState(false);
  const [showAverages, setShowAverages] = useState(false);

  useEffect(() => {
    fetchAnalysisData();
  }, []);
  
  useEffect(() => {
    fetchCategories();
  }, []);
  
  useEffect(() => {
    fetchSavedViews();
  }, []);
  
  // Recalculate data when filters change
  useEffect(() => {
    if (transactions.length > 0) {
      processTransactionData(transactions);
    }
  }, [transactions, selectedPeriod, customDateRange, aggregation, selectedCategories, chartType, showCumulative, showAverages]);

  const fetchAnalysisData = async () => {
    try {
      setLoading(true);
      
      // Fetch transactions, accounts, and categories data
      // Use /all endpoint to get complete transaction data for analysis
      const [transactionsRes, accountsRes] = await Promise.all([
        axios.get('http://localhost:8000/api/transactions/all'),
        axios.get('http://localhost:8000/api/accounts')
      ]);

      const transactionsData = transactionsRes.data;
      const accountsData = accountsRes.data;
      
      setTransactions(transactionsData);
      
      // Process data for charts
      processTransactionData(transactionsData);
      processAccountData(accountsData);
      
      setError(null);
    } catch (err) {
      setError('Failed to fetch analysis data');
      console.error('Error fetching analysis data:', err);
      // Fallback to sample data
      loadSampleData();
    } finally {
      setLoading(false);
    }
  };
  
  const fetchCategories = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/categories');
      const allCategories = response.data.filter((cat: Category) => !cat.is_bank_account);
      setCategories(allCategories);
      
      // Build category tree
      const tree = buildCategoryTree(allCategories);
      setCategoryTree(tree);
    } catch (err) {
      console.error('Error fetching categories:', err);
    }
  };
  
  const fetchSavedViews = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/analysis-views');
      setSavedViews(response.data);
    } catch (err) {
      console.error('Error fetching saved views:', err);
    }
  };
  
  const buildCategoryTree = (categories: Category[]): Category[] => {
    const categoryMap = new Map<string, Category>();
    const rootCategories: Category[] = [];
    
    // Create category map
    categories.forEach(cat => {
      categoryMap.set(cat.id, { ...cat, children: [] });
    });
    
    // Build tree structure
    categories.forEach(cat => {
      const category = categoryMap.get(cat.id)!;
      if (cat.parent_id && categoryMap.has(cat.parent_id)) {
        const parent = categoryMap.get(cat.parent_id)!;
        parent.children!.push(category);
      } else {
        rootCategories.push(category);
      }
    });
    
    return rootCategories;
  };

  const loadSampleData = () => {
    setCategoryData([
      { name: 'Food/Groceries', amount: 645.32, percentage: 35 },
      { name: 'Utilities', amount: 287.50, percentage: 15 },
      { name: 'Business/Supplies', amount: 234.50, percentage: 13 },
      { name: 'Transport', amount: 189.20, percentage: 10 },
      { name: 'Entertainment', amount: 156.80, percentage: 8 },
      { name: 'Other', amount: 342.68, percentage: 19 }
    ]);

    const now = new Date();
    setMonthlyData([
      { period: 'Jan', income: 4250, expenses: 3100, net: 1150, date: new Date(now.getFullYear(), 0, 15) },
      { period: 'Feb', income: 3980, expenses: 3250, net: 730, date: new Date(now.getFullYear(), 1, 15) },
      { period: 'Mar', income: 4750, expenses: 2890, net: 1860, date: new Date(now.getFullYear(), 2, 15) },
      { period: 'Apr', income: 4200, expenses: 3450, net: 750, date: new Date(now.getFullYear(), 3, 15) },
      { period: 'May', income: 5100, expenses: 3200, net: 1900, date: new Date(now.getFullYear(), 4, 15) }
    ]);

    setAccountBalances([
      { account: 'Westpac Savings', balance: 5234.67, change: 234.56 },
      { account: 'NAB Business', balance: 12450.33, change: -156.78 },
      { account: 'NAB Savings', balance: 1875.20, change: 89.45 }
    ]);
  };

  const getDateRange = () => {
    const now = new Date();
    let startDate: Date, endDate: Date;
    
    if (selectedPeriod === 'custom' && customDateRange.start && customDateRange.end) {
      startDate = new Date(customDateRange.start);
      endDate = new Date(customDateRange.end);
    } else {
      endDate = now;
      switch (selectedPeriod) {
        case 'week':
          startDate = new Date(now);
          startDate.setDate(now.getDate() - 7);
          break;
        case 'month':
          startDate = new Date(now.getFullYear(), now.getMonth(), 1);
          break;
        case 'quarter':
          const quarterStartMonth = Math.floor(now.getMonth() / 3) * 3;
          startDate = new Date(now.getFullYear(), quarterStartMonth, 1);
          break;
        case 'year':
          startDate = new Date(now.getFullYear(), 0, 1);
          break;
        default:
          startDate = new Date(now.getFullYear(), now.getMonth(), 1);
      }
    }
    
    return { startDate, endDate };
  };
  
  const processTransactionData = (transactions: any[]) => {
    const { startDate, endDate } = getDateRange();
    
    // Filter transactions by date range and exclude uncategorised transactions
    const filteredTransactions = transactions.filter(transaction => {
      if (transaction.is_internal_transfer) return false;
      if (!transaction.category_id) return false; // Exclude uncategorised transactions
      const transactionDate = new Date(transaction.date);
      return transactionDate >= startDate && transactionDate <= endDate;
    });
    
    // Filter by selected categories if any are selected
    const categoryFilteredTransactions = selectedCategories.length > 0 
      ? filteredTransactions.filter(t => {
          if (!t.category_id) return false;
          // Check if transaction category or any parent category is selected
          return isSelectedCategory(t.category_id, selectedCategories);
        })
      : filteredTransactions;
    
    // Group transactions by time period
    const periodData = new Map<string, { income: number, expenses: number, date: Date, categoryBreakdown: Map<string, number> }>();
    const expensesByCategory = new Map<string, number>();
    const incomeByCategory = new Map<string, number>();
    
    categoryFilteredTransactions.forEach(transaction => {
      const date = new Date(transaction.date);
      let periodKey: string;
      
      switch (aggregation) {
        case 'day':
          periodKey = date.toISOString().split('T')[0];
          break;
        case 'week':
          const weekStart = new Date(date);
          weekStart.setDate(date.getDate() - date.getDay());
          periodKey = weekStart.toISOString().split('T')[0];
          break;
        case 'month':
          periodKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
          break;
        case 'quarter':
          const quarter = Math.floor(date.getMonth() / 3) + 1;
          periodKey = `${date.getFullYear()}-Q${quarter}`;
          break;
      }
      
      // Initialize period data
      if (!periodData.has(periodKey)) {
        periodData.set(periodKey, { income: 0, expenses: 0, date, categoryBreakdown: new Map() });
      }
      
      const data = periodData.get(periodKey)!;
      
      const category = transaction.category_name || transaction.category_id;
      const simplifiedCategory = category.split('/').pop() || category;

      if (transaction.deposit > 0) {
        data.income += transaction.deposit;
        
        // Group income by category
        incomeByCategory.set(simplifiedCategory, (incomeByCategory.get(simplifiedCategory) || 0) + transaction.deposit);
      } else if (transaction.withdrawal > 0) {
        data.expenses += transaction.withdrawal;
        
        // Group expenses by category for pie chart and stacked bars
        expensesByCategory.set(simplifiedCategory, (expensesByCategory.get(simplifiedCategory) || 0) + transaction.withdrawal);
        
        // Track category breakdown for stacked charts
        const currentAmount = data.categoryBreakdown.get(simplifiedCategory) || 0;
        data.categoryBreakdown.set(simplifiedCategory, currentAmount + transaction.withdrawal);
      }
    });
    
    // Convert to chart data with category breakdown
    const sortedPeriods = Array.from(periodData.entries())
      .sort(([a, dataA], [b, dataB]) => dataA.date.getTime() - dataB.date.getTime())
      .map(([period, data]) => {
        const result: any = {
          period,
          income: data.income,
          expenses: data.expenses,
          net: data.income - data.expenses,
          date: data.date
        };
        
        // Add category breakdown for stacked charts
        data.categoryBreakdown.forEach((amount, category) => {
          result[category] = amount;
        });
        
        return result;
      });
    
    // Always calculate cumulative data (will be used conditionally in charts)
    let cumulativeIncome = 0;
    let cumulativeExpenses = 0;
    let cumulativeNet = 0;
    
    sortedPeriods.forEach(item => {
      cumulativeIncome += item.income;
      cumulativeExpenses += item.expenses;
      cumulativeNet += item.net;
      
      (item as any).cumulativeIncome = cumulativeIncome;
      (item as any).cumulativeExpenses = cumulativeExpenses;
      (item as any).cumulativeNet = cumulativeNet;
    });
    
    // Always calculate averages (will be used conditionally in charts)
    if (sortedPeriods.length > 0) {
      const avgIncome = sortedPeriods.reduce((sum, item) => sum + item.income, 0) / sortedPeriods.length;
      const avgExpenses = sortedPeriods.reduce((sum, item) => sum + item.expenses, 0) / sortedPeriods.length;
      const avgNet = sortedPeriods.reduce((sum, item) => sum + item.net, 0) / sortedPeriods.length;
      
      sortedPeriods.forEach(item => {
        (item as any).avgIncome = avgIncome;
        (item as any).avgExpenses = avgExpenses;
        (item as any).avgNet = avgNet;
      });
    }
    
    // Category data for pie chart with "Other" grouping
    const totalExpenses = Array.from(expensesByCategory.values()).reduce((sum, amount) => sum + amount, 0);
    const expenseCategories = Array.from(expensesByCategory.entries())
      .map(([name, amount]) => ({
        name,
        amount,
        percentage: (amount / totalExpenses) * 100
      }))
      .sort((a, b) => b.amount - a.amount);
    
    // Group categories with <1% into "Other" (only for pie chart)
    const significantCategories = expenseCategories.filter(cat => cat.percentage >= 1);
    const smallCategories = expenseCategories.filter(cat => cat.percentage < 1);
    
    const categoryChartData = [...significantCategories];
    if (smallCategories.length > 0) {
      const otherAmount = smallCategories.reduce((sum, cat) => sum + cat.amount, 0);
      categoryChartData.push({
        name: 'Other',
        amount: otherAmount,
        percentage: (otherAmount / totalExpenses) * 100
      });
    }
    
    // Income category data
    const totalIncome = Array.from(incomeByCategory.values()).reduce((sum, amount) => sum + amount, 0);
    const incomeCategories = Array.from(incomeByCategory.entries())
      .map(([name, amount]) => ({
        name,
        amount,
        percentage: (amount / totalIncome) * 100
      }))
      .sort((a, b) => b.amount - a.amount);
    
    setCategoryData(categoryChartData);
    setIncomeCategoryData(incomeCategories);
    setMonthlyData(sortedPeriods);
    
    // Store the original expense categories (without "Other" grouping) for the breakdown table
    setExpenseCategoriesData(expenseCategories);
  };

  const processAccountData = (accounts: any[]) => {
    const accountData = accounts.map(account => ({
      account: account.name,
      balance: account.current_balance,
      change: Math.random() * 200 - 100 // Mock change data - would need historical data for real changes
    }));
    
    setAccountBalances(accountData);
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D', '#8DD1E1', '#D084D0'];
  
  const getCategoryColor = (categoryName: string, index: number) => {
    return categoryName === 'Other' ? '#000000' : COLORS[index % COLORS.length];
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'AUD'
    }).format(value);
  };

  const getTotalBalance = () => {
    return accountBalances.reduce((sum, account) => sum + account.balance, 0);
  };

  const getTotalIncome = () => {
    return monthlyData.reduce((sum, item) => sum + item.income, 0);
  };

  const getTotalExpenses = () => {
    return categoryData.reduce((sum, category) => sum + category.amount, 0);
  };

  const getNetIncome = () => {
    return monthlyData.reduce((sum, item) => sum + item.net, 0);
  };
  
  const formatPeriodLabel = (period: string, date?: Date) => {
    if (!date) return period;
    
    switch (aggregation) {
      case 'day':
        return date.toLocaleDateString('en-AU', { month: 'short', day: 'numeric' });
      case 'week':
        return `Week ${date.toLocaleDateString('en-AU', { month: 'short', day: 'numeric' })}`;
      case 'month':
        return date.toLocaleDateString('en-AU', { month: 'short', year: 'numeric' });
      case 'quarter':
        return period;
      default:
        return period;
    }
  };
  
  const isSelectedCategory = (categoryId: string, selectedIds: string[]): boolean => {
    if (selectedIds.includes(categoryId)) return true;
    
    // Check if any parent category is selected
    const category = categories.find(c => c.id === categoryId);
    if (category?.parent_id) {
      return isSelectedCategory(category.parent_id, selectedIds);
    }
    
    return false;
  };
  
  const getAllChildCategories = (categoryId: string): string[] => {
    const children: string[] = [];
    const category = categories.find(c => c.id === categoryId);
    
    if (category) {
      children.push(categoryId);
      categories
        .filter(c => c.parent_id === categoryId)
        .forEach(child => {
          children.push(...getAllChildCategories(child.id));
        });
    }
    
    return children;
  };
  
  const toggleCategory = (categoryId: string) => {
    const allChildren = getAllChildCategories(categoryId);
    const isCurrentlySelected = selectedCategories.some(id => allChildren.includes(id));
    
    if (isCurrentlySelected) {
      // Remove this category and all its children
      setSelectedCategories(prev => prev.filter(id => !allChildren.includes(id)));
    } else {
      // Add this category (and implicitly its children)
      setSelectedCategories(prev => [...prev, categoryId]);
    }
  };
  
  const toggleCategoryExpanded = (categoryId: string) => {
    setExpandedCategories(prev => {
      const newSet = new Set(prev);
      if (newSet.has(categoryId)) {
        newSet.delete(categoryId);
      } else {
        newSet.add(categoryId);
      }
      return newSet;
    });
  };
  
  const clearCategoryFilter = () => {
    setSelectedCategories([]);
  };
  
  // View management functions
  const saveCurrentView = async () => {
    if (!currentViewName.trim()) return;
    
    try {
      const viewData = {
        name: currentViewName,
        selectedCategories,
        selectedPeriod,
        customDateRange,
        aggregation,
        chartType,
        showIncome,
        showExpenses,
        showCumulative,
        showAverages
      };
      
      await axios.post('http://localhost:8000/api/analysis-views', viewData);
      setCurrentViewName('');
      
      // Refresh the saved views list
      await fetchSavedViews();
    } catch (err) {
      console.error('Error saving view:', err);
    }
  };
  
  const loadView = (view: AnalysisView) => {
    setSelectedCategories(view.selectedCategories);
    setSelectedPeriod(view.selectedPeriod);
    setCustomDateRange(view.customDateRange);
    setAggregation(view.aggregation);
    setChartType(view.chartType);
    setShowIncome(view.showIncome);
    setShowExpenses(view.showExpenses);
    setShowCumulative(view.showCumulative);
    setShowAverages(view.showAverages);
  };
  
  const deleteView = async (viewId: string) => {
    try {
      await axios.delete(`http://localhost:8000/api/analysis-views/${viewId}`);
      
      // Refresh the saved views list
      await fetchSavedViews();
    } catch (err) {
      console.error('Error deleting view:', err);
    }
  };
  
  const clearCustomRange = () => {
    setCustomDateRange({ start: '', end: '' });
  };

  const selectEarliestDate = () => {
    if (transactions.length === 0) return;
    
    // Filter transactions by selected categories if any are selected, always exclude uncategorised
    const relevantTransactions = selectedCategories.length > 0 
      ? transactions.filter(t => {
          if (!t.category_id) return false;
          return isSelectedCategory(t.category_id, selectedCategories);
        })
      : transactions.filter(t => t.category_id); // Exclude uncategorised transactions
    
    if (relevantTransactions.length === 0) return;
    
    // Find the earliest transaction date
    const earliestDate = relevantTransactions.reduce((earliest, transaction) => {
      const transactionDate = new Date(transaction.date);
      return transactionDate < earliest ? transactionDate : earliest;
    }, new Date(relevantTransactions[0].date));
    
    // Set the custom date range from earliest to now
    const now = new Date();
    setCustomDateRange({
      start: earliestDate.toISOString().split('T')[0],
      end: now.toISOString().split('T')[0]
    });
  };
  
  // Get unique categories from filtered data for stacked charts
  const getSelectedCategoryNames = () => {
    if (selectedCategories.length === 0) return [];
    
    const selectedCategorySet = new Set<string>();
    selectedCategories.forEach(catId => {
      const allChildren = getAllChildCategories(catId);
      allChildren.forEach(childId => {
        const category = categories.find(c => c.id === childId);
        if (category) {
          const simplifiedName = category.name.split('/').pop() || category.name;
          selectedCategorySet.add(simplifiedName);
        }
      });
    });
    
    return Array.from(selectedCategorySet);
  };
  
  const renderCategoryTree = (categories: Category[], level: number = 0) => {
    return categories.map(category => {
      const hasChildren = category.children && category.children.length > 0;
      const isExpanded = expandedCategories.has(category.id);
      const isSelected = selectedCategories.includes(category.id);
      const hasSelectedChildren = selectedCategories.some(id => 
        getAllChildCategories(category.id).includes(id)
      );
      
      return (
        <div key={category.id} className="">
          <div 
            className={`flex items-center py-1 px-2 rounded hover:bg-gray-100 cursor-pointer ${
              isSelected ? 'bg-indigo-100 text-indigo-800' : 
              hasSelectedChildren ? 'bg-indigo-50 text-indigo-600' : ''
            }`}
            style={{ paddingLeft: `${level * 20 + 8}px` }}
          >
            {hasChildren && (
              <button
                onClick={() => toggleCategoryExpanded(category.id)}
                className="mr-1 p-0.5 hover:bg-gray-200 rounded"
              >
                {isExpanded ? 
                  <ChevronDown className="w-3 h-3" /> : 
                  <ChevronRight className="w-3 h-3" />
                }
              </button>
            )}
            {!hasChildren && <div className="w-4 mr-1" />}
            
            <button
              onClick={() => toggleCategory(category.id)}
              className="flex-1 text-left text-sm"
            >
              {category.name.split('/').pop()}
            </button>
            
            {(isSelected || hasSelectedChildren) && (
              <div className={`w-2 h-2 rounded-full ${
                isSelected ? 'bg-indigo-500' : 'bg-indigo-300'
              }`} />
            )}
          </div>
          
          {hasChildren && isExpanded && (
            <div className="">
              {renderCategoryTree(category.children!, level + 1)}
            </div>
          )}
        </div>
      );
    });
  };
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-xl">Loading analysis data...</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4 shadow-sm">
        {error && (
          <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded mb-4">
            {error} - Using sample data for demonstration
          </div>
        )}
        <div className="flex flex-col space-y-4 mb-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200">Financial Analysis</h2>
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-gray-500 dark:text-gray-400" />
              <span className="text-sm text-gray-500 dark:text-gray-400">Filters Active: {selectedCategories.length > 0 || customDateRange.start ? 'Yes' : 'No'}</span>
            </div>
          </div>
          
          {/* Filter Controls */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
            {/* Date Range */}
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-700 dark:text-gray-300">Time Period</label>
              <select
                className="w-full border border-gray-300 dark:border-gray-600 rounded-md px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                value={selectedPeriod}
                onChange={(e) => {
                  setSelectedPeriod(e.target.value);
                  if (e.target.value !== 'custom') {
                    clearCustomRange();
                  }
                }}
              >
                <option value="week">This Week</option>
                <option value="month">This Month</option>
                <option value="quarter">This Quarter</option>
                <option value="year">This Year</option>
                <option value="custom">Custom Range</option>
              </select>
              
              {selectedPeriod === 'custom' && (
                <div className="space-y-1 mt-1">
                  <div className="flex space-x-1">
                    <input
                      type="date"
                      className="flex-1 border border-gray-300 dark:border-gray-600 rounded-md px-1.5 py-1 text-xs bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                      value={customDateRange.start}
                      onChange={(e) => setCustomDateRange(prev => ({ ...prev, start: e.target.value }))}
                    />
                    <input
                      type="date"
                      className="flex-1 border border-gray-300 dark:border-gray-600 rounded-md px-1.5 py-1 text-xs bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                      value={customDateRange.end}
                      onChange={(e) => setCustomDateRange(prev => ({ ...prev, end: e.target.value }))}
                    />
                  </div>
                  <button
                    onClick={selectEarliestDate}
                    className="w-full px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                    title={selectedCategories.length > 0 ? "Select earliest date from filtered categories" : "Select earliest date from all transactions"}
                  >
                    Select Earliest
                  </button>
                </div>
              )}
            </div>
            
            {/* Aggregation */}
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-700 dark:text-gray-300">Group By</label>
              <select
                className="w-full border border-gray-300 dark:border-gray-600 rounded-md px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                value={aggregation}
                onChange={(e) => setAggregation(e.target.value as any)}
              >
                <option value="day">Daily</option>
                <option value="week">Weekly</option>
                <option value="month">Monthly</option>
                <option value="quarter">Quarterly</option>
              </select>
            </div>
            
            {/* Views Management */}
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-700 dark:text-gray-300">Views</label>
              <div className="flex space-x-1">
                <button
                  onClick={() => setShowViewManager(!showViewManager)}
                  className="flex-1 flex items-center justify-center space-x-1 px-2 py-1.5 bg-white dark:bg-gray-700 rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600 text-xs dark:text-gray-100"
                >
                  <Eye className="w-3 h-3" />
                  <span>Manage</span>
                </button>
                {savedViews.length > 0 && (
                  <div className="flex space-x-0.5">
                    {savedViews.slice(0, 2).map(view => (
                      <button
                        key={view.id}
                        onClick={() => loadView(view)}
                        className="px-1.5 py-1.5 text-xs bg-indigo-100 text-indigo-700 rounded hover:bg-indigo-200"
                        title={view.name}
                      >
                        {view.name.substring(0, 3)}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
            
            {/* Category Filter */}
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-700 dark:text-gray-300">Categories</label>
              <button
                onClick={() => setShowCategoryPanel(!showCategoryPanel)}
                className={`w-full flex items-center justify-center space-x-1.5 px-2 py-1.5 rounded border transition-colors text-xs ${
                  showCategoryPanel 
                    ? 'bg-indigo-500 text-white border-indigo-500' 
                    : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:border-indigo-300 dark:hover:border-indigo-500'
                }`}
              >
                <Filter className="w-3 h-3" />
                <span>Filter ({selectedCategories.length})</span>
                {showCategoryPanel ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
              </button>
            </div>
          </div>
          
          {/* View Manager Panel */}
          {showViewManager && (
            <div className="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium text-gray-800 dark:text-gray-200">Saved Views</h4>
                <button
                  onClick={() => setShowViewManager(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ×
                </button>
              </div>
              
              <div className="flex space-x-2 mb-3">
                <input
                  type="text"
                  placeholder="View name..."
                  value={currentViewName}
                  onChange={(e) => setCurrentViewName(e.target.value)}
                  className="flex-1 px-2 py-1 border rounded text-sm"
                />
                <button
                  onClick={saveCurrentView}
                  disabled={!currentViewName.trim()}
                  className="flex items-center space-x-1 px-2 py-1 bg-indigo-500 text-white rounded text-sm disabled:opacity-50"
                >
                  <Save className="w-3 h-3" />
                  <span>Save</span>
                </button>
              </div>
              
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {savedViews.map(view => (
                  <div key={view.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm font-medium">{view.name}</span>
                    <div className="flex space-x-1">
                      <button
                        onClick={() => loadView(view)}
                        className="px-2 py-1 text-xs bg-indigo-500 text-white rounded hover:bg-indigo-600"
                      >
                        Load
                      </button>
                      <button
                        onClick={() => deleteView(view.id)}
                        className="px-2 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                ))}
                {savedViews.length === 0 && (
                  <p className="text-sm text-gray-500 text-center py-2">No saved views</p>
                )}
              </div>
            </div>
          )}
          
          {/* Category Filter Panel */}
          {showCategoryPanel && categoryTree.length > 0 && (
            <div className="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium text-gray-800">Filter by Categories</h4>
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-gray-500">{selectedCategories.length} selected</span>
                  {selectedCategories.length > 0 && (
                    <button
                      onClick={clearCategoryFilter}
                      className="text-xs text-indigo-600 hover:text-indigo-800"
                    >
                      Clear All
                    </button>
                  )}
                  <button
                    onClick={() => setShowCategoryPanel(false)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    ×
                  </button>
                </div>
              </div>
              
              <div className="max-h-64 overflow-y-auto border rounded p-2">
                {renderCategoryTree(categoryTree)}
              </div>
            </div>
          )}
        </div>

      </div>

      {/* Charts */}
      <div className="flex-1 overflow-auto p-4">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Income vs Expenses Chart */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-800">
                Income vs Expenses ({aggregation === 'day' ? 'Daily' : aggregation === 'week' ? 'Weekly' : aggregation === 'month' ? 'Monthly' : 'Quarterly'})
              </h3>
              <div className="flex items-center space-x-4">
                {/* Chart Type Controls */}
                <div className="flex items-center space-x-1">
                  <span className="text-xs text-gray-600">Type:</span>
                  <button
                    className={`px-2 py-1 text-xs rounded ${chartType === 'grouped' ? 'bg-indigo-500 text-white' : 'bg-gray-200 text-gray-700'}`}
                    onClick={() => {
                      setChartType('grouped');
                      setShowCumulative(false); // Reset cumulative when switching to bar chart
                    }}
                    title="Grouped Bars"
                  >
                    <BarChart3 className="w-3 h-3" />
                  </button>
                  <button
                    className={`px-2 py-1 text-xs rounded ${chartType === 'stacked' ? 'bg-indigo-500 text-white' : 'bg-gray-200 text-gray-700'}`}
                    onClick={() => {
                      setChartType('stacked');
                      setShowCumulative(false); // Reset cumulative when switching to bar chart
                    }}
                    title="Stacked Bars"
                  >
                    <Target className="w-3 h-3" />
                  </button>
                  <button
                    className={`px-2 py-1 text-xs rounded ${chartType === 'line' ? 'bg-indigo-500 text-white' : 'bg-gray-200 text-gray-700'}`}
                    onClick={() => {
                      setChartType('line');
                      setShowAverages(false); // Reset averages when switching to line chart
                    }}
                    title="Line Chart"
                  >
                    <LineChartIcon className="w-3 h-3" />
                  </button>
                </div>
                
                {/* Display Options */}
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-gray-600">Show:</span>
                  <div className="flex items-center space-x-1">
                    <input
                      type="checkbox"
                      id="showIncomeChart"
                      checked={showIncome}
                      onChange={(e) => setShowIncome(e.target.checked)}
                      className="rounded w-3 h-3"
                    />
                    <label htmlFor="showIncomeChart" className="text-xs">Inc</label>
                  </div>
                  <div className="flex items-center space-x-1">
                    <input
                      type="checkbox"
                      id="showExpensesChart"
                      checked={showExpenses}
                      onChange={(e) => setShowExpenses(e.target.checked)}
                      className="rounded w-3 h-3"
                    />
                    <label htmlFor="showExpensesChart" className="text-xs">Exp</label>
                  </div>
                  <div className="flex items-center space-x-1">
                    <input
                      type="checkbox"
                      id="showCumulativeChart"
                      checked={showCumulative}
                      onChange={(e) => setShowCumulative(e.target.checked)}
                      className="rounded w-3 h-3"
                    />
                    <label htmlFor="showCumulativeChart" className="text-xs">Cum</label>
                  </div>
                  <div className="flex items-center space-x-1">
                    <input
                      type="checkbox"
                      id="showAveragesChart"
                      checked={showAverages}
                      onChange={(e) => setShowAverages(e.target.checked)}
                      className="rounded w-3 h-3"
                    />
                    <label htmlFor="showAveragesChart" className="text-xs">Avg</label>
                  </div>
                </div>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={350}>
              {chartType === 'line' ? (
                <LineChart data={monthlyData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="period" 
                    tickFormatter={(value, index) => formatPeriodLabel(value, monthlyData[index]?.date)}
                  />
                  <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(1)}k`} />
                  <Tooltip 
                    formatter={(value) => formatCurrency(Number(value))} 
                    labelFormatter={(label, payload) => {
                      if (payload && payload[0]) {
                        return formatPeriodLabel(label, payload[0].payload.date);
                      }
                      return label;
                    }}
                  />
                  <Legend />
                  {showIncome && (
                    <Line 
                      type="monotone" 
                      dataKey={showCumulative ? "cumulativeIncome" : "income"} 
                      stroke="#22C55E" 
                      strokeWidth={2}
                      name={showCumulative ? "Cumulative Income" : "Income"}
                    />
                  )}
                  {showExpenses && (
                    <Line 
                      type="monotone" 
                      dataKey={showCumulative ? "cumulativeExpenses" : "expenses"} 
                      stroke="#EF4444" 
                      strokeWidth={2}
                      name={showCumulative ? "Cumulative Expenses" : "Expenses"}
                    />
                  )}
                  <Line 
                    type="monotone" 
                    dataKey={showCumulative ? "cumulativeNet" : "net"} 
                    stroke="#3B82F6" 
                    strokeWidth={2}
                    name={showCumulative ? "Cumulative Net" : "Net"}
                  />
                  {/* No averages for line charts */}
                  <Brush dataKey="period" height={30} />
                </LineChart>
              ) : (
                <BarChart data={monthlyData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="period" 
                    tickFormatter={(value, index) => formatPeriodLabel(value, monthlyData[index]?.date)}
                  />
                  <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(1)}k`} />
                  <Tooltip 
                    formatter={(value) => formatCurrency(Number(value))} 
                    labelFormatter={(label, payload) => {
                      if (payload && payload[0]) {
                        return formatPeriodLabel(label, payload[0].payload.date);
                      }
                      return label;
                    }}
                  />
                  <Legend />
                  {showIncome && (
                    <Bar 
                      dataKey="income" 
                      fill="#22C55E" 
                      name="Income"
                      stackId={chartType === 'stacked' ? 'stack' : undefined}
                    />
                  )}
                  {showExpenses && chartType === 'stacked' && selectedCategories.length > 0 ? (
                    // Show individual categories in stacked view
                    getSelectedCategoryNames().map((categoryName, index) => (
                      <Bar 
                        key={categoryName}
                        dataKey={categoryName}
                        fill={COLORS[index % COLORS.length]} 
                        name={categoryName}
                        stackId="expenses"
                      />
                    ))
                  ) : showExpenses ? (
                    <Bar 
                      dataKey="expenses" 
                      fill="#EF4444" 
                      name="Expenses"
                      stackId={chartType === 'stacked' ? 'stack' : undefined}
                    />
                  ) : null}
                  {/* Average lines - only for bar charts */}
                  {showAverages && showIncome && (chartType === 'grouped' || chartType === 'stacked') && monthlyData.length > 0 && (
                    <ReferenceLine y={(monthlyData[0] as any)?.avgIncome || 0} stroke="#22C55E" strokeDasharray="5 5" label="Avg Income" />
                  )}
                  {showAverages && showExpenses && (chartType === 'grouped' || chartType === 'stacked') && monthlyData.length > 0 && (
                    <ReferenceLine y={(monthlyData[0] as any)?.avgExpenses || 0} stroke="#EF4444" strokeDasharray="5 5" label="Avg Expenses" />
                  )}
                  <Brush dataKey="period" height={30} />
                </BarChart>
              )}
            </ResponsiveContainer>
          </div>

          {/* Expense Categories (Pie Chart) */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Expense Breakdown</h3>
            <ResponsiveContainer width="100%" height={350}>
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percentage }) => `${name} (${percentage.toFixed(1)}%)`}
                  outerRadius={120}
                  fill="#8884d8"
                  dataKey="amount"
                >
                  {categoryData.map((category, index) => (
                    <Cell key={`cell-${index}`} fill={getCategoryColor(category.name, index)} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => formatCurrency(Number(value))} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
          <div className="bg-green-50 rounded-lg p-4">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <TrendingUp className="w-6 h-6 text-green-600" />
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-green-600">Income</p>
                <p className="text-2xl font-semibold text-green-900">{formatCurrency(getTotalIncome())}</p>
              </div>
            </div>
          </div>

          <div className="bg-red-50 rounded-lg p-4">
            <div className="flex items-center">
              <div className="p-2 bg-red-100 rounded-lg">
                <TrendingDown className="w-6 h-6 text-red-600" />
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-red-600">Expenses</p>
                <p className="text-2xl font-semibold text-red-900">{formatCurrency(getTotalExpenses())}</p>
              </div>
            </div>
          </div>

          <div className={`${getNetIncome() >= 0 ? 'bg-green-50' : 'bg-red-50'} rounded-lg p-4`}>
            <div className="flex items-center">
              <div className={`p-2 ${getNetIncome() >= 0 ? 'bg-green-100' : 'bg-red-100'} rounded-lg`}>
                <DollarSign className={`w-6 h-6 ${getNetIncome() >= 0 ? 'text-green-600' : 'text-red-600'}`} />
              </div>
              <div className="ml-3">
                <p className={`text-sm font-medium ${getNetIncome() >= 0 ? 'text-green-600' : 'text-red-600'}`}>Net Income</p>
                <p className={`text-2xl font-semibold ${getNetIncome() >= 0 ? 'text-green-900' : 'text-red-900'}`}>
                  {formatCurrency(getNetIncome())}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Categories Breakdown with Net Analysis */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 mt-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Categories Breakdown</h3>
          <div className="overflow-x-auto">
            {(() => {
              // Combine income and expense data
              const incomeMap = new Map(incomeCategoryData.map(cat => [cat.name, cat.amount]));
              const expenseMap = new Map(expenseCategoriesData.map(cat => [cat.name, cat.amount]));
              
              // Get all unique category names
              const allCategoryNames = new Set([
                ...incomeCategoryData.map(cat => cat.name),
                ...expenseCategoriesData.map(cat => cat.name)
              ]);
              
              // Create combined data with net calculations
              const combinedData = Array.from(allCategoryNames).map(name => {
                const income = incomeMap.get(name) || 0;
                const expense = expenseMap.get(name) || 0;
                const net = income - expense;
                
                return {
                  name,
                  income,
                  expense,
                  net,
                  totalAmount: Math.abs(net)
                };
              }).sort((a, b) => b.net - a.net); // Sort by net (highest income to lowest expense)
              
              // Calculate max absolute value for bar width scaling
              const maxAbsValue = Math.max(...combinedData.map(cat => 
                Math.max(cat.income, cat.expense, Math.abs(cat.net))
              ));
              
              return (
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider w-1/4">
                        Category
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-green-600 uppercase tracking-wider w-1/5">
                        Income
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-red-600 uppercase tracking-wider w-1/5">
                        Expenses
                      </th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-600 uppercase tracking-wider w-2/5">
                        Net Amount
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {combinedData.map((category, index) => {
                      const netBarWidth = maxAbsValue > 0 ? (Math.abs(category.net) / maxAbsValue) * 100 : 0;
                      const isPositive = category.net >= 0;
                      
                      return (
                        <tr key={index} className="hover:bg-gray-50">
                          <td className="px-4 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {category.name}
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap text-sm text-right">
                            {category.income > 0 ? (
                              <span className="text-green-600 font-medium">
                                {formatCurrency(category.income)}
                              </span>
                            ) : (
                              <span className="text-gray-400">—</span>
                            )}
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap text-sm text-right">
                            {category.expense > 0 ? (
                              <span className="text-red-600 font-medium">
                                {formatCurrency(category.expense)}
                              </span>
                            ) : (
                              <span className="text-gray-400">—</span>
                            )}
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap">
                            <div className="flex items-center justify-center space-x-2">
                              <div className="flex-1 flex items-center justify-end">
                                <span className={`text-sm font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                                  {formatCurrency(Math.abs(category.net))}
                                </span>
                              </div>
                              <div className="w-24 h-4 bg-gray-200 rounded-full relative overflow-hidden">
                                <div 
                                  className={`h-full rounded-full transition-all duration-300 ${
                                    isPositive ? 'bg-green-400' : 'bg-red-400'
                                  }`}
                                  style={{ width: `${netBarWidth}%` }}
                                />
                              </div>
                              <div className="flex-1 flex items-center justify-start">
                                <span className={`text-xs ${
                                  isPositive ? 'text-green-600' : 'text-red-600'
                                }`}>
                                  {category.net !== 0 ? `${((Math.abs(category.net) / (getTotalIncome() + getTotalExpenses())) * 100).toFixed(1)}%` : '0%'}
                                </span>
                              </div>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                    {combinedData.length === 0 && (
                      <tr>
                        <td colSpan={4} className="px-4 py-6 text-center text-sm text-gray-500">
                          No categories found for selected period
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              );
            })()}
          </div>
          
          {/* Legend */}
          <div className="flex items-center justify-center space-x-6 mt-4 text-xs text-gray-600">
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-green-400 rounded"></div>
              <span>Net Income</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-red-400 rounded"></div>
              <span>Net Expense</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-gray-200 rounded"></div>
              <span>Relative Scale</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalysisView;