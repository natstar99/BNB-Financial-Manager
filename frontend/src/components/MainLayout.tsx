import React, { useState } from 'react';
import { Settings, BarChart3, FileText, CreditCard, FolderOpen, Tag, Zap, Moon, Sun } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import TransactionViewStandalone from './TransactionViewStandalone';
import CategoryView from './CategoryView';
import AccountView from './AccountView';
import AnalysisView from './AnalysisView';
import AutoCategorizeRulesView from './AutoCategorizeRulesView';

type ViewType = 'transactions' | 'categories' | 'accounts' | 'reports' | 'charts' | 'budget' | 'auto-rules';

interface NavigationState {
  view: ViewType;
  params?: {
    accountFilter?: string;
    categoryFilter?: string;
  };
}

const MainLayout: React.FC = () => {
  const [navigationState, setNavigationState] = useState<NavigationState>({
    view: 'transactions'
  });
  const { isDarkMode, toggleDarkMode } = useTheme();

  const handleNavigation = (newState: NavigationState) => {
    setNavigationState(newState);
  };

  const renderCurrentView = () => {
    switch (navigationState.view) {
      case 'transactions':
        return <TransactionViewStandalone 
          initialAccountFilter={navigationState.params?.accountFilter} 
          initialCategoryFilter={navigationState.params?.categoryFilter}
        />;
      case 'categories':
        return <CategoryView 
          onNavigateToAccount={(accountId) => handleNavigation({ view: 'transactions', params: { accountFilter: accountId } })}
          onNavigateToCategory={(categoryId) => handleNavigation({ view: 'transactions', params: { categoryFilter: categoryId } })}
        />;
      case 'accounts':
        return <AccountView />;
      case 'auto-rules':
        return <AutoCategorizeRulesView />;
      case 'reports':
        return (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <FileText size={48} className="mx-auto text-gray-400 dark:text-gray-500 mb-4" />
              <h3 className="text-xl font-semibold text-gray-600 dark:text-gray-300 mb-2">Reports</h3>
              <p className="text-gray-500 dark:text-gray-400">Financial reports coming soon...</p>
            </div>
          </div>
        );
      case 'charts':
        return <AnalysisView />;
      case 'budget':
        return (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <Tag size={48} className="mx-auto text-gray-400 dark:text-gray-500 mb-4" />
              <h3 className="text-xl font-semibold text-gray-600 dark:text-gray-300 mb-2">Budget</h3>
              <p className="text-gray-500 dark:text-gray-400">Budget management coming soon...</p>
            </div>
          </div>
        );
      default:
        return <TransactionViewStandalone />;
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header with app title and main navigation */}
      <header className="bg-indigo-700 dark:bg-indigo-800 text-white p-4 shadow-md">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold">BNB Financial Manager</h1>
          <div className="flex space-x-2">
            <button 
              onClick={toggleDarkMode}
              className="p-2 hover:bg-indigo-600 dark:hover:bg-indigo-700 rounded transition-colors"
              title={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {isDarkMode ? <Sun size={20} /> : <Moon size={20} />}
            </button>
            <button className="p-2 hover:bg-indigo-600 dark:hover:bg-indigo-700 rounded">
              <Settings size={20} />
            </button>
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar - Navigation */}
        <nav className="w-48 bg-indigo-800 dark:bg-indigo-900 text-white p-4">
          <div className="space-y-6">
            <div>
              <h2 className="text-xs uppercase tracking-wider text-indigo-300 mb-2">Management</h2>
              <ul className="space-y-1">
                <li>
                  <button
                    className={`w-full text-left rounded px-3 py-2 font-medium flex items-center space-x-2 ${
                      navigationState.view === 'transactions' ? 'bg-indigo-900 dark:bg-indigo-950' : 'hover:bg-indigo-700 dark:hover:bg-indigo-800'
                    }`}
                    onClick={() => setNavigationState({ view: 'transactions' })}
                  >
                    <CreditCard size={16} />
                    <span>Transactions</span>
                  </button>
                </li>
                <li>
                  <button
                    className={`w-full text-left rounded px-3 py-2 font-medium flex items-center space-x-2 ${
                      navigationState.view === 'categories' ? 'bg-indigo-900 dark:bg-indigo-950' : 'hover:bg-indigo-700 dark:hover:bg-indigo-800'
                    }`}
                    onClick={() => setNavigationState({ view: 'categories' })}
                  >
                    <FolderOpen size={16} />
                    <span>Categories</span>
                  </button>
                </li>
                <li>
                  <button
                    className={`w-full text-left rounded px-3 py-2 font-medium flex items-center space-x-2 ${
                      navigationState.view === 'accounts' ? 'bg-indigo-900 dark:bg-indigo-950' : 'hover:bg-indigo-700 dark:hover:bg-indigo-800'
                    }`}
                    onClick={() => setNavigationState({ view: 'accounts' })}
                  >
                    <CreditCard size={16} />
                    <span>Accounts</span>
                  </button>
                </li>
                <li>
                  <button
                    className={`w-full text-left rounded px-3 py-2 font-medium flex items-center space-x-2 ${
                      navigationState.view === 'auto-rules' ? 'bg-indigo-900 dark:bg-indigo-950' : 'hover:bg-indigo-700 dark:hover:bg-indigo-800'
                    }`}
                    onClick={() => setNavigationState({ view: 'auto-rules' })}
                  >
                    <Zap size={16} />
                    <span>Auto Rules</span>
                  </button>
                </li>
              </ul>
            </div>
            <div>
              <h2 className="text-xs uppercase tracking-wider text-indigo-300 mb-2">Analysis</h2>
              <ul className="space-y-1">
                <li>
                  <button
                    className={`w-full text-left rounded px-3 py-2 font-medium flex items-center space-x-2 ${
                      navigationState.view === 'reports' ? 'bg-indigo-900 dark:bg-indigo-950' : 'hover:bg-indigo-700 dark:hover:bg-indigo-800'
                    }`}
                    onClick={() => setNavigationState({ view: 'reports' })}
                  >
                    <FileText size={16} />
                    <span>Reports</span>
                  </button>
                </li>
                <li>
                  <button
                    className={`w-full text-left rounded px-3 py-2 font-medium flex items-center space-x-2 ${
                      navigationState.view === 'charts' ? 'bg-indigo-900 dark:bg-indigo-950' : 'hover:bg-indigo-700 dark:hover:bg-indigo-800'
                    }`}
                    onClick={() => setNavigationState({ view: 'charts' })}
                  >
                    <BarChart3 size={16} />
                    <span>Charts</span>
                  </button>
                </li>
                <li>
                  <button
                    className={`w-full text-left rounded px-3 py-2 font-medium flex items-center space-x-2 ${
                      navigationState.view === 'budget' ? 'bg-indigo-900 dark:bg-indigo-950' : 'hover:bg-indigo-700 dark:hover:bg-indigo-800'
                    }`}
                    onClick={() => setNavigationState({ view: 'budget' })}
                  >
                    <Tag size={16} />
                    <span>Budget</span>
                  </button>
                </li>
              </ul>
            </div>
          </div>
        </nav>

        {/* Main Content Area */}
        <main className="flex-1 overflow-hidden">
          {renderCurrentView()}
        </main>
      </div>
    </div>
  );
};

export default MainLayout;