import React, { useState, useEffect } from 'react';
import { X, Plus, Trash2 } from 'lucide-react';
import axios from 'axios';
import CategoryPickerDialog from './CategoryPickerDialog';

interface AutoCategorizeRule {
  id?: number;
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

interface Category {
  id: string;
  name: string;
  category_type: string;
}

interface BankAccount {
  id: string;
  name: string;
}

interface AddRuleDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onRuleAdded: () => void;
  editingRule?: AutoCategorizeRule | null;
}

const AddRuleDialog: React.FC<AddRuleDialogProps> = ({ 
  isOpen, 
  onClose, 
  onRuleAdded,
  editingRule 
}) => {
  const [formData, setFormData] = useState<AutoCategorizeRule>({
    category_id: '',
    amount_operator: '',
    amount_value: undefined,
    amount_value2: undefined,
    account_id: '',
    date_range: '',
    apply_future: true,
    descriptions: [{ description_text: '', case_sensitive: false, sequence: 0 }]
  });

  const [categories, setCategories] = useState<Category[]>([]);
  const [accounts, setAccounts] = useState<BankAccount[]>([]);
  const [loading, setLoading] = useState(false);
  const [showCategoryPicker, setShowCategoryPicker] = useState(false);
  const [isInternalTransfer, setIsInternalTransfer] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchCategories();
      fetchAccounts();
      
      if (editingRule) {
        setFormData(editingRule);
        setIsInternalTransfer(editingRule.category_id === '0');
      } else {
        setFormData({
          category_id: '',
          amount_operator: '',
          amount_value: undefined,
          amount_value2: undefined,
          account_id: '',
          date_range: '',
          apply_future: true,
          descriptions: [{ description_text: '', case_sensitive: false, sequence: 0 }]
        });
        setIsInternalTransfer(false);
      }
    }
  }, [isOpen, editingRule]);

  const fetchCategories = async () => {
    try {
      const response = await axios.get<Category[]>('http://localhost:8000/api/categories');
      // Filter to only transaction categories (not groups)
      const transactionCategories = response.data.filter(cat => cat.category_type === 'transaction');
      setCategories(transactionCategories);
    } catch (err) {
      console.error('Error fetching categories:', err);
    }
  };

  const fetchAccounts = async () => {
    try {
      const response = await axios.get<BankAccount[]>('http://localhost:8000/api/accounts');
      setAccounts(response.data);
    } catch (err) {
      console.error('Error fetching accounts:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.category_id && !isInternalTransfer) {
      alert('Please select a category or choose Internal Transfer');
      return;
    }

    if (formData.descriptions.length === 0 || !formData.descriptions[0].description_text) {
      alert('Please add at least one description criteria');
      return;
    }

    try {
      setLoading(true);
      
      const payload = {
        category_id: isInternalTransfer ? '0' : formData.category_id,
        descriptions: formData.descriptions.filter(d => d.description_text.trim()),
        amount_operator: formData.amount_operator || null,
        amount_value: formData.amount_value || null,
        amount_value2: formData.amount_value2 || null,
        account_id: formData.account_id || null,
        date_range: formData.date_range || null,
        apply_future: formData.apply_future
      };

      if (editingRule) {
        await axios.put(`http://localhost:8000/api/auto-categorisation/rules/${editingRule.id}`, payload);
      } else {
        await axios.post('http://localhost:8000/api/auto-categorisation/rules', payload);
      }

      onRuleAdded();
      onClose();
    } catch (err) {
      console.error('Error saving rule:', err);
      alert('Failed to save rule');
    } finally {
      setLoading(false);
    }
  };

  const addDescriptionCriteria = () => {
    setFormData({
      ...formData,
      descriptions: [
        ...formData.descriptions,
        { 
          operator: 'AND',
          description_text: '', 
          case_sensitive: false, 
          sequence: formData.descriptions.length 
        }
      ]
    });
  };

  const removeDescriptionCriteria = (index: number) => {
    if (formData.descriptions.length > 1) {
      const newDescriptions = formData.descriptions.filter((_, i) => i !== index);
      setFormData({
        ...formData,
        descriptions: newDescriptions.map((desc, i) => ({
          ...desc,
          sequence: i,
          operator: i === 0 ? undefined : desc.operator
        }))
      });
    }
  };

  const updateDescription = (index: number, field: string, value: any) => {
    const newDescriptions = [...formData.descriptions];
    newDescriptions[index] = { ...newDescriptions[index], [field]: value };
    setFormData({ ...formData, descriptions: newDescriptions });
  };

  const getSelectedCategoryName = () => {
    if (isInternalTransfer) return 'Internal Transfer';
    const category = categories.find(c => c.id === formData.category_id);
    return category?.name || formData.category_id;
  };

  const handleInternalTransferChange = (checked: boolean) => {
    setIsInternalTransfer(checked);
    if (checked) {
      setFormData({ ...formData, category_id: '0' });
    } else {
      setFormData({ ...formData, category_id: '' });
    }
  };

  if (!isOpen) return null;

  return (
    <>
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b">
            <h3 className="text-lg font-semibold">
              {editingRule ? 'Edit Auto-Categorisation Rule' : 'Add Auto-Categorisation Rule'}
            </h3>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <X size={20} />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {/* Category Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Target Category *
              </label>
              
              {/* Internal Transfer Radio Button */}
              <div className="mb-3">
                <label className="flex items-center space-x-2">
                  <input
                    type="radio"
                    name="category-type"
                    checked={isInternalTransfer}
                    onChange={(e) => handleInternalTransferChange(e.target.checked)}
                  />
                  <span className="text-sm font-medium text-gray-700">
                    Internal Transfer
                  </span>
                </label>
                <p className="text-xs text-gray-500 ml-6">
                  Mark transactions as internal transfers between accounts
                </p>
              </div>
              
              {/* Category Selection Radio Button */}
              <div className="mb-3">
                <label className="flex items-center space-x-2">
                  <input
                    type="radio"
                    name="category-type"
                    checked={!isInternalTransfer}
                    onChange={(e) => handleInternalTransferChange(!e.target.checked)}
                  />
                  <span className="text-sm font-medium text-gray-700">
                    Category
                  </span>
                </label>
              </div>
              
              {/* Category Picker */}
              {!isInternalTransfer && (
                <div className="flex space-x-2">
                  <input
                    type="text"
                    className="flex-1 border border-gray-300 rounded-md px-3 py-2 bg-gray-50"
                    value={getSelectedCategoryName()}
                    readOnly
                    placeholder="Click to select category"
                  />
                  <button
                    type="button"
                    className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded"
                    onClick={() => setShowCategoryPicker(true)}
                  >
                    Select
                  </button>
                </div>
              )}
            </div>

            {/* Description Criteria */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description Criteria *
              </label>
              <div className="space-y-3">
                {formData.descriptions.map((desc, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    {index > 0 && (
                      <select
                        className="w-20 border border-gray-300 rounded-md px-2 py-2"
                        value={desc.operator || 'AND'}
                        onChange={(e) => updateDescription(index, 'operator', e.target.value)}
                      >
                        <option value="AND">AND</option>
                        <option value="OR">OR</option>
                      </select>
                    )}
                    <input
                      type="text"
                      className="flex-1 border border-gray-300 rounded-md px-3 py-2"
                      placeholder="Text to match in transaction description"
                      value={desc.description_text}
                      onChange={(e) => updateDescription(index, 'description_text', e.target.value)}
                      required
                    />
                    <label className="flex items-center space-x-1">
                      <input
                        type="checkbox"
                        checked={desc.case_sensitive}
                        onChange={(e) => updateDescription(index, 'case_sensitive', e.target.checked)}
                      />
                      <span className="text-sm">Case sensitive</span>
                    </label>
                    {formData.descriptions.length > 1 && (
                      <button
                        type="button"
                        className="text-red-600 hover:text-red-800"
                        onClick={() => removeDescriptionCriteria(index)}
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </div>
                ))}
                <button
                  type="button"
                  className="flex items-center space-x-1 text-indigo-600 hover:text-indigo-800"
                  onClick={addDescriptionCriteria}
                >
                  <Plus size={16} />
                  <span>Add description criteria</span>
                </button>
              </div>
            </div>

            {/* Amount Criteria */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Amount Criteria (Optional)
              </label>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <select
                  className="border border-gray-300 rounded-md px-3 py-2"
                  value={formData.amount_operator || ''}
                  onChange={(e) => setFormData({ ...formData, amount_operator: e.target.value })}
                >
                  <option value="">Any amount</option>
                  <option value="equals">Equals</option>
                  <option value="greater_than">Greater than</option>
                  <option value="less_than">Less than</option>
                  <option value="between">Between</option>
                </select>
                <input
                  type="number"
                  step="0.01"
                  className="border border-gray-300 rounded-md px-3 py-2"
                  placeholder="Amount"
                  value={formData.amount_value || ''}
                  onChange={(e) => setFormData({ ...formData, amount_value: parseFloat(e.target.value) || undefined })}
                  disabled={!formData.amount_operator}
                />
                {formData.amount_operator === 'between' && (
                  <input
                    type="number"
                    step="0.01"
                    className="border border-gray-300 rounded-md px-3 py-2"
                    placeholder="Upper amount"
                    value={formData.amount_value2 || ''}
                    onChange={(e) => setFormData({ ...formData, amount_value2: parseFloat(e.target.value) || undefined })}
                  />
                )}
              </div>
            </div>

            {/* Account Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Account Filter (Optional)
              </label>
              <select
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                value={formData.account_id || ''}
                onChange={(e) => setFormData({ ...formData, account_id: e.target.value })}
              >
                <option value="">Any account</option>
                {accounts.map(account => (
                  <option key={account.id} value={account.id}>{account.name}</option>
                ))}
              </select>
            </div>

            {/* Apply to Future */}
            <div>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={formData.apply_future}
                  onChange={(e) => setFormData({ ...formData, apply_future: e.target.checked })}
                />
                <span className="text-sm font-medium text-gray-700">
                  Apply to future imports (recommended)
                </span>
              </label>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end space-x-3 pt-4 border-t">
              <button
                type="button"
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
                onClick={onClose}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded disabled:bg-gray-400"
                disabled={loading}
              >
                {loading ? 'Saving...' : (editingRule ? 'Update Rule' : 'Create Rule')}
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Category Picker Dialog */}
      <CategoryPickerDialog
        isOpen={showCategoryPicker}
        onClose={() => setShowCategoryPicker(false)}
        onCategorySelect={(categoryId) => {
          setFormData({ ...formData, category_id: categoryId });
          setShowCategoryPicker(false);
        }}
        currentCategoryId={formData.category_id}
      />
    </>
  );
};

export default AddRuleDialog;