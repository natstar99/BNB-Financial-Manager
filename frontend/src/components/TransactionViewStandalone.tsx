import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { Search, Filter, Plus, Upload, Download, Tag, ArrowDownUp, Settings, Trash2, Eye, EyeOff, RefreshCw, ArrowLeftRight, ChevronUp, ChevronDown } from 'lucide-react';
import axios from 'axios';
import ImportDialog from './dialogs/ImportDialog';
import CategoryPickerDialog from './dialogs/CategoryPickerDialog';

interface Transaction {
  id: number;
  date: string;
  account: string;
  account_name?: string;
  description: string;
  withdrawal: number;
  deposit: number;
  category_id?: string;
  category_name?: string;
  tax_type?: string;
  is_tax_deductible: boolean;
  is_hidden: boolean;
  is_matched: boolean;
  is_internal_transfer: boolean;
}

interface PaginatedTransactionResponse {
  transactions: Transaction[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

interface TransactionViewStandaloneProps {
  initialAccountFilter?: string;
  initialCategoryFilter?: string;
}

const TransactionViewStandalone: React.FC<TransactionViewStandaloneProps> = ({ initialAccountFilter, initialCategoryFilter }) => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Pagination states
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(250);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  // Filter states - matching existing Qt application exactly
  const [activeFilter, setActiveFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [accountFilter, setAccountFilter] = useState(initialAccountFilter || '');
  const [categoryFilter, setCategoryFilter] = useState(initialCategoryFilter || '');
  
  // Sorting states
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  
  // Dialog states
  const [showImportDialog, setShowImportDialog] = useState(false);
  const [showCategoryPicker, setShowCategoryPicker] = useState(false);
  const [selectedTransactionId, setSelectedTransactionId] = useState<number | null>(null);
  
  // Multiselect states
  const [selectedTransactionIds, setSelectedTransactionIds] = useState<Set<number>>(new Set());
  const [showBulkCategoryPicker, setShowBulkCategoryPicker] = useState(false);
  
  // Request management and optimized caching
  const [abortController, setAbortController] = useState<AbortController | null>(null);
  
  // Simple cache for filter results (now includes page)
  const [cache, setCache] = useState<Map<string, PaginatedTransactionResponse>>(new Map());
  const [categoryName, setCategoryName] = useState<string>('');

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      // Only debounce search terms, fetch immediately for filter changes
      if (searchTerm.length === 0 || searchTerm.length >= 2) {
        // Reset to page 1 when filters change
        setCurrentPage(1);
        fetchTransactions(1);
      }
    }, searchTerm ? 800 : 0); // No delay for initial load or filter changes

