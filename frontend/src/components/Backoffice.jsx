import { useState, useEffect } from 'react';
import { Download, Calendar, Database, Settings, Package, AlertCircle, CheckCircle2, Loader2, Info, FileSpreadsheet, Archive, ChevronDown, ChevronUp, Sparkles } from 'lucide-react';
import { api } from '../api';

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

const YEARS = [2020, 2021, 2022, 2023, 2024, 2025, 2026];

export default function Backoffice() {
  // State
  const [dataTypes, setDataTypes] = useState([]);
  const [selectedTypes, setSelectedTypes] = useState([]);
  const [mode, setMode] = useState('month'); // 'month', 'year', 'custom'
  const [year, setYear] = useState(2025);
  const [month, setMonth] = useState(1);
  const [startDate, setStartDate] = useState('2025-01-01');
  const [endDate, setEndDate] = useState('2025-01-31');
  const [batchesPerDay, setBatchesPerDay] = useState(20);
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState(null);
  const [scenarios, setScenarios] = useState(null);
  const [showScenarios, setShowScenarios] = useState(false);
  const [message, setMessage] = useState(null);

  // Load data types and scenarios on mount
  useEffect(() => {
    loadDataTypes();
    loadScenarios();
  }, []);

  const loadDataTypes = async () => {
    try {
      const types = await api.getDataTypes();
      setDataTypes(types);
      // Select all by default
      setSelectedTypes(types.map(t => t.name));
    } catch (err) {
      console.error('Failed to load data types:', err);
    }
  };

  const loadScenarios = async () => {
    try {
      const data = await api.getScenarios();
      setScenarios(data);
    } catch (err) {
      console.error('Failed to load scenarios:', err);
    }
  };

  const handleTypeToggle = (typeName) => {
    setSelectedTypes(prev =>
      prev.includes(typeName)
        ? prev.filter(t => t !== typeName)
        : [...prev, typeName]
    );
    setPreview(null);
  };

  const handleSelectAll = () => {
    setSelectedTypes(dataTypes.map(t => t.name));
    setPreview(null);
  };

  const handleSelectNone = () => {
    setSelectedTypes([]);
    setPreview(null);
  };

  const handlePreview = async () => {
    if (selectedTypes.length === 0) {
      setMessage({ type: 'error', text: 'Please select at least one data type' });
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      const result = await api.previewMonthGeneration(
        year,
        month,
        batchesPerDay,
        selectedTypes.length === dataTypes.length ? null : selectedTypes
      );
      setPreview(result);
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to generate preview: ' + err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    if (selectedTypes.length === 0) {
      setMessage({ type: 'error', text: 'Please select at least one data type' });
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      let blob;
      let filename;
      const types = selectedTypes.length === dataTypes.length ? null : selectedTypes;

      if (mode === 'month') {
        blob = await api.downloadMonthData(year, month, batchesPerDay, types);
        filename = `apr_data_${year}_${String(month).padStart(2, '0')}.zip`;
      } else if (mode === 'year') {
        blob = await api.downloadYearData(year, batchesPerDay, types);
        filename = `apr_data_${year}_full_year.zip`;
      } else {
        blob = await api.downloadCustomData(startDate, endDate, batchesPerDay, types);
        filename = `apr_data_${startDate}_to_${endDate}.zip`;
      }

      // Trigger download
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      setMessage({ type: 'success', text: `Successfully downloaded ${filename}` });
    } catch (err) {
      setMessage({ type: 'error', text: 'Download failed: ' + err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadSingle = async (dataType) => {
    setLoading(true);
    setMessage(null);

    try {
      const blob = await api.downloadSingleDataType(dataType, year, month, batchesPerDay);
      const filename = `${year}_${String(month).padStart(2, '0')}_${dataType}.csv`;
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      setMessage({ type: 'success', text: `Downloaded ${filename}` });
    } catch (err) {
      setMessage({ type: 'error', text: 'Download failed: ' + err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl p-6 text-white">
        <div className="flex items-center gap-3">
          <div className="bg-white/20 p-3 rounded-xl">
            <Database className="w-8 h-8" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Data Generation Backoffice</h1>
            <p className="text-indigo-100">Generate synthetic pharmaceutical CSV data for APR analysis</p>
          </div>
        </div>
      </div>

      {/* Message */}
      {message && (
        <div className={`p-4 rounded-lg flex items-center gap-3 ${
          message.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' :
          'bg-red-50 text-red-700 border border-red-200'
        }`}>
          {message.type === 'success' ? <CheckCircle2 className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
          {message.text}
        </div>
      )}

      <div className="grid grid-cols-3 gap-6">
        {/* Left Column: Configuration */}
        <div className="col-span-2 space-y-6">
          {/* Period Selection */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center gap-2 mb-4">
              <Calendar className="w-5 h-5 text-indigo-600" />
              <h2 className="text-lg font-semibold">Period Selection</h2>
            </div>

            {/* Mode Tabs */}
            <div className="flex gap-2 mb-4">
              {[
                { id: 'month', label: 'Single Month' },
                { id: 'year', label: 'Full Year' },
                { id: 'custom', label: 'Custom Range' }
              ].map(m => (
                <button
                  key={m.id}
                  onClick={() => { setMode(m.id); setPreview(null); }}
                  className={`px-4 py-2 rounded-lg font-medium transition-all ${
                    mode === m.id
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {m.label}
                </button>
              ))}
            </div>

            {/* Date Inputs */}
            <div className="grid grid-cols-2 gap-4">
              {mode !== 'custom' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Year</label>
                  <select
                    value={year}
                    onChange={(e) => { setYear(parseInt(e.target.value)); setPreview(null); }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    {YEARS.map(y => (
                      <option key={y} value={y}>{y}</option>
                    ))}
                  </select>
                </div>
              )}

              {mode === 'month' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Month</label>
                  <select
                    value={month}
                    onChange={(e) => { setMonth(parseInt(e.target.value)); setPreview(null); }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    {MONTHS.map((m, i) => (
                      <option key={i + 1} value={i + 1}>{m}</option>
                    ))}
                  </select>
                </div>
              )}

              {mode === 'custom' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                    <input
                      type="date"
                      value={startDate}
                      onChange={(e) => { setStartDate(e.target.value); setPreview(null); }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                    <input
                      type="date"
                      value={endDate}
                      onChange={(e) => { setEndDate(e.target.value); setPreview(null); }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Data Types Selection */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Package className="w-5 h-5 text-indigo-600" />
                <h2 className="text-lg font-semibold">Data Types</h2>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleSelectAll}
                  className="text-sm text-indigo-600 hover:text-indigo-800"
                >
                  Select All
                </button>
                <span className="text-gray-300">|</span>
                <button
                  onClick={handleSelectNone}
                  className="text-sm text-indigo-600 hover:text-indigo-800"
                >
                  Clear
                </button>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              {dataTypes.map(type => (
                <label
                  key={type.name}
                  className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                    selectedTypes.includes(type.name)
                      ? 'border-indigo-500 bg-indigo-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedTypes.includes(type.name)}
                    onChange={() => handleTypeToggle(type.name)}
                    className="mt-1 h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-gray-900 text-sm">{type.display_name}</div>
                    <div className="text-xs text-gray-500 mt-0.5 truncate">{type.description}</div>
                    <div className="text-xs text-indigo-600 mt-1">{type.approximate_columns} columns</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Configuration */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center gap-2 mb-4">
              <Settings className="w-5 h-5 text-indigo-600" />
              <h2 className="text-lg font-semibold">Configuration</h2>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Batches per Day
                </label>
                <input
                  type="number"
                  value={batchesPerDay}
                  onChange={(e) => { setBatchesPerDay(parseInt(e.target.value) || 20); setPreview(null); }}
                  min={1}
                  max={100}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
                <p className="text-xs text-gray-500 mt-1">Typical production: 15-25 batches/day</p>
              </div>
              <div className="flex items-end">
                <div className="bg-indigo-50 p-3 rounded-lg border border-indigo-200 w-full">
                  <div className="text-xs text-indigo-600 font-medium">Selected</div>
                  <div className="text-2xl font-bold text-indigo-700">
                    {selectedTypes.length} / {dataTypes.length}
                  </div>
                  <div className="text-xs text-indigo-600">data types</div>
                </div>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-4">
            <button
              onClick={handlePreview}
              disabled={loading || selectedTypes.length === 0}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-white border-2 border-indigo-600 text-indigo-600 rounded-xl font-semibold hover:bg-indigo-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Info className="w-5 h-5" />}
              Preview Generation
            </button>
            <button
              onClick={handleDownload}
              disabled={loading || selectedTypes.length === 0}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-xl font-semibold hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Archive className="w-5 h-5" />}
              Download ZIP
            </button>
          </div>
        </div>

        {/* Right Column: Preview & Info */}
        <div className="space-y-6">
          {/* Preview Card */}
          {preview && (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex items-center gap-2 mb-4">
                <FileSpreadsheet className="w-5 h-5 text-green-600" />
                <h2 className="text-lg font-semibold">Generation Preview</h2>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Period:</span>
                  <span className="font-medium">{preview.period_start} to {preview.period_end}</span>
                </div>

                <div className="border-t border-gray-100 pt-3">
                  <div className="text-sm font-medium text-gray-700 mb-2">Estimated Records:</div>
                  <div className="space-y-1">
                    {Object.entries(preview.total_records).map(([type, count]) => (
                      <div key={type} className="flex justify-between text-sm">
                        <span className="text-gray-600 capitalize">{type.replace('_', ' ')}</span>
                        <span className="font-mono text-gray-900">{count.toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="border-t border-gray-100 pt-3">
                  <div className="flex justify-between text-sm font-semibold">
                    <span>Total Files:</span>
                    <span className="text-indigo-600">{preview.files_generated.length}</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Quick Download */}
          {mode === 'month' && (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex items-center gap-2 mb-4">
                <Download className="w-5 h-5 text-indigo-600" />
                <h2 className="text-lg font-semibold">Quick Download</h2>
              </div>
              <p className="text-sm text-gray-600 mb-3">Download individual CSV files:</p>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {dataTypes.map(type => (
                  <button
                    key={type.name}
                    onClick={() => handleDownloadSingle(type.name)}
                    disabled={loading}
                    className="w-full flex items-center justify-between px-3 py-2 text-sm bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
                  >
                    <span className="truncate">{type.display_name}</span>
                    <Download className="w-4 h-4 text-gray-400 flex-shrink-0" />
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Scenarios */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <button
              onClick={() => setShowScenarios(!showScenarios)}
              className="w-full flex items-center justify-between"
            >
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-amber-500" />
                <h2 className="text-lg font-semibold">Hidden Scenarios</h2>
              </div>
              {showScenarios ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
            </button>

            {showScenarios && scenarios && (
              <div className="mt-4 space-y-3">
                <p className="text-sm text-gray-600">
                  The generated data contains {scenarios.total_scenarios} embedded scenarios for analysis:
                </p>
                {scenarios.scenarios.map((scenario, idx) => (
                  <div key={idx} className="p-3 bg-amber-50 rounded-lg border border-amber-200">
                    <div className="font-medium text-amber-900 text-sm">{scenario.scenario}</div>
                    <div className="text-xs text-amber-700 mt-1">{scenario.period}</div>
                    <div className="text-xs text-gray-600 mt-2">
                      Effects: {scenario.effects.slice(0, 2).join(', ')}
                      {scenario.effects.length > 2 && '...'}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Info Card */}
          <div className="bg-indigo-50 rounded-xl border border-indigo-200 p-6">
            <div className="flex items-start gap-3">
              <Info className="w-5 h-5 text-indigo-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-indigo-800">
                <p className="font-medium mb-2">About Generated Data</p>
                <ul className="space-y-1 text-indigo-700">
                  <li>• Realistic pharmaceutical scenarios</li>
                  <li>• Interconnected batch, QC, and complaint data</li>
                  <li>• Hidden anomalies for analysis training</li>
                  <li>• ICH-compliant stability conditions</li>
                  <li>• Deterministic generation (same seed = same data)</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
