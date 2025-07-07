import React, { useState, useEffect, useRef } from 'react';
import { X, Search, FolderOpen, Folder } from 'lucide-react';
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

interface CategoryPickerDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onCategorySelect: (categoryId: string) => void;
  onMarkAsInternalTransfer?: () => void;
  onMarkAsHidden?: () => void;
  currentCategoryId?: string;
}

const CategoryPickerDialog: React.FC<CategoryPickerDialogProps> = ({ 
  isOpen, 
  onClose, 
  onCategorySelect, 
  onMarkAsInternalTransfer,
  onMarkAsHidden,
  currentCategoryId 
}) => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(currentCategoryId || null);
  const [loading, setLoading] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Sample data matching the existing structure
  const sampleCategories: Category[] = [
    {
      id: "1",
      name: "Income",
      parent_id: null,
      category_type: "group",
      tax_type: null,
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
          tax_type: null,
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
      parent_id: null,
      category_type: "group",
      tax_type: null,
      is_bank_account: false,
      expanded: true,
      children: [
        {
          id: "2.1",
          name: "Food",
          parent_id: "2",
          category_type: "group",
          tax_type: null,
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
          tax_type: null,
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
          tax_type: null,
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
    }
  ];

  useEffect(() => {
    if (isOpen) {
      fetchCategories();
      // Auto-focus search input when dialog opens
      setTimeout(() => {
        searchInputRef.current?.focus();
      }, 100);
    }
  }, [isOpen]);

  const fetchCategories = async () => {
    try {
      setLoading(true);
      const response = await axios.get<Category[]>('http://localhost:8000/api/categories');
      
      // Build tree structure from flat list
      const categoryMap = new Map<string, Category>();
      const rootCategories: Category[] = [];

      // First pass: create all category objects
      response.data.forEach(cat => {
        categoryMap.set(cat.id, { ...cat, children: [], expanded: true });
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
    } catch (err) {
      console.error('Error fetching categories:', err);
      // Fallback to sample data
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
    if (category.is_bank_account) return 'text-green-700';
    if (category.category_type === 'group') return 'text-gray-700 font-medium';
    return 'text-gray-600';
  };

  const getMatchingTransactionCategories = (cats: Category[]): Category[] => {
    const matches: Category[] = [];
    
    const searchCategories = (categories: Category[]) => {
      categories.forEach(cat => {
        const matchesSearch = searchTerm === '' || 
          cat.name.toLowerCase().includes(searchTerm.toLowerCase());
        
        if (matchesSearch && cat.category_type === 'transaction') {
          matches.push(cat);
        }
        
        if (cat.children) {
          searchCategories(cat.children);
        }
      });
    };
    
    searchCategories(cats);
    return matches;
  };

  // Auto-select when only one transaction category matches
  useEffect(() => {
    if (searchTerm && searchTerm.length >= 2) {
      const matchingCategories = getMatchingTransactionCategories(categories);
      if (matchingCategories.length === 1) {
        setSelectedCategory(matchingCategories[0].id);
      }
    }
  }, [searchTerm, categories]);

  const renderCategory = (category: Category, level: number = 0) => {
    const hasChildren = category.children && category.children.length > 0;
    const paddingLeft = level * 24;
    const isTransactionCategory = category.category_type === 'transaction';
    const matchesSearch = searchTerm === '' || 
      category.name.toLowerCase().includes(searchTerm.toLowerCase());

    if (!matchesSearch && !hasChildren) return null;

    return (
      <div key={category.id}>
        <div 
          className={`flex items-center py-2 px-3 hover:bg-gray-50 cursor-pointer ${
            selectedCategory === category.id ? 'bg-indigo-50 border-r-2 border-indigo-500' : ''
          } ${!isTransactionCategory ? 'cursor-default' : ''}`}
          style={{ paddingLeft: `${paddingLeft + 12}px` }}
          onClick={() => {
            if (isTransactionCategory) {
              setSelectedCategory(category.id);
            } else if (hasChildren) {
              toggleExpanded(category.id);
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
              {category.expanded ? (
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                </svg>
              )}
            </button>
          )}
          {!hasChildren && <div className="w-6"></div>}
          
          <div className="mr-2">
            {getCategoryIcon(category)}
          </div>
          
          <div className="flex-1">
            <div className={`text-sm ${getCategoryTypeColor(category)}`}>
              {category.name}
              {!isTransactionCategory && (
                <span className="text-xs text-gray-400 ml-1">(Group)</span>
              )}
            </div>
            {category.tax_type && (
              <div className="text-xs text-gray-500">Tax: {category.tax_type}</div>
            )}
          </div>

          {isTransactionCategory && selectedCategory === category.id && (
            <div className="text-indigo-600">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
            </div>
          )}
        </div>
        
        {hasChildren && category.expanded && (
          <div>
            {category.children!.map(child => renderCategory(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  const handleSelect = () => {
    if (selectedCategory) {
      onCategorySelect(selectedCategory);
      onClose();
    }
  };

  const getSelectedCategoryName = () => {
    const findCategory = (cats: Category[]): string | null => {
      for (const cat of cats) {
        if (cat.id === selectedCategory) {
          return cat.name;
        }
        if (cat.children) {
          const found = findCategory(cat.children);
          if (found) return found;
        }
      }
      return null;
    };
    return findCategory(categories);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-96 max-w-full mx-4 max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="text-lg font-semibold">Select Category</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X size={20} />
          </button>
        </div>

        {/* Quick Action Buttons - moved to top */}
        {(onMarkAsInternalTransfer || onMarkAsHidden) && (
          <div className="p-3 border-b bg-gray-50">
            <div className="flex space-x-2">
              {onMarkAsInternalTransfer && (
                <button
                  className="bg-purple-100 hover:bg-purple-200 text-purple-800 px-3 py-1.5 rounded text-sm font-medium flex-1 transition-colors"
                  onClick={() => {
                    onMarkAsInternalTransfer();
                    onClose();
                  }}
                >
                  Mark as Internal Transfer
                </button>
              )}
              {onMarkAsHidden && (
                <button
                  className="bg-orange-100 hover:bg-orange-200 text-orange-800 px-3 py-1.5 rounded text-sm font-medium flex-1 transition-colors"
                  onClick={() => {
                    onMarkAsHidden();
                    onClose();
                  }}
                >
                  Mark as Hidden
                </button>
              )}
            </div>
          </div>
        )}

        {/* Search */}
        <div className="p-4 border-b">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={16} />
            <input
              ref={searchInputRef}
              type="text"
              placeholder="Search categories..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && selectedCategory) {
                  handleSelect();
                }
              }}
            />
          </div>
        </div>

        {/* Category List */}
        <div className="flex-1 overflow-auto p-2">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-gray-500">Loading categories...</div>
            </div>
          ) : (
            categories.map(category => renderCategory(category))
          )}
        </div>

        {/* Selected Category Display */}
        {selectedCategory && (
          <div className="p-4 border-t bg-gray-50">
            <div className="text-sm text-gray-600">Selected:</div>
            <div className="font-medium text-gray-900">{getSelectedCategoryName()}</div>
          </div>
        )}


        {/* Action Buttons */}
        <div className="flex justify-between items-center p-4 border-t">
          <button
            className="text-gray-600 hover:text-gray-800"
            onClick={() => setSelectedCategory(null)}
          >
            Clear Selection
          </button>
          <div className="space-x-3">
            <button
              className="px-4 py-2 text-gray-600 hover:text-gray-800"
              onClick={onClose}
            >
              Cancel
            </button>
            <button
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded disabled:bg-gray-400 disabled:cursor-not-allowed"
              onClick={handleSelect}
              disabled={!selectedCategory}
            >
              Select Category
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CategoryPickerDialog;