import React, { useState, useEffect } from 'react';
import { Plus, Edit, Trash2, Play, Settings, Search } from 'lucide-react';
import axios from 'axios';
import AddRuleDialog from './dialogs/AddRuleDialog';

interface AutoCategorizeRule {
  id: number;
  category_id: string;
  category_name?: string;
  amount_operator?: string;
  amount_value?: number;
  amount_value2?: number;
  account_id?: string;
  account_name?: string;
  date_range?: string;
  apply_future: boolean;
  descriptions: Array<{
    operator?: string;
    description_text: string;
    case_sensitive: boolean;
    sequence: number;
  }>;
}

const AutoCategorizeRulesView: React.FC = () => {
  const [rules, setRules] = useState<AutoCategorizeRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [editingRule, setEditingRule] = useState<AutoCategorizeRule | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchRules();
  }, []);

  const fetchRules = async () => {
    try {
      setLoading(true);
      const response = await axios.get<AutoCategorizeRule[]>('http://localhost:8000/api/auto-categorisation/rules');
      setRules(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch auto-categorisation rules');
      console.error('Error fetching rules:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteRule = async (ruleId: number) => {
    if (!confirm('Are you sure you want to delete this rule?')) {
      return;
    }

    try {
      await axios.delete(`http://localhost:8000/api/auto-categorisation/rules/${ruleId}`);
      fetchRules(); // Refresh the list
    } catch (err) {
      console.error('Error deleting rule:', err);
      alert('Failed to delete rule');
    }
  };

  const handleRunAutoCategorisation = async () => {
    try {
      const response = await axios.post('http://localhost:8000/api/auto-categorize');
      alert(response.data.message);
    } catch (err) {
      console.error('Error running auto-categorisation:', err);
      alert('Failed to run auto-categorisation');
    }
  };

  const formatAmountCriteria = (rule: AutoCategorizeRule) => {
    if (!rule.amount_operator || !rule.amount_value) return '';
    
    const formatCurrency = (value: number) => {
      return new Intl.NumberFormat('en-AU', {
        style: 'currency',
        currency: 'AUD'
      }).format(value);
    };

    switch (rule.amount_operator) {
      case 'equals':
        return `Amount = ${formatCurrency(rule.amount_value)}`;
      case 'greater_than':
        return `Amount > ${formatCurrency(rule.amount_value)}`;
      case 'less_than':
        return `Amount < ${formatCurrency(rule.amount_value)}`;
      case 'between':
        return `Amount between ${formatCurrency(rule.amount_value)} and ${formatCurrency(rule.amount_value2 || 0)}`;
      default:
        return '';
    }
  };

  const formatDescriptions = (descriptions: AutoCategorizeRule['descriptions']) => {
    if (descriptions.length === 0) return 'No description criteria';
    
    return descriptions.map((desc, index) => {
      const prefix = index === 0 ? '' : (desc.operator || 'AND');
      const caseNote = desc.case_sensitive ? '' : ' (case-insensitive)';
      return `${prefix} "${desc.description_text}"${caseNote}`;
    }).join(' ');
  };

  const filteredRules = rules
    .filter(rule => {
      if (!searchTerm) return true;
      const searchLower = searchTerm.toLowerCase();
      const displayName = rule.category_id === '0' ? 'Internal Transfer' : (rule.category_name || rule.category_id);
      return (
        displayName.toLowerCase().includes(searchLower) ||
        rule.account_name?.toLowerCase().includes(searchLower) ||
        rule.descriptions.some(desc => desc.description_text.toLowerCase().includes(searchLower))
      );
    })
    .sort((a, b) => {
      const aName = a.category_id === '0' ? 'Internal Transfer' : (a.category_name || a.category_id);
      const bName = b.category_id === '0' ? 'Internal Transfer' : (b.category_name || b.category_id);
      return aName.localeCompare(bName);
    });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-xl">Loading auto-categorisation rules...</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-800">
      {/* Header */}
      <div className="border-b border-gray-200 dark:border-gray-700 p-4 bg-white dark:bg-gray-800 shadow-sm">
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}
        
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200">Auto-Categorisation Rules</h2>
          <div className="flex space-x-2">
            <button 
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded flex items-center space-x-1"
              onClick={handleRunAutoCategorisation}
            >
              <Play size={18} />
              <span>Run All Rules</span>
            </button>
            <button 
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded flex items-center space-x-1"
              onClick={() => setShowAddDialog(true)}
            >
              <Plus size={18} />
              <span>Add Rule</span>
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="flex items-center mb-4">
          <div className="flex bg-gray-100 dark:bg-gray-700 rounded-md mr-4 flex-1">
            <div className="flex items-center px-3 text-gray-500 dark:text-gray-400">
              <Search size={18} />
            </div>
            <input
              type="text"
              placeholder="Search rules by category, account, or description..."
              className="bg-transparent border-none py-2 px-1 flex-1 focus:outline-none focus:ring-1 focus:ring-indigo-500 rounded-md text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-indigo-50 dark:bg-indigo-900 rounded-lg p-4">
            <div className="flex items-center">
              <div className="p-2 bg-indigo-100 dark:bg-indigo-800 rounded-lg">
                <Settings className="w-6 h-6 text-indigo-600" />
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-indigo-600 dark:text-indigo-300">Total Rules</p>
                <p className="text-2xl font-semibold text-indigo-900 dark:text-indigo-100">{rules.length}</p>
              </div>
            </div>
          </div>

          <div className="bg-green-50 dark:bg-green-900 rounded-lg p-4">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 dark:bg-green-800 rounded-lg">
                <Play className="w-6 h-6 text-green-600" />
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-green-600 dark:text-green-300">Active Rules</p>
                <p className="text-2xl font-semibold text-green-900 dark:text-green-100">
                  {rules.filter(r => r.apply_future).length}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-blue-50 dark:bg-blue-900 rounded-lg p-4">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 dark:bg-blue-800 rounded-lg">
                <Search className="w-6 h-6 text-blue-600" />
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-blue-600 dark:text-blue-300">Showing</p>
                <p className="text-2xl font-semibold text-blue-900 dark:text-blue-100">{filteredRules.length}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Rules Table */}
      <div className="flex-1 overflow-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-900">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Category
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Description Criteria
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Amount Criteria
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Account
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Status
              </th>
              <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {filteredRules.map((rule) => (
              <tr key={rule.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {rule.category_id === '0' ? 'Internal Transfer' : (rule.category_name || rule.category_id)}
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm text-gray-900 dark:text-gray-100 max-w-xs truncate" title={formatDescriptions(rule.descriptions)}>
                    {formatDescriptions(rule.descriptions)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900 dark:text-gray-100">
                    {formatAmountCriteria(rule) || 'Any amount'}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900 dark:text-gray-100">
                    {rule.account_name || 'Any account'}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    rule.apply_future 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {rule.apply_future ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                  <button 
                    className="text-indigo-600 hover:text-indigo-900"
                    onClick={() => {
                      setEditingRule(rule);
                      setShowAddDialog(true);
                    }}
                  >
                    <Edit size={16} />
                  </button>
                  <button 
                    className="text-red-600 hover:text-red-900"
                    onClick={() => handleDeleteRule(rule.id)}
                  >
                    <Trash2 size={16} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredRules.length === 0 && !loading && (
          <div className="text-center py-8">
            <div className="text-gray-500">
              {searchTerm ? 'No rules match your search.' : 'No auto-categorisation rules found.'}
            </div>
            {!searchTerm && (
              <button 
                className="mt-2 text-indigo-600 hover:text-indigo-800"
                onClick={() => setShowAddDialog(true)}
              >
                Create your first rule
              </button>
            )}
          </div>
        )}
      </div>

      {/* Add/Edit Rule Dialog */}
      <AddRuleDialog
        isOpen={showAddDialog}
        onClose={() => {
          setShowAddDialog(false);
          setEditingRule(null);
        }}
        onRuleAdded={() => {
          fetchRules();
          setShowAddDialog(false);
          setEditingRule(null);
        }}
        editingRule={editingRule}
      />
    </div>
  );
};

export default AutoCategorizeRulesView;