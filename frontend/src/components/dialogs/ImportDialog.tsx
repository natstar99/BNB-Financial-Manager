import React, { useState, useEffect } from 'react';
import { Upload, X, AlertCircle, CheckCircle, Trash2, Eye, ArrowLeft } from 'lucide-react';
import axios from 'axios';

interface ImportDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onImportComplete: () => void;
}

interface BankAccount {
  id: string;
  name: string;
  account_number?: string;
  bank_name?: string;
}

interface FileAccountMapping {
  file: File;
  accountId: string;
  preview?: TransactionPreview;
}

interface TransactionPreview {
  format: string;
  transaction_count: number;
  transactions: PreviewTransaction[];
  metadata: {
    latest_balance?: number;
    balance_warnings?: string[];
    column_mapping?: Record<string, string>;
  };
  filename: string;
}

interface PreviewTransaction {
  date: string;
  description: string;
  amount: number;
  withdrawal: number;
  deposit: number;
  balance?: number;
  transaction_id?: string;
  category?: string;
}

const ImportDialog: React.FC<ImportDialogProps> = ({ isOpen, onClose, onImportComplete }) => {
  const [fileMappings, setFileMappings] = useState<FileAccountMapping[]>([]);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [accounts, setAccounts] = useState<BankAccount[]>([]);
  const [loadingAccounts, setLoadingAccounts] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [previewingFile, setPreviewingFile] = useState<number | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);

  // Fetch accounts from API
  useEffect(() => {
    if (isOpen) {
      fetchAccounts();
    }
  }, [isOpen]);

  const fetchAccounts = async () => {
    setLoadingAccounts(true);
    try {
      const response = await axios.get('http://localhost:8000/api/accounts');
      setAccounts(response.data);
    } catch (err) {
      setError('Failed to load bank accounts');
    } finally {
      setLoadingAccounts(false);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) {
      const newMappings = Array.from(files).map(file => ({
        file,
        accountId: ''
      }));
      setFileMappings(prev => [...prev, ...newMappings]);
    }
    setError(null);
    setImportResult(null);
    // Reset the input so the same file can be selected again
    event.target.value = '';
  };

  const updateAccountForFile = (fileIndex: number, accountId: string) => {
    setFileMappings(prev => 
      prev.map((mapping, index) => 
        index === fileIndex ? { ...mapping, accountId } : mapping
      )
    );
  };

  const removeFile = (fileIndex: number) => {
    setFileMappings(prev => prev.filter((_, index) => index !== fileIndex));
  };

  const previewFile = async (fileIndex: number) => {
    setLoadingPreview(true);
    setError(null);

    try {
      const mapping = fileMappings[fileIndex];
      const formData = new FormData();
      formData.append('file', mapping.file);

      const response = await axios.post(
        'http://localhost:8000/api/import/preview',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      // Update the file mapping with preview data
      setFileMappings(prev =>
        prev.map((m, index) =>
          index === fileIndex ? { ...m, preview: response.data } : m
        )
      );

      setPreviewingFile(fileIndex);
      setShowPreview(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to preview file');
    } finally {
      setLoadingPreview(false);
    }
  };

  const closePreview = () => {
    setShowPreview(false);
    setPreviewingFile(null);
  };

  const handleImport = async () => {
    if (fileMappings.length === 0) {
      setError('Please select at least one QIF file');
      return;
    }

    // Check that all files have accounts selected
    const unmappedFiles = fileMappings.filter(mapping => !mapping.accountId);
    if (unmappedFiles.length > 0) {
      setError('Please select an account for all files');
      return;
    }

    setImporting(true);
    setError(null);

    try {
      let totalImported = 0;
      const results: string[] = [];
      const balanceUpdates: string[] = [];
      const warnings: string[] = [];

      for (const mapping of fileMappings) {
        const formData = new FormData();
        formData.append('file', mapping.file);

        const response = await axios.post(
          `http://localhost:8000/api/import?account_id=${mapping.accountId}`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          }
        );

        const imported = response.data.imported_count;
        const duplicates = response.data.duplicate_count || 0;
        const format = response.data.format || 'Unknown';
        totalImported += imported;
        
        const accountName = accounts.find(a => a.id === mapping.accountId)?.name || mapping.accountId;
        let resultLine = `${mapping.file.name} (${format}) → ${accountName}: ${imported} transactions`;
        if (duplicates > 0) {
          resultLine += ` (${duplicates} duplicates skipped)`;
        }
        results.push(resultLine);

        // Handle CSV-specific features
        if (response.data.updated_balance !== undefined) {
          balanceUpdates.push(`${accountName}: Updated to $${response.data.updated_balance.toFixed(2)}`);
        }

        if (response.data.balance_warnings) {
          warnings.push(...response.data.balance_warnings);
        }
      }

      let resultMessage = `Successfully imported ${totalImported} total transactions:\n${results.join('\n')}`;
      
      if (balanceUpdates.length > 0) {
        resultMessage += `\n\nAccount Balances Updated:\n${balanceUpdates.join('\n')}`;
      }

      if (warnings.length > 0) {
        resultMessage += `\n\nBalance Warnings:\n${warnings.join('\n')}`;
      }

      setImportResult(resultMessage);
      onImportComplete();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to import files');
    } finally {
      setImporting(false);
    }
  };

  const handleClose = () => {
    setFileMappings([]);
    setImporting(false);
    setImportResult(null);
    setError(null);
    setShowPreview(false);
    setPreviewingFile(null);
    setLoadingPreview(false);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-96 max-w-full mx-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Import QIF Files</h3>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X size={20} />
          </button>
        </div>

        <div className="space-y-4">

          {/* File Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Select QIF or CSV Files *
            </label>
            <div className="border-2 border-dashed border-gray-300 rounded-md p-6 text-center hover:border-indigo-400 transition-colors">
              <Upload className="mx-auto w-8 h-8 text-gray-400 mb-2" />
              <div className="text-sm text-gray-600 mb-2">
                Drag and drop QIF or CSV files here, or{' '}
                <label className="text-indigo-600 hover:text-indigo-500 cursor-pointer">
                  browse
                  <input
                    type="file"
                    multiple
                    accept=".qif,.csv"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                </label>
              </div>
              <div className="text-xs text-gray-500">
                Supports QIF and CSV files from your bank
              </div>
            </div>
          </div>

          {/* File to Account Mappings */}
          {fileMappings.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                File to Account Mapping ({fileMappings.length} files)
              </label>
              <div className="max-h-64 overflow-y-auto border border-gray-200 rounded-md p-3 space-y-3">
                {fileMappings.map((mapping, index) => (
                  <div key={index} className="flex items-center space-x-3 p-2 bg-gray-50 rounded border">
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-700">
                        📄 {mapping.file.name}
                      </div>
                      <div className="text-xs text-gray-500">
                        {(mapping.file.size / 1024).toFixed(1)} KB
                      </div>
                    </div>
                    <div className="flex-1">
                      <select
                        className="w-full border border-gray-300 rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500"
                        value={mapping.accountId}
                        onChange={(e) => updateAccountForFile(index, e.target.value)}
                        disabled={loadingAccounts}
                      >
                        <option value="">Select account...</option>
                        {accounts.map(account => (
                          <option key={account.id} value={account.id}>
                            {account.name} {account.bank_name && `(${account.bank_name})`}
                          </option>
                        ))}
                      </select>
                    </div>
                    <button
                      onClick={() => previewFile(index)}
                      className="text-blue-500 hover:text-blue-700 p-1"
                      title="Preview transactions"
                      disabled={loadingPreview && previewingFile === index}
                    >
                      {loadingPreview && previewingFile === index ? (
                        <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                      ) : (
                        <Eye size={16} />
                      )}
                    </button>
                    <button
                      onClick={() => removeFile(index)}
                      className="text-red-500 hover:text-red-700 p-1"
                      title="Remove file"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
              </div>
              {loadingAccounts && (
                <div className="text-sm text-gray-500 mt-2">
                  Loading accounts...
                </div>
              )}
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3 flex items-start space-x-2">
              <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-red-700">{error}</div>
            </div>
          )}

          {/* Success Message */}
          {importResult && (
            <div className="bg-green-50 border border-green-200 rounded-md p-3 flex items-start space-x-2">
              <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-green-700">{importResult}</div>
            </div>
          )}

          {/* Import Notes */}
          <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
            <h4 className="text-sm font-medium text-blue-800 mb-1">Import Notes:</h4>
            <ul className="text-xs text-blue-700 space-y-1">
              <li>• Duplicate transactions will be automatically detected</li>
              <li>• Internal transfers will be matched if found</li>
              <li>• Auto-categorisation rules will be applied</li>
              <li>• CSV files will automatically update account balances</li>
              <li>• QIF and CSV files should be exported from your bank</li>
            </ul>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end space-x-3 mt-6">
          <button
            className="px-4 py-2 text-gray-600 hover:text-gray-800"
            onClick={handleClose}
            disabled={importing}
          >
            {importResult ? 'Close' : 'Cancel'}
          </button>
          {!importResult && (
            <button
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded disabled:bg-gray-400 disabled:cursor-not-allowed"
              onClick={handleImport}
              disabled={importing || fileMappings.length === 0 || fileMappings.some(m => !m.accountId)}
            >
              {importing ? 'Importing...' : `Import ${fileMappings.length} File${fileMappings.length !== 1 ? 's' : ''}`}
            </button>
          )}
        </div>
      </div>

      {/* Transaction Preview Modal */}
      {showPreview && previewingFile !== null && fileMappings[previewingFile]?.preview && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-60">
          <div className="bg-white rounded-lg p-6 w-11/12 max-w-6xl max-h-5/6 overflow-hidden flex flex-col">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">
                Preview: {fileMappings[previewingFile].preview.filename}
              </h3>
              <button
                onClick={closePreview}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={20} />
              </button>
            </div>

            <div className="flex-1 overflow-hidden flex flex-col">
              {/* Preview Header Info */}
              <div className="mb-4 p-3 bg-gray-50 rounded-md">
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="font-medium">Format:</span> {fileMappings[previewingFile].preview.format}
                  </div>
                  <div>
                    <span className="font-medium">Transactions:</span> {fileMappings[previewingFile].preview.transaction_count}
                  </div>
                  {fileMappings[previewingFile].preview.metadata.latest_balance && (
                    <div>
                      <span className="font-medium">Latest Balance:</span> ${fileMappings[previewingFile].preview.metadata.latest_balance.toFixed(2)}
                    </div>
                  )}
                </div>
                
                {/* Show balance warnings if any */}
                {fileMappings[previewingFile].preview.metadata.balance_warnings && 
                 fileMappings[previewingFile].preview.metadata.balance_warnings.length > 0 && (
                  <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded">
                    <div className="text-sm font-medium text-yellow-800">Balance Warnings:</div>
                    {fileMappings[previewingFile].preview.metadata.balance_warnings.map((warning, idx) => (
                      <div key={idx} className="text-xs text-yellow-700 mt-1">• {warning}</div>
                    ))}
                  </div>
                )}
              </div>

              {/* Transactions Table */}
              <div className="flex-1 overflow-auto border border-gray-200 rounded-md">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 sticky top-0">
                    <tr>
                      <th className="px-3 py-2 text-left">Date</th>
                      <th className="px-3 py-2 text-left">Description</th>
                      <th className="px-3 py-2 text-right">Withdrawal</th>
                      <th className="px-3 py-2 text-right">Deposit</th>
                      {fileMappings[previewingFile].preview.format === 'CSV' && (
                        <th className="px-3 py-2 text-right">Balance</th>
                      )}
                      {fileMappings[previewingFile].preview.transactions.some(t => t.category) && (
                        <th className="px-3 py-2 text-left">Category</th>
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {fileMappings[previewingFile].preview.transactions.map((transaction, idx) => (
                      <tr key={idx} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className="px-3 py-2">{transaction.date}</td>
                        <td className="px-3 py-2">{transaction.description}</td>
                        <td className="px-3 py-2 text-right">
                          {transaction.withdrawal > 0 ? `$${transaction.withdrawal.toFixed(2)}` : ''}
                        </td>
                        <td className="px-3 py-2 text-right">
                          {transaction.deposit > 0 ? `$${transaction.deposit.toFixed(2)}` : ''}
                        </td>
                        {fileMappings[previewingFile].preview.format === 'CSV' && (
                          <td className="px-3 py-2 text-right">
                            {transaction.balance !== null && transaction.balance !== undefined 
                              ? `$${transaction.balance.toFixed(2)}` : ''}
                          </td>
                        )}
                        {fileMappings[previewingFile].preview.transactions.some(t => t.category) && (
                          <td className="px-3 py-2">{transaction.category || ''}</td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Preview Footer */}
            <div className="flex justify-end space-x-3 mt-4">
              <button
                onClick={closePreview}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                <ArrowLeft size={16} className="inline mr-1" />
                Back to Import
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ImportDialog;