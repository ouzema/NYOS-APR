import { useState, useEffect } from 'react';
import { 
  Package, AlertTriangle, CheckCircle, Clock, FileWarning, Wrench, 
  TrendingUp, TrendingDown, FileText, Download, Activity, Target,
  AlertCircle, Zap, BarChart3, ArrowUpRight, ArrowDownRight, Minus,
  Factory, Users, Truck, Shield, ChevronDown, ChevronUp, X, Calendar,
  History, Eye, Trash2, Info
} from 'lucide-react';
import { api } from '../api';
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area 
} from 'recharts';

function parseMarkdown(text) {
  if (!text) return '';
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/### (.*?)(\n|$)/g, '<h4 class="font-semibold text-lg mt-4 mb-2">$1</h4>')
    .replace(/## (.*?)(\n|$)/g, '<h3 class="font-bold text-xl mt-4 mb-2">$1</h3>')
    .replace(/# (.*?)(\n|$)/g, '<h2 class="font-bold text-2xl mt-4 mb-3">$1</h2>')
    .replace(/- (.*?)(\n|$)/g, '<li class="ml-4">$1</li>')
    .replace(/\n/g, '<br/>');
}

// Quality Score Gauge
function QualityGauge({ score }) {
  const getColor = (s) => {
    if (s >= 90) return '#22c55e';
    if (s >= 75) return '#eab308';
    if (s >= 50) return '#f97316';
    return '#ef4444';
  };
  
  const getLabel = (s) => {
    if (s >= 90) return 'Excellent';
    if (s >= 75) return 'Good';
    if (s >= 50) return 'Needs Attention';
    return 'Critical';
  };

  const color = getColor(score);
  const circumference = 2 * Math.PI * 45;
  const progress = (score / 100) * circumference;

  return (
    <div className="flex flex-col items-center">
      <div className="relative">
        <svg className="w-24 h-24 sm:w-32 sm:h-32 transform -rotate-90">
          <circle cx="64" cy="64" r="45" stroke="#e5e7eb" strokeWidth="10" fill="none" />
          <circle 
            cx="64" cy="64" r="45" 
            stroke={color} 
            strokeWidth="10" 
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={circumference - progress}
            strokeLinecap="round"
            className="transition-all duration-1000"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl sm:text-3xl font-bold" style={{ color }}>{score}</span>
          <span className="text-xs text-gray-500">/100</span>
        </div>
      </div>
      <span className="mt-2 text-sm font-medium" style={{ color }}>{getLabel(score)}</span>
    </div>
  );
}

// KPI Card with trend - now clickable for details
function KPICard({ icon: Icon, label, value, trend, trendValue, color = 'blue', subtext, onClick, hasDetails = false }) {
  const colors = {
    blue: 'bg-blue-100 text-blue-600 border-blue-200',
    green: 'bg-green-100 text-green-600 border-green-200',
    yellow: 'bg-yellow-100 text-yellow-600 border-yellow-200',
    red: 'bg-red-100 text-red-600 border-red-200',
    purple: 'bg-purple-100 text-purple-600 border-purple-200',
  };
  
  const TrendIcon = trend === 'up' ? ArrowUpRight : trend === 'down' ? ArrowDownRight : Minus;
  const trendColor = trend === 'up' ? 'text-green-500' : trend === 'down' ? 'text-red-500' : 'text-gray-400';
  
  return (
    <div 
      className={`bg-white rounded-xl p-3 sm:p-5 border border-gray-200 hover:shadow-lg transition-shadow ${hasDetails ? 'cursor-pointer hover:border-primary-300' : ''}`}
      onClick={onClick}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <p className="text-sm text-gray-500 mb-1">{label}</p>
            {hasDetails && <Info size={12} className="text-primary-400" />}
          </div>
          <p className="text-xl sm:text-2xl font-bold text-gray-900">{value}</p>
          {(trendValue !== undefined) && (
            <div className={`flex items-center gap-1 mt-1 text-sm ${trendColor}`}>
              <TrendIcon size={14} />
              <span>{trendValue > 0 ? '+' : ''}{trendValue}%</span>
            </div>
          )}
          {subtext && <p className="text-xs text-gray-400 mt-1">{subtext}</p>}
        </div>
        <div className={`p-3 rounded-lg ${colors[color]}`}>
          <Icon size={22} />
        </div>
      </div>
    </div>
  );
}

// Drift Alert Card
function DriftCard({ drift }) {
  const isAlert = drift.alert;
  const Icon = drift.direction === 'up' ? TrendingUp : TrendingDown;
  
  return (
    <div className={`p-4 rounded-lg border ${isAlert ? 'bg-yellow-50 border-yellow-200' : 'bg-gray-50 border-gray-200'}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${isAlert ? 'bg-yellow-100' : 'bg-gray-100'}`}>
            <Icon size={18} className={isAlert ? 'text-yellow-600' : 'text-gray-500'} />
          </div>
          <div>
            <p className="font-medium text-gray-900">{drift.label}</p>
            <p className="text-sm text-gray-500">
              {drift.previous_avg} → {drift.current_avg}
            </p>
          </div>
        </div>
        <div className="text-right">
          <p className={`font-bold ${drift.change > 0 ? 'text-green-600' : 'text-red-600'}`}>
            {drift.change > 0 ? '+' : ''}{drift.change}
          </p>
          <p className="text-xs text-gray-400">{drift.change_pct}%</p>
        </div>
      </div>
      {drift.equipment_drifts?.length > 0 && (
        <div className="mt-3 pt-3 border-t border-yellow-200">
          <p className="text-xs text-yellow-700 mb-1">Affected equipment:</p>
          {drift.equipment_drifts.map((eq, i) => (
            <span key={i} className="inline-block bg-yellow-100 text-yellow-700 text-xs px-2 py-1 rounded mr-1">
              {eq.equipment}: {eq.change > 0 ? '+' : ''}{eq.change}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

// Anomaly Item
function AnomalyItem({ anomaly }) {
  const colors = {
    critical: 'bg-red-100 text-red-700 border-red-200',
    warning: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  };
  
  return (
    <div className={`p-3 rounded-lg border ${colors[anomaly.severity]} mb-2`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="font-medium">{anomaly.message}</p>
          {anomaly.batch_id && <p className="text-sm opacity-75">Lot: {anomaly.batch_id}</p>}
          {anomaly.details && <p className="text-xs mt-1 opacity-60">{anomaly.details}</p>}
        </div>
        <span className={`text-xs px-2 py-1 rounded ${anomaly.severity === 'critical' ? 'bg-red-200' : 'bg-yellow-200'}`}>
          {anomaly.severity}
        </span>
      </div>
    </div>
  );
}

// Detail Modal Component for KPI details
function DetailModal({ isOpen, onClose, title, children }) {
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl w-full max-w-2xl max-h-[85vh] sm:max-h-[80vh] flex flex-col mx-2 sm:mx-auto">
        <div className="p-3 sm:p-4 border-b flex items-center justify-between">
          <h3 className="font-bold text-base sm:text-lg">{title}</h3>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg">
            <X size={20} />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-4 sm:p-6">
          {children}
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [drifts, setDrifts] = useState(null);
  const [anomalies, setAnomalies] = useState(null);
  const [yearly, setYearly] = useState(null);
  const [suppliers, setSuppliers] = useState(null);
  const [summary, setSummary] = useState('');
  const [report, setReport] = useState('');
  const [loading, setLoading] = useState(true);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryMinimized, setSummaryMinimized] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);
  const [showReport, setShowReport] = useState(false);
  
  // New states for enhanced features
  const [showReportConfig, setShowReportConfig] = useState(false);
  const [reportStartDate, setReportStartDate] = useState('');
  const [reportEndDate, setReportEndDate] = useState('');
  const [reportTitle, setReportTitle] = useState('');
  const [reportHistory, setReportHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [selectedDetail, setSelectedDetail] = useState(null);
  const [detailData, setDetailData] = useState(null);
  
  // APR PDF generation states
  const [aprYear, setAprYear] = useState(2025);
  const [aprStatus, setAprStatus] = useState(null); // 'generating', 'ready', 'downloading', null
  const [aprMessage, setAprMessage] = useState('');
  const [complaints, setComplaints] = useState([]);
  const [capas, setCapas] = useState([]);
  const [equipment, setEquipment] = useState(null);

  useEffect(() => { loadData(); loadReportHistory(); }, []);

  async function loadReportHistory() {
    try {
      const history = await api.getReportHistory();
      setReportHistory(history);
    } catch (e) {
      console.error('Failed to load report history:', e);
    }
  }

  async function loadData() {
    setLoading(true);
    try {
      const [analyticsData, driftsData, anomaliesData, yearlyData, suppliersData] = await Promise.all([
        api.getAnalyticsOverview(),
        api.getDriftDetection(90),
        api.getAnomalies(30),
        api.getYearlySummary(),
        api.getSupplierPerformance()
      ]);
      setAnalytics(analyticsData);
      setDrifts(driftsData);
      setAnomalies(anomaliesData);
      setYearly(yearlyData);
      setSuppliers(suppliersData);
    } catch (e) {
      console.error('Failed to load analytics:', e);
    } finally {
      setLoading(false);
    }
  }

  function generateSummary() {
    setSummaryLoading(true);
    setSummary('');
    api.streamSummary(
      (text) => setSummary(prev => prev + text),
      () => setSummaryLoading(false),
      (error) => { setSummary("Error: " + error); setSummaryLoading(false); }
    );
  }

  async function generateReport() {
    setReportLoading(true);
    try {
      const data = await api.getReport(
        reportStartDate || null,
        reportEndDate || null,
        reportTitle || null,
        true
      );
      setReport(data.report);
      setShowReport(true);
      setShowReportConfig(false);
      loadReportHistory(); // Refresh history
    } catch (e) { setReport("Error generating report."); }
    finally { setReportLoading(false); }
  }

  async function loadSavedReport(reportId) {
    try {
      const data = await api.getSavedReport(reportId);
      setReport(data.content);
      setShowReport(true);
      setShowHistory(false);
    } catch (e) {
      console.error('Failed to load report:', e);
    }
  }

  async function deleteReport(reportId) {
    if (confirm('Delete this report?')) {
      await api.deleteReport(reportId);
      loadReportHistory();
    }
  }

  // Load detail data for KPI clicks
  async function loadDetailData(type) {
    setSelectedDetail(type);
    try {
      switch (type) {
        case 'complaints':
          const complaintsData = await api.getComplaints();
          setDetailData(complaintsData);
          break;
        case 'capas':
          const capasData = await api.getCapas();
          setDetailData(capasData);
          break;
        case 'equipment':
          const equipData = await api.getEquipmentAnalysis();
          setDetailData(equipData);
          break;
        case 'batches':
          const batchesData = await api.getBatches(100);
          setDetailData(batchesData);
          break;
        default:
          setDetailData(null);
      }
    } catch (e) {
      console.error('Failed to load detail:', e);
      setDetailData(null);
    }
  }

  function downloadReport() {
    const blob = new Blob([report], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const dateStr = new Date().toISOString().slice(0, 10);
    a.download = `apr_report_nyos_${dateStr}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function printReport() {
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`<html><head><title>NYOS APR Report</title><style>body{font-family:Arial,sans-serif;padding:40px;max-width:800px;margin:0 auto}h1,h2,h3,h4{color:#1e40af}ul{margin-left:20px}</style></head><body>${parseMarkdown(report)}</body></html>`);
    printWindow.document.close();
    printWindow.print();
  }

  async function generateAPRPdf() {
    setAprStatus('generating');
    setAprMessage('Generating APR report with AI analysis...');
    
    try {
      // First, generate the APR report
      const result = await api.generateAPR(aprYear, false);
      if (!result || result.status === 'failed') {
        throw new Error(result?.error || 'Failed to generate APR');
      }
      
      setAprMessage('APR generated! Preparing PDF with logo...');
      setAprStatus('downloading');
      
      // Now download the PDF
      const blob = await api.downloadAPRPdf(aprYear);
      
      // Trigger download
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `APR_${aprYear}_Paracetamol_500mg_NYOS.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      setAprStatus('ready');
      setAprMessage('PDF downloaded successfully!');
      setTimeout(() => {
        setShowReportConfig(false);
        setAprStatus(null);
        setAprMessage('');
      }, 2000);
      
    } catch (err) {
      console.error('APR generation failed:', err);
      setAprStatus(null);
      setAprMessage(`Error: ${err.message}`);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-500">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (!analytics?.has_data) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-8 text-center">
        <AlertTriangle className="mx-auto text-yellow-500 mb-4" size={56} />
        <h3 className="font-semibold text-yellow-800 text-xl mb-2">No data available</h3>
        <p className="text-yellow-600 mb-4">
          Import data via the "Import Data" tab to start the analysis.
        </p>
        <p className="text-sm text-yellow-500">
          Use CSV files generated in the apr_data/ folder
        </p>
      </div>
    );
  }

  const criticalIssues = (anomalies?.critical || 0) + (analytics?.compliance?.overdue_capas || 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Quality Dashboard</h2>
          <p className="text-xs sm:text-sm text-gray-500">
            Period: {analytics?.period?.start?.slice(0,10)} - {analytics?.period?.end?.slice(0,10)} ({analytics?.period?.years} years)
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={generateSummary} disabled={summaryLoading} className="flex items-center gap-1.5 px-3 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors">
            {summaryLoading ? <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div> : <Zap size={16} />}
            <span className="hidden sm:inline">AI</span> Summary
          </button>
          <button onClick={() => setShowReportConfig(true)} disabled={aprStatus !== null} className="flex items-center gap-1.5 px-3 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors">
            {aprStatus ? <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div> : <Download size={16} />}
            APR PDF
          </button>
          <button onClick={() => setShowHistory(true)} className="flex items-center gap-1.5 px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
            <History size={16} />
            History ({reportHistory.length})
          </button>
        </div>
      </div>

      {/* Report Configuration Modal */}
      {showReportConfig && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl w-full max-w-md p-4 sm:p-6 mx-2 sm:mx-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-lg flex items-center gap-2">
                <FileText size={20} className="text-green-600" /> Generate APR Report (PDF)
              </h3>
              <button onClick={() => { setShowReportConfig(false); setAprStatus(null); setAprMessage(''); }} className="p-2 hover:bg-gray-100 rounded-lg">
                <X size={20} />
              </button>
            </div>
            
            <div className="space-y-4">
              {/* Logo Preview */}
              <div className="bg-gradient-to-r from-blue-900 to-blue-700 rounded-lg p-4 flex items-center gap-3">
                <img src="/logo-icon.svg" alt="NYOS Logo" className="w-12 h-12 bg-white rounded-lg p-1" />
                <div className="text-white">
                  <div className="font-bold text-lg">NYOS PharmaCo Global</div>
                  <div className="text-blue-200 text-sm">Annual Product Review</div>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Report Year</label>
                <select
                  value={aprYear}
                  onChange={(e) => setAprYear(parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  disabled={aprStatus !== null}
                >
                  {[2020, 2021, 2022, 2023, 2024, 2025, 2026].map(y => (
                    <option key={y} value={y}>{y}</option>
                  ))}
                </select>
              </div>
              
              <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
                <h4 className="font-medium text-blue-900 text-sm mb-2">PDF Report Includes:</h4>
                <ul className="text-xs text-blue-700 space-y-1">
                  <li>✓ Cover page with NYOS logo</li>
                  <li>✓ Executive summary with KPIs</li>
                  <li>✓ Production & quality analysis</li>
                  <li>✓ Complaints & CAPA review</li>
                  <li>✓ Equipment & stability status</li>
                  <li>✓ Trend analysis & recommendations</li>
                  <li>✓ Professional signature page</li>
                </ul>
              </div>
              
              {/* Status Messages */}
              {aprMessage && (
                <div className={`p-3 rounded-lg text-sm ${
                  aprStatus === 'ready' ? 'bg-green-50 text-green-700 border border-green-200' :
                  aprMessage.startsWith('Error') ? 'bg-red-50 text-red-700 border border-red-200' :
                  'bg-blue-50 text-blue-700 border border-blue-200'
                }`}>
                  {aprStatus === 'generating' || aprStatus === 'downloading' ? (
                    <span className="flex items-center gap-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current"></div>
                      {aprMessage}
                    </span>
                  ) : aprStatus === 'ready' ? (
                    <span className="flex items-center gap-2">
                      <CheckCircle size={16} />
                      {aprMessage}
                    </span>
                  ) : (
                    aprMessage
                  )}
                </div>
              )}
              
              <div className="flex gap-2 pt-2">
                <button
                  onClick={() => { setShowReportConfig(false); setAprStatus(null); setAprMessage(''); }}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                  disabled={aprStatus === 'generating' || aprStatus === 'downloading'}
                >
                  Cancel
                </button>
                <button
                  onClick={generateAPRPdf}
                  disabled={aprStatus !== null}
                  className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {aprStatus ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  ) : (
                    <Download size={18} />
                  )}
                  {aprStatus ? 'Processing...' : 'Generate PDF'}
                </button>
              </div>
              
              <p className="text-xs text-gray-500 text-center">
                AI-powered analysis using data uploaded for the selected year
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Report History Modal */}
      {showHistory && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl w-full max-w-2xl max-h-[85vh] sm:max-h-[80vh] flex flex-col mx-2 sm:mx-auto">
            <div className="p-3 sm:p-4 border-b flex items-center justify-between">
              <h3 className="font-bold text-base sm:text-lg flex items-center gap-2">
                <History size={20} /> Report History
              </h3>
              <button onClick={() => setShowHistory(false)} className="p-2 hover:bg-gray-100 rounded-lg">
                <X size={20} />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              {reportHistory.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No reports generated yet.</p>
              ) : (
                <div className="space-y-2">
                  {reportHistory.map((r) => (
                    <div key={r.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100">
                      <div className="flex-1">
                        <p className="font-medium">{r.title}</p>
                        <p className="text-sm text-gray-500">
                          {r.period_start && r.period_end 
                            ? `${r.period_start.slice(0,10)} - ${r.period_end.slice(0,10)}`
                            : 'All data'
                          }
                          {' • '}
                          {new Date(r.generated_at).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => loadSavedReport(r.id)}
                          className="p-2 text-primary-600 hover:bg-primary-100 rounded-lg"
                          title="View"
                        >
                          <Eye size={18} />
                        </button>
                        <button
                          onClick={() => deleteReport(r.id)}
                          className="p-2 text-red-600 hover:bg-red-100 rounded-lg"
                          title="Delete"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Critical Alert Banner */}
      {criticalIssues > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-4">
          <div className="p-3 bg-red-100 rounded-full">
            <AlertCircle className="text-red-600" size={24} />
          </div>
          <div className="flex-1">
            <p className="font-semibold text-red-800">Warning: {criticalIssues} critical issue(s)</p>
            <p className="text-sm text-red-600">
              {anomalies?.critical || 0} critical anomalies, {analytics?.compliance?.overdue_capas || 0} overdue CAPAs
            </p>
          </div>
        </div>
      )}

      {/* AI Summary */}
      {summary && (
        <div className="bg-gradient-to-r from-primary-50 to-blue-50 border border-primary-200 rounded-xl p-4 sm:p-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-primary-900 flex items-center gap-2">
              <Zap size={20} className="text-primary-600" /> AI Executive Summary
            </h3>
            <div className="flex items-center gap-2">
              <button 
                onClick={() => setSummaryMinimized(!summaryMinimized)} 
                className="p-1.5 hover:bg-primary-100 rounded-lg transition-colors text-primary-600"
                title={summaryMinimized ? "Expand" : "Minimize"}
              >
                {summaryMinimized ? <ChevronDown size={20} /> : <ChevronUp size={20} />}
              </button>
              <button 
                onClick={() => setSummary('')} 
                className="p-1.5 hover:bg-red-100 rounded-lg transition-colors text-red-500"
                title="Close"
              >
                <X size={20} />
              </button>
            </div>
          </div>
          {!summaryMinimized && (
            <div className="text-gray-700 prose max-w-none" dangerouslySetInnerHTML={{ __html: parseMarkdown(summary) }} />
          )}
          {summaryMinimized && (
            <p className="text-sm text-gray-500 italic">Click to expand the summary</p>
          )}
        </div>
      )}

      {/* Quality Score & Main KPIs */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Quality Score */}
        <div className="bg-white rounded-xl p-4 sm:p-6 border border-gray-200 flex flex-col items-center justify-center">
          <h3 className="text-sm font-medium text-gray-500 mb-3 sm:mb-4">Overall Quality Score</h3>
          <QualityGauge score={analytics?.quality?.quality_score || 0} />
        </div>

        {/* Main KPIs */}
        <div className="lg:col-span-3 grid grid-cols-2 sm:grid-cols-3 gap-3 sm:gap-4">
          <KPICard 
            icon={Factory} 
            label="Batches Produced" 
            value={analytics?.production?.total_batches?.toLocaleString() || 0}
            subtext={`${analytics?.production?.recent_batches || 0} this month`}
            color="blue"
            hasDetails={true}
            onClick={() => loadDetailData('batches')}
          />
          <KPICard 
            icon={Target} 
            label="Average Yield" 
            value={`${analytics?.production?.avg_yield || 0}%`}
            trend={analytics?.production?.recent_yield > analytics?.production?.avg_yield ? 'up' : 'down'}
            trendValue={((analytics?.production?.recent_yield - analytics?.production?.avg_yield) || 0).toFixed(1)}
            color="green"
          />
          <KPICard 
            icon={CheckCircle} 
            label="QC Pass Rate" 
            value={`${analytics?.quality?.pass_rate || 0}%`}
            color={analytics?.quality?.pass_rate >= 99 ? 'green' : 'yellow'}
          />
          <KPICard 
            icon={AlertTriangle} 
            label="Open Complaints" 
            value={analytics?.compliance?.open_complaints || 0}
            subtext={`${analytics?.compliance?.critical_complaints || 0} critical`}
            color={analytics?.compliance?.open_complaints > 5 ? 'red' : 'yellow'}
            hasDetails={true}
            onClick={() => loadDetailData('complaints')}
          />
          <KPICard 
            icon={FileWarning} 
            label="Open CAPAs" 
            value={analytics?.compliance?.open_capas || 0}
            subtext={`${analytics?.compliance?.overdue_capas || 0} overdue`}
            color={analytics?.compliance?.overdue_capas > 0 ? 'red' : 'yellow'}
            hasDetails={true}
            onClick={() => loadDetailData('capas')}
          />
          <KPICard 
            icon={Wrench} 
            label="Calibrations OK" 
            value={`${analytics?.equipment?.calibration_pass_rate || 0}%`}
            color={analytics?.equipment?.failed_calibrations > 0 ? 'yellow' : 'green'}
            hasDetails={true}
            onClick={() => loadDetailData('equipment')}
          />
        </div>
      </div>

      {/* Detail Modal for KPI clicks */}
      <DetailModal
        isOpen={selectedDetail !== null}
        onClose={() => { setSelectedDetail(null); setDetailData(null); }}
        title={
          selectedDetail === 'complaints' ? 'Complaints Details' :
          selectedDetail === 'capas' ? 'CAPAs Details' :
          selectedDetail === 'equipment' ? 'Equipment Analysis' :
          selectedDetail === 'batches' ? 'Recent Batches' : 'Details'
        }
      >
        {selectedDetail === 'complaints' && detailData && (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-2 sm:gap-4 mb-4">
              <div className="bg-red-50 p-3 rounded-lg text-center">
                <p className="text-2xl font-bold text-red-600">{detailData.filter(c => c.status?.toLowerCase() === 'open').length}</p>
                <p className="text-sm text-red-700">Open</p>
              </div>
              <div className="bg-yellow-50 p-3 rounded-lg text-center">
                <p className="text-2xl font-bold text-yellow-600">{detailData.filter(c => c.severity?.toLowerCase() === 'critical').length}</p>
                <p className="text-sm text-yellow-700">Critical</p>
              </div>
              <div className="bg-green-50 p-3 rounded-lg text-center">
                <p className="text-2xl font-bold text-green-600">{detailData.filter(c => c.status?.toLowerCase() === 'closed').length}</p>
                <p className="text-sm text-green-700">Closed</p>
              </div>
            </div>
            <div className="max-h-80 overflow-y-auto space-y-2">
              {detailData.slice(0, 20).map((c, i) => (
                <div key={i} className={`p-3 rounded-lg border ${c.status?.toLowerCase() === 'open' ? 'bg-red-50 border-red-200' : 'bg-gray-50 border-gray-200'}`}>
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium">{c.complaint_id}</p>
                      <p className="text-sm text-gray-600">{c.category} - {c.description?.slice(0, 100)}...</p>
                      <p className="text-xs text-gray-400 mt-1">Batch: {c.batch_id} | {c.complaint_date?.slice(0,10)}</p>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded ${
                      c.severity?.toLowerCase() === 'critical' ? 'bg-red-200 text-red-700' : 'bg-yellow-200 text-yellow-700'
                    }`}>{c.severity}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {selectedDetail === 'capas' && detailData && (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-2 sm:gap-4 mb-4">
              <div className="bg-yellow-50 p-3 rounded-lg text-center">
                <p className="text-2xl font-bold text-yellow-600">{detailData.filter(c => !c.status?.toLowerCase().includes('closed')).length}</p>
                <p className="text-sm text-yellow-700">Open</p>
              </div>
              <div className="bg-red-50 p-3 rounded-lg text-center">
                <p className="text-2xl font-bold text-red-600">{detailData.filter(c => c.status?.toLowerCase() === 'overdue').length}</p>
                <p className="text-sm text-red-700">Overdue</p>
              </div>
              <div className="bg-green-50 p-3 rounded-lg text-center">
                <p className="text-2xl font-bold text-green-600">{detailData.filter(c => c.status?.toLowerCase().includes('closed')).length}</p>
                <p className="text-sm text-green-700">Closed</p>
              </div>
            </div>
            <div className="max-h-80 overflow-y-auto space-y-2">
              {detailData.slice(0, 20).map((c, i) => (
                <div key={i} className={`p-3 rounded-lg border ${
                  c.status?.toLowerCase() === 'overdue' ? 'bg-red-50 border-red-200' : 
                  !c.status?.toLowerCase().includes('closed') ? 'bg-yellow-50 border-yellow-200' : 
                  'bg-gray-50 border-gray-200'
                }`}>
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium">{c.capa_id}</p>
                      <p className="text-sm text-gray-600">{c.problem_statement?.slice(0, 100)}...</p>
                      <p className="text-xs text-gray-400 mt-1">Source: {c.source} | Owner: {c.capa_owner}</p>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded ${
                      c.risk_score === 'Critical' ? 'bg-red-200 text-red-700' : 'bg-gray-200 text-gray-700'
                    }`}>{c.risk_score}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {selectedDetail === 'equipment' && detailData && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="bg-green-50 p-3 rounded-lg text-center">
                <p className="text-2xl font-bold text-green-600">{detailData.pass_rate || 0}%</p>
                <p className="text-sm text-green-700">Pass Rate</p>
              </div>
              <div className="bg-red-50 p-3 rounded-lg text-center">
                <p className="text-2xl font-bold text-red-600">{detailData.failed_count || 0}</p>
                <p className="text-sm text-red-700">Failed</p>
              </div>
            </div>
            {detailData.by_type && (
              <div>
                <h4 className="font-medium mb-2">By Equipment Type</h4>
                <div className="space-y-2">
                  {Object.entries(detailData.by_type).map(([type, data]) => (
                    <div key={type} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span>{type}</span>
                      <span className="font-medium">{data.count} calibrations</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
        
        {selectedDetail === 'batches' && detailData && (
          <div className="space-y-4">
            <p className="text-sm text-gray-500 mb-2">Recent {detailData.length} batches</p>
            <div className="max-h-80 overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="text-left p-2">Batch ID</th>
                    <th className="text-left p-2">Date</th>
                    <th className="text-left p-2">Press</th>
                    <th className="text-right p-2">Yield</th>
                    <th className="text-right p-2">Hardness</th>
                  </tr>
                </thead>
                <tbody>
                  {detailData.slice(0, 30).map((b, i) => (
                    <tr key={i} className="border-t border-gray-100">
                      <td className="p-2 font-mono text-xs">{b.batch_id}</td>
                      <td className="p-2">{b.manufacturing_date?.slice(0,10)}</td>
                      <td className="p-2">{b.tablet_press_id}</td>
                      <td className={`p-2 text-right ${b.yield_percent < 95 ? 'text-red-600' : 'text-green-600'}`}>
                        {b.yield_percent?.toFixed(1)}%
                      </td>
                      <td className="p-2 text-right">{b.hardness?.toFixed(1)} kp</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        
        {!detailData && (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          </div>
        )}
      </DetailModal>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        {/* Yearly Trends */}
        {yearly?.years?.length > 0 && (
          <div className="bg-white rounded-xl p-4 sm:p-6 border border-gray-200">
            <h3 className="font-semibold text-gray-900 mb-4">Annual Yield Evolution</h3>
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={yearly.years}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="year" stroke="#6b7280" fontSize={12} />
                <YAxis stroke="#6b7280" fontSize={12} domain={[90, 100]} />
                <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }} />
                <Area type="monotone" dataKey="avg_yield" name="Yield %" stroke="#22c55e" fill="#22c55e" fillOpacity={0.2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Complaints by Year */}
        {yearly?.years?.length > 0 && (
          <div className="bg-white rounded-xl p-4 sm:p-6 border border-gray-200">
            <h3 className="font-semibold text-gray-900 mb-4">Complaints by Year</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={yearly.years}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="year" stroke="#6b7280" fontSize={12} />
                <YAxis stroke="#6b7280" fontSize={12} />
                <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }} />
                <Bar dataKey="complaints" name="Complaints" fill="#f97316" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Drifts & Anomalies */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        {/* Drift Detection */}
        <div className="bg-white rounded-xl p-4 sm:p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">Drift Detection</h3>
            {drifts?.total_alerts > 0 && (
              <span className="bg-yellow-100 text-yellow-700 px-2 py-1 rounded-full text-sm">
                {drifts.total_alerts} alert(s)
              </span>
            )}
          </div>
          <p className="text-sm text-gray-500 mb-4">{drifts?.period}</p>
          <div className="space-y-3">
            {drifts?.drifts?.slice(0, 4).map((drift, i) => (
              <DriftCard key={i} drift={drift} />
            ))}
            {(!drifts?.drifts || drifts.drifts.length === 0) && (
              <p className="text-gray-400 text-center py-4">No significant drift detected</p>
            )}
          </div>
        </div>

        {/* Recent Anomalies */}
        <div className="bg-white rounded-xl p-4 sm:p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">Recent Anomalies</h3>
            <span className={`px-2 py-1 rounded-full text-sm ${
              anomalies?.critical > 0 ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-600'
            }`}>
              {anomalies?.total || 0} detected
            </span>
          </div>
          <p className="text-sm text-gray-500 mb-4">{anomalies?.period}</p>
          <div className="max-h-64 overflow-y-auto">
            {anomalies?.anomalies?.slice(0, 6).map((a, i) => (
              <AnomalyItem key={i} anomaly={a} />
            ))}
            {(!anomalies?.anomalies || anomalies.anomalies.length === 0) && (
              <p className="text-gray-400 text-center py-4">No recent anomalies</p>
            )}
          </div>
        </div>
      </div>

      {/* Supplier Performance */}
      {suppliers?.suppliers?.length > 0 && (
        <div className="bg-white rounded-xl p-4 sm:p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900 flex items-center gap-2 text-sm sm:text-base">
              <Truck size={18} /> Supplier Performance
            </h3>
            {suppliers.at_risk > 0 && (
              <span className="bg-red-100 text-red-700 px-2 py-1 rounded-full text-sm">
                {suppliers.at_risk} at risk
              </span>
            )}
          </div>
          <div className="overflow-x-auto -mx-4 sm:mx-0">
            <table className="w-full text-xs sm:text-sm min-w-[480px]">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 px-2 font-medium text-gray-500">Supplier</th>
                  <th className="text-center py-2 px-1 font-medium text-gray-500">Deliveries</th>
                  <th className="text-center py-2 px-1 font-medium text-gray-500 hidden sm:table-cell">Approved</th>
                  <th className="text-center py-2 px-1 font-medium text-gray-500 hidden sm:table-cell">Rejected</th>
                  <th className="text-center py-2 px-1 font-medium text-gray-500">Rate</th>
                  <th className="text-center py-2 px-1 font-medium text-gray-500">Status</th>
                </tr>
              </thead>
              <tbody>
                {suppliers.suppliers.slice(0, 5).map((s, i) => (
                  <tr key={i} className="border-b border-gray-100">
                    <td className="py-2 px-2 font-medium truncate max-w-[120px]">{s.supplier_name || s.supplier_id}</td>
                    <td className="text-center py-2 px-1">{s.total_deliveries}</td>
                    <td className="text-center py-2 px-1 text-green-600 hidden sm:table-cell">{s.approved}</td>
                    <td className="text-center py-2 px-1 text-red-600 hidden sm:table-cell">{s.rejected}</td>
                    <td className="text-center py-2 px-1 font-medium">{s.approval_rate}%</td>
                    <td className="text-center py-2">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        s.status === 'good' ? 'bg-green-100 text-green-700' :
                        s.status === 'warning' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {s.status === 'good' ? 'OK' : s.status === 'warning' ? 'Warning' : 'Critical'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Report Modal */}
      {showReport && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl w-full max-w-4xl max-h-[90vh] flex flex-col mx-2 sm:mx-auto">
            <div className="p-3 sm:p-4 border-b flex items-center justify-between gap-2">
              <h3 className="font-bold text-base sm:text-lg truncate">Full APR Report</h3>
              <div className="flex gap-1 sm:gap-2 flex-shrink-0">
                <button onClick={downloadReport} className="flex items-center gap-1 px-2 sm:px-3 py-1 bg-gray-100 rounded hover:bg-gray-200 text-xs sm:text-sm">
                  <Download size={14} /> <span className="hidden sm:inline">.md</span>
                </button>
                <button onClick={printReport} className="flex items-center gap-1 px-2 sm:px-3 py-1 bg-primary-600 text-white rounded hover:bg-primary-700 text-xs sm:text-sm">
                  <FileText size={14} /> PDF
                </button>
                <button onClick={() => setShowReport(false)} className="px-2 sm:px-3 py-1 text-gray-500 hover:bg-gray-100 rounded">X</button>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-4 sm:p-6 prose max-w-none text-sm sm:text-base" dangerouslySetInnerHTML={{ __html: parseMarkdown(report) }} />
          </div>
        </div>
      )}
    </div>
  );
}
