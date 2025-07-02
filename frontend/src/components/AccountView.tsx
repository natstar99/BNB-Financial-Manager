import React, { useState, useEffect } from 'react';
import { Plus, Edit, Trash2, CreditCard, Building, DollarSign } from 'lucide-react';
import axios from 'axios';

interface BankAccount {
  id: string;
  name: string;
  account_number: string;
  bsb: string;
  bank_name: string;
  current_balance: number;
  last_import_date?: string;
  notes: string;
}

const AccountView: React.FC = () => {
  const [accounts, setAccounts] = useState<BankAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [newAccount, setNewAccount] = useState({
    name: '',
    account_number: '',
    bsb: '',
    bank_name: '',
    notes: ''
  });

  // Sample data matching existing structure
  const sampleAccounts: BankAccount[] = [
    {
      id: "3.1",
      name: "Westpac Savings",
      account_number: "123456789",
      bsb: "032-001",
      bank_name: "Westpac Banking Corporation",
      current_balance: 5234.67,
      last_import_date: "2025-05-01",
      notes: "Primary savings account"
    },
    {
      id: "3.2",
      name: "NAB Business",
      account_number: "987654321",
      bsb: "084-123",
      bank_name: "National Australia Bank",
      current_balance: 12450.33,
      last_import_date: "2025-04-30",
      notes: "Business transaction account"
    },
    {
      id: "3.3",
      name: "NAB Savings",
      account_number: "456789123",
      bsb: "084-123",
      bank_name: "National Australia Bank",
      current_balance: 1875.20,
      last_import_date: "2025-04-28",
      notes: "Secondary savings account"
    }
  ];

  useEffect(() => {
    fetchAccounts();
  }, []);

  const fetchAccounts = async () => {
    try {
      const response = await axios.get<BankAccount[]>('http://localhost:8000/api/accounts');
      setAccounts(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch accounts, showing sample data');
      console.error('Error fetching accounts:', err);
      // Fall back to sample data
      setAccounts(sampleAccounts);
    } finally {
      setLoading(false);
    }
  };

  const handleAddAccount = async () => {
    if (!newAccount.name.trim() || !newAccount.account_number.trim() || !newAccount.bsb.trim() || !newAccount.bank_name.trim()) {
      alert('Please fill in all required fields');
      return;
    }

    try {
      await axios.post('http://localhost:8000/api/accounts', null, {
        params: {
          name: newAccount.name,
          account_number: newAccount.account_number,
          bsb: newAccount.bsb,
          bank_name: newAccount.bank_name,
          notes: newAccount.notes
        }
      });

      // Refresh accounts
      fetchAccounts();

      // Reset form
      setNewAccount({
        name: '',
        account_number: '',
        bsb: '',
        bank_name: '',
        notes: ''
      });
      setShowAddDialog(false);
    } catch (err) {
      console.error('Error creating account:', err);
      alert('Failed to create account');
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'AUD'
    }).format(value);
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString('en-AU');
  };

  const getTotalBalance = () => {
    return accounts.reduce((sum, account) => sum + account.current_balance, 0);
  };

  const getBankLogo = (bankName: string) => {
    if (bankName.toLowerCase().includes('westpac')) {
      return <div className="w-8 h-8 bg-red-500 rounded flex items-center justify-center text-white text-xs font-bold">W</div>;
    }
    if (bankName.toLowerCase().includes('nab')) {
      return <div className="w-8 h-8 bg-red-600 rounded flex items-center justify-center text-white text-xs font-bold">N</div>;
    }
    if (bankName.toLowerCase().includes('anz')) {
      return <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center text-white text-xs font-bold">A</div>;
    }
    if (bankName.toLowerCase().includes('cba') || bankName.toLowerCase().includes('commonwealth')) {
      return <div className="w-8 h-8 bg-yellow-500 rounded flex items-center justify-center text-white text-xs font-bold">C</div>;
    }
    return <div className="w-8 h-8 bg-gray-500 rounded flex items-center justify-center text-white text-xs font-bold"><Building size={16} /></div>;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-xl">Loading accounts...</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200">Bank Accounts</h2>
          <div className="flex space-x-2">
            <button 
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded flex items-center space-x-1"
              onClick={() => setShowAddDialog(true)}
            >
              <Plus size={18} />
              <span>Add Account</span>
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-indigo-50 dark:bg-indigo-900 rounded-lg p-4">
            <div className="flex items-center">
              <div className="p-2 bg-indigo-100 dark:bg-indigo-800 rounded-lg">
                <CreditCard className="w-6 h-6 text-indigo-600" />
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-indigo-600 dark:text-indigo-300">Total Accounts</p>
                <p className="text-2xl font-semibold text-indigo-900 dark:text-indigo-100">{accounts.length}</p>
              </div>
            </div>
          </div>

          <div className="bg-green-50 dark:bg-green-900 rounded-lg p-4">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 dark:bg-green-800 rounded-lg">
                <DollarSign className="w-6 h-6 text-green-600" />
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-green-600 dark:text-green-300">Total Balance</p>
                <p className="text-2xl font-semibold text-green-900 dark:text-green-100">{formatCurrency(getTotalBalance())}</p>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
            <div className="flex items-center">
              <div className="p-2 bg-gray-100 dark:bg-gray-600 rounded-lg">
                <Building className="w-6 h-6 text-gray-600 dark:text-gray-400" />
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Active Banks</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                  {new Set(accounts.map(a => a.bank_name)).size}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Account Cards */}
      <div className="flex-1 overflow-auto p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {accounts.map((account) => (
            <div key={account.id} className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow">
              <div className="p-6">
                {/* Account Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    {getBankLogo(account.bank_name)}
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{account.name}</h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400">{account.bank_name}</p>
                    </div>
                  </div>
                  <button className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300">
                    <Edit size={16} />
                  </button>
                </div>

                {/* Account Details */}
                <div className="space-y-3">
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">Account Number</p>
                    <p className="text-sm font-mono text-gray-900 dark:text-gray-100">{account.account_number}</p>
                  </div>

                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">BSB</p>
                    <p className="text-sm font-mono text-gray-900 dark:text-gray-100">{account.bsb}</p>
                  </div>

                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">Current Balance</p>
                    <p className={`text-lg font-semibold ${account.current_balance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatCurrency(account.current_balance)}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">Last Import</p>
                    <p className="text-sm text-gray-900 dark:text-gray-100">{formatDate(account.last_import_date)}</p>
                  </div>

                  {account.notes && (
                    <div>
                      <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">Notes</p>
                      <p className="text-sm text-gray-900 dark:text-gray-100">{account.notes}</p>
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex space-x-2 mt-4 pt-4 border-t border-gray-100 dark:border-gray-700">
                  <button className="flex-1 bg-indigo-50 text-indigo-600 py-2 px-3 rounded text-sm font-medium hover:bg-indigo-100">
                    View Transactions
                  </button>
                  <button className="bg-gray-50 dark:bg-gray-700 text-gray-600 dark:text-gray-300 py-2 px-3 rounded text-sm hover:bg-gray-100 dark:hover:bg-gray-600">
                    <Edit size={16} />
                  </button>
                  <button className="bg-red-50 text-red-600 py-2 px-3 rounded text-sm hover:bg-red-100">
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Add Account Dialog */}
      {showAddDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-96 max-w-full mx-4 border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold mb-4">Add New Bank Account</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Account Name *
                </label>
                <input
                  type="text"
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  value={newAccount.name}
                  onChange={(e) => setNewAccount({...newAccount, name: e.target.value})}
                  placeholder="e.g., My Savings Account"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Bank Name *
                </label>
                <input
                  type="text"
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  value={newAccount.bank_name}
                  onChange={(e) => setNewAccount({...newAccount, bank_name: e.target.value})}
                  placeholder="e.g., Westpac Banking Corporation"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    BSB *
                  </label>
                  <input
                    type="text"
                    className="w-full border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                    value={newAccount.bsb}
                    onChange={(e) => setNewAccount({...newAccount, bsb: e.target.value})}
                    placeholder="123-456"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Account Number *
                  </label>
                  <input
                    type="text"
                    className="w-full border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                    value={newAccount.account_number}
                    onChange={(e) => setNewAccount({...newAccount, account_number: e.target.value})}
                    placeholder="123456789"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Notes
                </label>
                <textarea
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  rows={3}
                  value={newAccount.notes}
                  onChange={(e) => setNewAccount({...newAccount, notes: e.target.value})}
                  placeholder="Optional notes about this account"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                onClick={() => setShowAddDialog(false)}
              >
                Cancel
              </button>
              <button
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded"
                onClick={handleAddAccount}
              >
                Add Account
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AccountView;