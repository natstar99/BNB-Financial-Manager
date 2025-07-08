import React, { useState, useEffect } from 'react';
import { Plus, FolderOpen, Folder, ChevronRight, ChevronDown } from 'lucide-react';
import axios from 'axios';

interface Category {
  id: string;
  name: string;
  parent_id?: string;
  category_type: string;
  tax_type?: string;
  is_bank_account: boolean;
  children?: Category[];
  expanded?: boolean;
}

interface CategoryViewProps {
  onNavigateToAccount?: (accountId: string) => void;
  onNavigateToCategory?: (categoryId: string) => void;
}

const CategoryView: React.FC<CategoryViewProps> = ({ onNavigateToAccount, onNavigateToCategory }) => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState('');
  const [newCategoryParent, setNewCategoryParent] = useState('');
  const [newCategoryType, setNewCategoryType] = useState('transaction');
  const [newTaxType, setNewTaxType] = useState('');

  // Sample data matching the existing structure
  const sampleCategories: Category[] = [
    {
      id: "1",
      name: "Income",
      parent_id: undefined,
      category_type: "group",
      tax_type: undefined,
      is_bank_account: false,
      expanded: true,
      children: [
        {
          id: "1.1",
          name: "Salary",
          parent_id: "1",
          category_type: "transaction",
          tax_type: "GST",
          is_bank_account: false
        },
        {
          id: "1.2",
          name: "Freelance",
          parent_id: "1",
          category_type: "transaction",
          tax_type: "GST",
          is_bank_account: false
        },
        {
          id: "1.3",
          name: "Government",
          parent_id: "1",
          category_type: "group",
          tax_type: undefined,
          is_bank_account: false,
          expanded: false,
          children: [
            {
              id: "1.3.1",
              name: "Medicare",
              parent_id: "1.3",
              category_type: "transaction",
              tax_type: "FRE",
              is_bank_account: false
            }
          ]
        }
      ]
    },
    {
      id: "2",
      name: "Expenses",
      parent_id: undefined,
      category_type: "group",
      tax_type: undefined,
      is_bank_account: false,
      expanded: true,
      children: [
        {
          id: "2.1",
          name: "Food",
          parent_id: "2",
          category_type: "group",
          tax_type: undefined,
          is_bank_account: false,
          expanded: true,
          children: [
            {
              id: "2.1.1",
              name: "Groceries",
              parent_id: "2.1",
              category_type: "transaction",
              tax_type: "GST",
              is_bank_account: false
            },
            {
              id: "2.1.2",
              name: "Dining Out",
              parent_id: "2.1",
              category_type: "transaction",
              tax_type: "GST",
              is_bank_account: false
            }
          ]
        },
        {
          id: "2.2",
          name: "Utilities",
          parent_id: "2",
          category_type: "group",
          tax_type: undefined,
          is_bank_account: false,
          expanded: false,
          children: [
            {
              id: "2.2.1",
              name: "Electricity",
              parent_id: "2.2",
              category_type: "transaction",
              tax_type: "GST",
              is_bank_account: false
            },
            {
              id: "2.2.2",
              name: "Water",
              parent_id: "2.2",
              category_type: "transaction",
              tax_type: "GST",
              is_bank_account: false
            }
          ]
        },
        {
          id: "2.3",
          name: "Business",
          parent_id: "2",
          category_type: "group",
          tax_type: undefined,
          is_bank_account: false,
          expanded: false,
          children: [
            {
              id: "2.3.1",
              name: "Supplies",
              parent_id: "2.3",
              category_type: "transaction",
              tax_type: "GST",
              is_bank_account: false
            }
          ]
        }
      ]
    },
    {
      id: "3",
      name: "Bank Accounts",
      parent_id: undefined,
      category_type: "group",
      tax_type: undefined,
      is_bank_account: false,
      expanded: true,
      children: [
        {
          id: "3.1",
          name: "Westpac Savings",
          parent_id: "3",
          category_type: "transaction",
          tax_type: undefined,
          is_bank_account: true
        },
        {
          id: "3.2",
          name: "NAB Business",
          parent_id: "3",
          category_type: "transaction",
          tax_type: undefined,
          is_bank_account: true
        }
      ]
    }
  ];

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    try {
      const response = await axios.get<Category[]>('http://localhost:8000/api/categories');
      // Build tree structure from flat list
      const categoryMap = new Map<string, Category>();
      const rootCategories: Category[] = [];

      // First pass: create all category objects
      response.data.forEach(cat => {
        categoryMap.set(cat.id, { ...cat, children: [], expanded: false });
      });

      // Second pass: build tree structure
      response.data.forEach(cat => {
        const category = categoryMap.get(cat.id)!;
        if (cat.parent_id) {
          const parent = categoryMap.get(cat.parent_id);
          if (parent) {
            parent.children = parent.children || [];
            parent.children.push(category);
          }
        } else {
          rootCategories.push(category);
        }
      });

      setCategories(rootCategories);
      setError(null);
    } catch (err) {
      setError('Failed to fetch categories');
      console.error('Error fetching categories:', err);
      // Fall back to sample data
      setCategories(sampleCategories);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpanded = (categoryId: string) => {
    const updateExpanded = (cats: Category[]): Category[] => {
      return cats.map(cat => {
        if (cat.id === categoryId) {
          return { ...cat, expanded: !cat.expanded };
        }
        if (cat.children) {
          return { ...cat, children: updateExpanded(cat.children) };
        }
        return cat;
      });
    };
    setCategories(updateExpanded(categories));
  };

  const handleAddCategory = async () => {
    if (!newCategoryName.trim()) return;

    try {
      await axios.post('http://localhost:8000/api/categories', null, {
        params: {
          name: newCategoryName,
          parent_id: newCategoryParent || undefined,
          category_type: newCategoryType,
          tax_type: newTaxType || undefined
        }
      });
      
      // Refresh categories
      fetchCategories();
      
      // Reset form
      setNewCategoryName('');
      setNewCategoryParent('');
      setNewCategoryType('transaction');
      setNewTaxType('');
      setShowAddDialog(false);
    } catch (err) {
      console.error('Error creating category:', err);
      alert('Failed to create category');
    }
  };

  const getCategoryIcon = (category: Category) => {
    if (category.is_bank_account) {
      return <div className="w-4 h-4 bg-green-500 rounded-full"></div>;
    }
    if (category.category_type === 'group') {
      return category.expanded ? <FolderOpen size={16} /> : <Folder size={16} />;
    }
    return <div className="w-4 h-4 bg-blue-500 rounded-sm"></div>;
  };

  const getCategoryTypeColor = (category: Category) => {
    if (category.is_bank_account) return 'text-green-700 dark:text-green-300';
    if (category.category_type === 'group') return 'text-gray-700 dark:text-gray-200 font-medium';
    return 'text-gray-600 dark:text-gray-300';
  };

  const renderCategory = (category: Category, level: number = 0) => {
    const hasChildren = category.children && category.children.length > 0;
    const paddingLeft = level * 24;

    return (
      <div key={category.id}>
        <div 
          className={`flex items-center py-2 px-3 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer ${
            selectedCategory === category.id ? 'bg-indigo-50 dark:bg-indigo-900 border-r-2 border-indigo-500' : ''
          }`}
          style={{ paddingLeft: `${paddingLeft + 12}px` }}
          onClick={() => setSelectedCategory(category.id)}
          onDoubleClick={() => {
            if (category.is_bank_account && onNavigateToAccount) {
              onNavigateToAccount(category.id);
            } else if (category.category_type === 'transaction' && onNavigateToCategory) {
              onNavigateToCategory(category.id);
            }
          }}
        >
          {hasChildren && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                toggleExpanded(category.id);
              }}
              className="mr-1 p-1 hover:bg-gray-200 rounded"
            >
              {category.expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            </button>
          )}
          {!hasChildren && <div className="w-6"></div>}
          
          <div className="mr-2">
            {getCategoryIcon(category)}
          </div>
          
          <div className="flex-1">
            <div className={`text-sm ${getCategoryTypeColor(category)}`}>
              {category.name}
            </div>
            {category.tax_type && (
              <div className="text-xs text-gray-500 dark:text-gray-400">Tax: {category.tax_type}</div>
            )}
          </div>
        </div>
        
        {hasChildren && category.expanded && (
          <div>
            {category.children!.map(child => renderCategory(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  const getAllCategories = (cats: Category[]): Category[] => {
    const result: Category[] = [];
    const traverse = (categories: Category[]) => {
      categories.forEach(cat => {
        result.push(cat);
        if (cat.children) {
          traverse(cat.children);
        }
      });
    };
    traverse(cats);
    return result;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-xl">Loading categories...</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-800">
      {/* Header */}
      <div className="border-b p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200">Categories</h2>
          <div className="flex space-x-2">
            <button 
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded flex items-center space-x-1"
              onClick={() => setShowAddDialog(true)}
            >
              <Plus size={18} />
              <span>Add Category</span>
            </button>
          </div>
        </div>
        
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}
      </div>

      {/* Category Tree */}
      <div className="flex-1 overflow-auto">
        <div className="divide-y divide-gray-100">
          {categories.map(category => renderCategory(category))}
        </div>
      </div>

      {/* Add Category Dialog */}
      {showAddDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-96 max-w-full mx-4 border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold mb-4">Add New Category</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Category Name
                </label>
                <input
                  type="text"
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  value={newCategoryName}
                  onChange={(e) => setNewCategoryName(e.target.value)}
                  placeholder="Enter category name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Parent Category (Optional)
                </label>
                <select
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  value={newCategoryParent}
                  onChange={(e) => setNewCategoryParent(e.target.value)}
                >
                  <option value="">No Parent (Root Category)</option>
                  {getAllCategories(categories).map(cat => (
                    <option key={cat.id} value={cat.id}>
                      {cat.name} ({cat.id})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Category Type
                </label>
                <select
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  value={newCategoryType}
                  onChange={(e) => setNewCategoryType(e.target.value)}
                >
                  <option value="transaction">Transaction Category</option>
                  <option value="group">Group Category</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Tax Type (Optional)
                </label>
                <select
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  value={newTaxType}
                  onChange={(e) => setNewTaxType(e.target.value)}
                >
                  <option value="">No Tax Type</option>
                  <option value="GST">GST (Goods and Services Tax)</option>
                  <option value="FRE">FRE (GST Free)</option>
                  <option value="NT">NT (Not Taxable)</option>
                </select>
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
                onClick={handleAddCategory}
              >
                Add Category
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CategoryView;