    return () => clearTimeout(timeoutId);
  }, [activeFilter, searchTerm, accountFilter, categoryFilter]);

  // Effect for page changes (no debounce needed)
  useEffect(() => {
    if (currentPage > 1) { // Don't double-fetch on initial load
      fetchTransactions(currentPage);
    }
  }, [currentPage]);

  // Update account filter when initialAccountFilter prop changes
  useEffect(() => {
    if (initialAccountFilter !== accountFilter) {
      setAccountFilter(initialAccountFilter || '');
    }
  }, [initialAccountFilter]);

  // Update category filter when initialCategoryFilter prop changes
  useEffect(() => {
    if (initialCategoryFilter !== categoryFilter) {
      setCategoryFilter(initialCategoryFilter || '');
    }
  }, [initialCategoryFilter]);

  // Fetch category name when category filter changes
  useEffect(() => {
    const fetchCategoryName = async () => {
      if (categoryFilter) {
        try {
          const response = await axios.get('http://localhost:8000/api/categories');
          const category = response.data.find((c: any) => c.id === categoryFilter);
          setCategoryName(category ? category.name : categoryFilter);
        } catch (err) {
          setCategoryName(categoryFilter);
        }
      } else {
        setCategoryName('');
      }
    };
    
    fetchCategoryName();
  }, [categoryFilter]);

  const fetchTransactions = async (page: number = currentPage) => {
    try {
      // Cancel previous request if still pending
      if (abortController) {
        abortController.abort();
      }
      
      const newAbortController = new AbortController();
      setAbortController(newAbortController);
      
      setLoading(true);
      const params: any = {
        page,
        page_size: pageSize
      };
      
      // Map filter names to match API expectations
      if (activeFilter === 'uncategorised') {
        params.filter = 'uncategorised';
      } else if (activeFilter === 'internal') {
        params.filter = 'internal_transfers';
      } else if (activeFilter === 'hidden') {
        params.filter = 'hidden';
      } else {
        params.filter = 'all';
      }
      
      // Only add search if it's meaningful
      if (searchTerm && searchTerm.length >= 2) {
        params.search = searchTerm;
      }
      
      // Add account filter if specified
      if (accountFilter) {
        params.account_filter = accountFilter;
      }
      
      // Add category filter if specified
      if (categoryFilter) {
        params.category_filter = categoryFilter;
      }
      
      // Create cache key including page
      const cacheKey = `${params.filter || 'all'}_${params.search || ''}_${params.account_filter || ''}_${params.category_filter || ''}_${page}`;
      
      // Check cache first
      if (cache.has(cacheKey) && !searchTerm) {
        const cachedResponse = cache.get(cacheKey)!;
        setTransactions(cachedResponse.transactions);
        setTotalCount(cachedResponse.total_count);
        setTotalPages(cachedResponse.total_pages);
        setCurrentPage(cachedResponse.page);
        setLoading(false);
        setError(null);
        return;
      }

      const response = await axios.get<PaginatedTransactionResponse>('http://localhost:8000/api/transactions', { 
        params,
        timeout: 10000,
        signal: newAbortController.signal
      });
      
      setTransactions(response.data.transactions);
      setTotalCount(response.data.total_count);
      setTotalPages(response.data.total_pages);
      setCurrentPage(response.data.page);
      setError(null);
      
      // Cache the results (only for non-search queries)
      if (!searchTerm) {
        const newCache = new Map(cache);
        newCache.set(cacheKey, response.data);
        setCache(newCache);
      }
    } catch (err: any) {
      if (err.name === 'CanceledError') {
        return; // Request was cancelled, ignore
      }
      setError('Failed to fetch transactions');
      console.error('Error fetching transactions:', err);
    } finally {
      setLoading(false);
      setAbortController(null);
    }
  };

  // Optimized cache invalidation - only clear affected entries
  const invalidateCache = () => {
    setCache(new Map());
  };

  const handleCategoryUpdate = async (transactionId: number, categoryId: string) => {
    try {
      // Get category name for optimistic update
      const categoryResponse = await axios.get('http://localhost:8000/api/categories');
      const category = categoryResponse.data.find((c: any) => c.id === categoryId);
      const categoryName = category?.name || categoryId;

      // Optimistic update - update the transaction in current state immediately
      setTransactions(prev => prev.map(t => 
        t.id === transactionId 
          ? { ...t, category_id: categoryId, category_name: categoryName }
          : t
      ));

      // Then make the API call
      await axios.put(`http://localhost:8000/api/transactions/${transactionId}/category`, null, {
        params: { category_id: categoryId }
      });
      
      // Invalidate cache for fresh data on next request
      invalidateCache();
    } catch (err) {
      console.error('Error updating transaction category:', err);
      alert('Failed to update transaction category');
      // Refresh on error to ensure consistency
      fetchTransactions();
    }
  };

  const handleToggleHidden = async (transactionId: number) => {
    try {
      await axios.put(`http://localhost:8000/api/transactions/${transactionId}/hide`);
      
      // Optimistic update
      setTransactions(prev => prev.map(t => 
        t.id === transactionId 
          ? { ...t, is_hidden: !t.is_hidden }
          : t
      ));
      
      invalidateCache();
    } catch (err) {
      console.error('Error toggling transaction visibility:', err);
      alert('Failed to toggle transaction visibility');
      fetchTransactions();
    }
  };

  const handleToggleInternalTransfer = async (transactionId: number) => {
    try {
      await axios.put(`http://localhost:8000/api/transactions/${transactionId}/internal_transfer`);
      
      // Optimistic update
      setTransactions(prev => prev.map(t => 
        t.id === transactionId 
          ? { ...t, is_internal_transfer: !t.is_internal_transfer }
          : t
      ));
      
      invalidateCache();
    } catch (err) {
      console.error('Error toggling transaction internal transfer status:', err);
      alert('Failed to toggle transaction internal transfer status');
      fetchTransactions();
    }
  };

  const handleDeleteTransaction = async (transactionId: number) => {
    if (!confirm('Are you sure you want to delete this transaction?')) {
      return;
    }
    
    try {
      await axios.delete(`http://localhost:8000/api/transactions/${transactionId}`);
      
      // Optimistic update - remove from current state
      setTransactions(prev => prev.filter(t => t.id !== transactionId));
      
      invalidateCache();
    } catch (err) {
      console.error('Error deleting transaction:', err);
      alert('Failed to delete transaction');
      fetchTransactions();
    }
  };

  const handleAutoCategorise = async () => {
    try {
      await axios.post('http://localhost:8000/api/auto-categorize');
      invalidateCache();
      fetchTransactions();
      alert('Auto-categorisation completed');
    } catch (err) {
      console.error('Error running auto-categorisation:', err);
      alert('Failed to run auto-categorisation');
    }
  };

  const handleSelectTransaction = (transactionId: number, event: React.MouseEvent) => {
    const newSelected = new Set(selectedTransactionIds);
    
    if (event.ctrlKey || event.metaKey) {
      // Toggle selection with Ctrl/Cmd
      if (newSelected.has(transactionId)) {
        newSelected.delete(transactionId);
      } else {
        newSelected.add(transactionId);
      }
    } else if (event.shiftKey && selectedTransactionIds.size > 0) {
      // Range selection with Shift
      const currentIds = displayTransactions.map(t => t.id);
      const lastSelected = Math.max(...Array.from(selectedTransactionIds));
      const currentIndex = currentIds.indexOf(transactionId);
      const lastIndex = currentIds.indexOf(lastSelected);
      
      const start = Math.min(currentIndex, lastIndex);
      const end = Math.max(currentIndex, lastIndex);
      
      for (let i = start; i <= end; i++) {
        newSelected.add(currentIds[i]);
      }
    } else {
      // Single selection
      newSelected.clear();
      newSelected.add(transactionId);
    }
    
    setSelectedTransactionIds(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedTransactionIds.size === displayTransactions.length) {
      setSelectedTransactionIds(new Set());
    } else {
      setSelectedTransactionIds(new Set(displayTransactions.map(t => t.id)));
    }
  };

  const handleBulkCategoryUpdate = async (categoryId: string) => {
    try {
      // Update all selected transactions
      const promises = Array.from(selectedTransactionIds).map(id =>
        axios.put(`http://localhost:8000/api/transactions/${id}/category`, null, {
          params: { category_id: categoryId }
        })
      );
      
      await Promise.all(promises);
      
      // Optimistic update for all selected transactions
      setTransactions(prev => prev.map(t => 
        selectedTransactionIds.has(t.id)
          ? { ...t, category_id: categoryId }
          : t
      ));
      
      // Clear selection and invalidate cache
      setSelectedTransactionIds(new Set());
      invalidateCache();
    } catch (err) {
      console.error('Error updating transaction categories:', err);
      alert('Failed to update transaction categories');
      fetchTransactions();
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'AUD'
    }).format(value);
  };

  // Handle column sorting
  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  // Sort transactions locally
  const sortTransactions = (transactions: Transaction[]) => {
    if (!sortColumn) return transactions;

    return [...transactions].sort((a, b) => {
      let aValue: any = '';
      let bValue: any = '';

      switch (sortColumn) {
        case 'date':
          aValue = new Date(a.date);
          bValue = new Date(b.date);
          break;
        case 'account':
          aValue = a.account_name || a.account;
          bValue = b.account_name || b.account;
          break;
        case 'description':
          aValue = a.description;
          bValue = b.description;
          break;
        case 'withdrawal':
          aValue = a.withdrawal;
          bValue = b.withdrawal;
          break;
        case 'deposit':
          aValue = a.deposit;
          bValue = b.deposit;
          break;
        case 'category':
          aValue = a.category_name || '';
          bValue = b.category_name || '';
          break;
        default:
          return 0;
      }

      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  };

  const displayTransactions = sortTransactions(transactions);

  const calculateTotals = () => {
    const totalWithdrawals = displayTransactions.reduce((sum, t) => sum + (t.withdrawal || 0), 0);
    const totalDeposits = displayTransactions.reduce((sum, t) => sum + (t.deposit || 0), 0);
    return { totalWithdrawals, totalDeposits };
  };

  const { totalWithdrawals, totalDeposits } = calculateTotals();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-xl">Loading transactions...</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-800">
      {/* Main Content */}
      <div className="flex-1 overflow-hidden flex flex-col">
          {/* Transaction Toolbar */}
          <div className="border-b border-gray-200 dark:border-gray-700 p-4 bg-white dark:bg-gray-800 shadow-sm">
            {error && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                {error}
              </div>
            )}
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200">Transactions</h2>
              <div className="flex space-x-2">
                <button 
                  className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded flex items-center space-x-1"
                  onClick={() => setShowImportDialog(true)}
                >
                  <Upload size={18} />
                  <span>Import</span>
                </button>
              </div>
            </div>

            {/* Filter bar */}
            <div className="flex items-center mb-4">
              <div className="flex bg-gray-100 dark:bg-gray-700 rounded-md mr-4 flex-1">
                <div className="flex items-center px-3 text-gray-500 dark:text-gray-400">
                  <Search size={18} />
                </div>
                <input
                  type="text"
                  placeholder="Search transactions..."
                  className="bg-transparent border-none py-2 px-1 flex-1 focus:outline-none focus:ring-1 focus:ring-indigo-500 rounded-md text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
              <div className="flex space-x-2">
                <button 
                  className="text-gray-600 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 p-2"
                  onClick={() => {
                    setCache(new Map());
                    fetchTransactions();
                  }}
                  title="Refresh transactions"
                >
                  <RefreshCw size={20} />
                </button>
              </div>
            </div>

            {/* Tab filters */}
            <div className="flex border-b border-gray-200 dark:border-gray-700">
              <button 
                className={`px-4 py-2 font-medium ${activeFilter === 'all' ? 'text-indigo-600 border-b-2 border-indigo-600' : 'text-gray-600 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400'}`}
                onClick={() => setActiveFilter('all')}
              >
                All
              </button>
              <button 
                className={`px-4 py-2 font-medium ${activeFilter === 'uncategorised' ? 'text-indigo-600 border-b-2 border-indigo-600' : 'text-gray-600 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400'}`}
                onClick={() => setActiveFilter('uncategorised')}
              >
                Uncategorised
              </button>
              <button 
                className={`px-4 py-2 font-medium ${activeFilter === 'internal' ? 'text-indigo-600 border-b-2 border-indigo-600' : 'text-gray-600 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400'}`}
                onClick={() => setActiveFilter('internal')}
              >
                Internal Transfers
              </button>
              <button 
                className={`px-4 py-2 font-medium ${activeFilter === 'hidden' ? 'text-indigo-600 border-b-2 border-indigo-600' : 'text-gray-600 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400'}`}
                onClick={() => setActiveFilter('hidden')}
              >
                Hidden
              </button>
              
              {/* Selection and Action Buttons */}
              <div className="ml-auto flex items-center space-x-2">
                <button 
                  className="px-3 py-2 text-gray-600 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 font-medium text-sm"
                  onClick={handleSelectAll}
                >
                  {selectedTransactionIds.size > 0 ? 'Unselect All' : 'Select All'}
                </button>
                <button 
                  className={`px-3 py-2 font-medium text-sm flex items-center space-x-1 rounded ${
                    selectedTransactionIds.size > 0 
                      ? 'bg-indigo-600 hover:bg-indigo-700 text-white' 
                      : 'bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                  }`}
                  onClick={() => selectedTransactionIds.size > 0 && setShowBulkCategoryPicker(true)}
                  disabled={selectedTransactionIds.size === 0}
                >
                  <Tag size={14} />
                  <span>Categorise Selected {selectedTransactionIds.size > 0 ? `(${selectedTransactionIds.size})` : ''}</span>
                </button>
                <button 
                  className="px-3 py-2 text-gray-600 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 font-medium text-sm flex items-center space-x-1"
                  onClick={handleAutoCategorise}
                >
                  <Tag size={14} />
                  <span>Auto-Categorise</span>
                </button>
              </div>
            </div>
            
            {/* Account Filter Indicator */}
            {accountFilter && (
              <div className="mt-2 flex items-center space-x-2">
                <span className="text-sm text-gray-600 dark:text-gray-400">Filtered by account:</span>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                  {accountFilter}
                </span>
                <button
                  onClick={() => setAccountFilter('')}
                  className="text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 underline"
                >
                  Clear filter
                </button>
              </div>
            )}

            {/* Category Filter Indicator */}
            {categoryFilter && (
              <div className="mt-2 flex items-center space-x-2">
                <span className="text-sm text-gray-600 dark:text-gray-400">Filtered by category:</span>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  {categoryName || categoryFilter}
                </span>
                <button
                  onClick={() => setCategoryFilter('')}
                  className="text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 underline"
                >
                  Clear filter
                </button>
              </div>
            )}

          </div>
          
          {/* Transaction Table */}
          <div className="overflow-auto flex-1 bg-white dark:bg-gray-800">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th scope="col" className="px-6 py-3 w-12">
                    <input
                      type="checkbox"
                      className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      checked={selectedTransactionIds.size === displayTransactions.length && displayTransactions.length > 0}
                      onChange={handleSelectAll}
                    />
                  </th>
                  <th 
                    scope="col" 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 select-none"
                    onClick={() => handleSort('date')}
                  >
                    <div className="flex items-center space-x-1">
                      <span>Date</span>
                      {sortColumn === 'date' && (
                        sortDirection === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                      )}
                    </div>
                  </th>
                  <th 
                    scope="col" 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 select-none"
                    onClick={() => handleSort('account')}
                  >
                    <div className="flex items-center space-x-1">
                      <span>Account</span>
                      {sortColumn === 'account' && (
                        sortDirection === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                      )}
                    </div>
                  </th>
                  <th 
                    scope="col" 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 select-none"
                    onClick={() => handleSort('description')}
                  >
                    <div className="flex items-center space-x-1">
                      <span>Description</span>
                      {sortColumn === 'description' && (
                        sortDirection === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                      )}
                    </div>
                  </th>
                  <th 
                    scope="col" 
                    className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 select-none"
                    onClick={() => handleSort('withdrawal')}
                  >
                    <div className="flex items-center justify-end space-x-1">
                      <span>Withdrawal</span>
                      {sortColumn === 'withdrawal' && (
                        sortDirection === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                      )}
                    </div>
                  </th>
                  <th 
                    scope="col" 
                    className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 select-none"
                    onClick={() => handleSort('deposit')}
                  >
                    <div className="flex items-center justify-end space-x-1">
                      <span>Deposit</span>
                      {sortColumn === 'deposit' && (
                        sortDirection === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                      )}
                    </div>
                  </th>
                  <th 
                    scope="col" 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 select-none"
                    onClick={() => handleSort('category')}
                  >
                    <div className="flex items-center space-x-1">
                      <span>Category</span>
                      {sortColumn === 'category' && (
                        sortDirection === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                      )}
                    </div>
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Tax Type</th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {displayTransactions.map((transaction) => (
                  <tr 
                    key={transaction.id} 
                    className={`hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer ${selectedTransactionIds.has(transaction.id) ? 'bg-indigo-50 dark:bg-indigo-900' : ''}`}
                    onClick={(e) => handleSelectTransaction(transaction.id, e)}
                    onDoubleClick={() => {
                      setSelectedTransactionId(transaction.id);
                      setShowCategoryPicker(true);
                    }}
                  >
                    <td className="px-6 py-3 whitespace-nowrap">
                      <input
                        type="checkbox"
                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                        checked={selectedTransactionIds.has(transaction.id)}
                        onChange={() => {}} // Handled by row click
                        onClick={(e) => e.stopPropagation()}
                      />
                    </td>
                    <td className="px-6 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">{transaction.date}</td>
                    <td className="px-6 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">{transaction.account_name || transaction.account}</td>
                    <td className="px-6 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">{transaction.description}</td>
                    <td className="px-6 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100 text-right">
                      {transaction.withdrawal > 0 ? formatCurrency(transaction.withdrawal) : ''}
                    </td>
                    <td className="px-6 py-3 whitespace-nowrap text-sm text-green-600 text-right">
                      {transaction.deposit > 0 ? formatCurrency(transaction.deposit) : ''}
                    </td>
                    <td className="px-6 py-3 whitespace-nowrap text-sm">
                      <span 
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          transaction.is_internal_transfer 
                            ? 'bg-purple-100 text-purple-800' 
                            : transaction.is_hidden
                              ? 'bg-orange-100 text-orange-800'
                              : transaction.category_name?.startsWith('Income') 
                                ? 'bg-green-100 text-green-800'
                                : transaction.category_name
                                  ? 'bg-blue-100 text-blue-800'
                                  : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {transaction.is_internal_transfer 
                          ? 'Internal Transfer' 
                          : transaction.is_hidden
                            ? 'Hidden'
                            : transaction.category_name || 'Uncategorised'}
                      </span>
                    </td>
                    <td className="px-6 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">{transaction.tax_type}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination and Status bar */}
          <div className="border-t border-gray-200 dark:border-gray-700 p-3 text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-900">
            {/* Pagination Controls */}
            <div className="flex justify-between items-center mb-2">
              <div className="flex items-center space-x-4">
                <span>
                  Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, totalCount)} of {totalCount} transactions
                </span>
                {totalCount > pageSize && (
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setCurrentPage(1)}
                      disabled={currentPage === 1}
                      className="px-2 py-1 border border-gray-300 dark:border-gray-600 rounded text-xs disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      First
                    </button>
                    <button
                      onClick={() => setCurrentPage(currentPage - 1)}
                      disabled={currentPage === 1}
                      className="px-2 py-1 border border-gray-300 dark:border-gray-600 rounded text-xs disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      Previous
                    </button>
                    <span className="text-xs">
                      Page {currentPage} of {totalPages}
                    </span>
                    <button
                      onClick={() => setCurrentPage(currentPage + 1)}
                      disabled={currentPage === totalPages}
                      className="px-2 py-1 border border-gray-300 dark:border-gray-600 rounded text-xs disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      Next
                    </button>
                    <button
                      onClick={() => setCurrentPage(totalPages)}
                      disabled={currentPage === totalPages}
                      className="px-2 py-1 border border-gray-300 dark:border-gray-600 rounded text-xs disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      Last
                    </button>
                  </div>
                )}
              </div>
              <div>
                Total withdrawals: {formatCurrency(totalWithdrawals)} • Total deposits: {formatCurrency(totalDeposits)}
              </div>
            </div>
          </div>
      </div>

      {/* Import Dialog */}
      <ImportDialog
        isOpen={showImportDialog}
        onClose={() => setShowImportDialog(false)}
        onImportComplete={() => {
          invalidateCache();
          fetchTransactions();
        }}
      />

      {/* Category Picker Dialog */}
      <CategoryPickerDialog
        isOpen={showCategoryPicker}
        onClose={() => {
          setShowCategoryPicker(false);
          setSelectedTransactionId(null);
        }}
        onCategorySelect={(categoryId) => {
          if (selectedTransactionId) {
            handleCategoryUpdate(selectedTransactionId, categoryId);
          }
          setShowCategoryPicker(false);
          setSelectedTransactionId(null);
        }}
        onMarkAsInternalTransfer={() => {
          if (selectedTransactionId) {
            handleToggleInternalTransfer(selectedTransactionId);
          }
          setSelectedTransactionId(null);
        }}
        onMarkAsHidden={() => {
          if (selectedTransactionId) {
            handleToggleHidden(selectedTransactionId);
          }
          setSelectedTransactionId(null);
        }}
        currentCategoryId={selectedTransactionId ? 
          transactions.find(t => t.id === selectedTransactionId)?.category_id : 
          undefined
        }
      />

      {/* Bulk Category Picker Dialog */}
      <CategoryPickerDialog
        isOpen={showBulkCategoryPicker}
        onClose={() => {
          setShowBulkCategoryPicker(false);
        }}
        onCategorySelect={(categoryId) => {
          handleBulkCategoryUpdate(categoryId);
          setShowBulkCategoryPicker(false);
        }}
      />
    </div>
  );
};

export default TransactionViewStandalone;