import { useState, useEffect } from 'react';
import { 
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, PieChart, Pie, Cell, RadarChart, Radar, 
  PolarGrid, PolarAngleAxis, PolarRadiusAxis, Legend
} from 'recharts';
import { 
  Search, Filter, Zap, TrendingUp, AlertTriangle, Users, 
  Factory, FileText, Layers, ArrowRight, ChevronDown
} from 'lucide-react';
import { api } from '../api';

const COLORS = ['#2563eb', '#22c55e', '#f97316', '#8b5cf6', '#ec4899', '#06b6d4'];

export default function Analytics() {
  const [activeTab, setActiveTab] = useState('overview');
  const [overview, setOverview] = useState(null);
  const [yearly, setYearly] = useState(null);
  const [suppliers, setSuppliers] = useState(null);
  const [equipment, setEquipment] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedYears, setSelectedYears] = useState([]);

  useEffect(() => {
    loadAllData();
  }, []);

  // Initialize selectedYears when yearly data loads
  useEffect(() => {
    if (yearly?.years?.length >= 2) {
      // Select last 2 years by default
      const years = yearly.years.map(y => y.year).sort();
      setSelectedYears(years.slice(-2));
    }
  }, [yearly]);

  async function loadAllData() {
    setLoading(true);
    try {
      const [overviewData, yearlyData, suppliersData, equipmentData, comparisonData] = await Promise.all([
        api.getAnalyticsOverview(),
        api.getYearlySummary(),
        api.getSupplierPerformance(),
        api.getEquipmentAnalysis(),
        api.getPeriodComparison()
      ]);
      setOverview(overviewData);
      setYearly(yearlyData);
      setSuppliers(suppliersData);
      setEquipment(equipmentData);
      setComparison(comparisonData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Layers },
    { id: 'production', label: 'Production', icon: Factory },
    { id: 'suppliers', label: 'Suppliers', icon: Users },
    { id: 'equipment', label: 'Equipment', icon: Factory },
    { id: 'comparison', label: 'Comparison', icon: TrendingUp },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-500">Loading advanced analytics...</p>
        </div>
      </div>
    );
  }

  if (!overview?.has_data) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-8 text-center">
        <AlertTriangle className="mx-auto text-yellow-500 mb-4" size={56} />
        <h3 className="font-semibold text-yellow-800 text-xl mb-2">No data available</h3>
        <p className="text-yellow-600">
          Import data to access advanced analytics.
        </p>
      </div>
    );
  }

  // Prepare radar chart data
  const radarData = [
    { metric: 'Yield', value: overview?.production?.avg_yield || 0, fullMark: 100 },
    { metric: 'QC Pass', value: overview?.quality?.pass_rate || 0, fullMark: 100 },
    { metric: 'Calibrations OK', value: overview?.equipment?.calibration_pass_rate || 0, fullMark: 100 },
    { metric: 'Quality Score', value: overview?.quality?.quality_score || 0, fullMark: 100 },
  ];

  // Yearly evolution data
  const yearlyChartData = yearly?.years || [];

  // Supplier pie chart data
  const supplierPieData = suppliers?.suppliers?.slice(0, 5).map(s => ({
    name: s.supplier_name || s.supplier_id,
    value: s.total_deliveries,
    rate: s.approval_rate
  })) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Advanced Analytics</h2>
          <p className="text-sm text-gray-500">
            Detailed insights on {overview?.period?.years} years of data
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-4">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 py-3 px-1 border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <tab.icon size={18} />
              <span className="font-medium">{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Performance Radar */}
          <div className="bg-white rounded-xl p-6 border border-gray-200">
            <h3 className="font-semibold text-gray-900 mb-4">Overall Performance</h3>
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={radarData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="metric" />
                <PolarRadiusAxis angle={30} domain={[0, 100]} />
                <Radar
                  name="Performance"
                  dataKey="value"
                  stroke="#2563eb"
                  fill="#2563eb"
                  fillOpacity={0.3}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          {/* Key Metrics */}
          <div className="bg-white rounded-xl p-6 border border-gray-200">
            <h3 className="font-semibold text-gray-900 mb-4">Key Metrics</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-gray-600">Total batches analyzed</span>
                <span className="text-xl font-bold">{overview?.production?.total_batches?.toLocaleString()}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-gray-600">QC tests performed</span>
                <span className="text-xl font-bold">{overview?.quality?.total_tests?.toLocaleString()}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-gray-600">Total complaints</span>
                <span className="text-xl font-bold">{overview?.compliance?.total_complaints}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-gray-600">CAPAs processed</span>
                <span className="text-xl font-bold">{overview?.compliance?.total_capas}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                <span className="text-green-700">Overall quality score</span>
                <span className="text-xl font-bold text-green-700">{overview?.quality?.quality_score}/100</span>
              </div>
            </div>
          </div>

          {/* Yearly Evolution */}
          {yearlyChartData.length > 0 && (
            <div className="bg-white rounded-xl p-6 border border-gray-200 lg:col-span-2">
              <h3 className="font-semibold text-gray-900 mb-4">6-Year Evolution</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={yearlyChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="year" stroke="#6b7280" />
                  <YAxis yAxisId="left" stroke="#6b7280" />
                  <YAxis yAxisId="right" orientation="right" stroke="#6b7280" />
                  <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }} />
                  <Legend />
                  <Line yAxisId="left" type="monotone" dataKey="batches" name="Batches" stroke="#2563eb" strokeWidth={2} />
                  <Line yAxisId="right" type="monotone" dataKey="complaints" name="Complaints" stroke="#ef4444" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* Production Tab */}
      {activeTab === 'production' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <p className="text-sm text-gray-500 mb-1">Total production</p>
              <p className="text-3xl font-bold text-gray-900">{overview?.production?.total_batches?.toLocaleString()}</p>
              <p className="text-sm text-gray-400 mt-1">batches over {overview?.period?.years} years</p>
            </div>
            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <p className="text-sm text-gray-500 mb-1">Average yield</p>
              <p className="text-3xl font-bold text-green-600">{overview?.production?.avg_yield}%</p>
              <p className="text-sm text-gray-400 mt-1">
                Min: {overview?.production?.yield_range?.min}% | Max: {overview?.production?.yield_range?.max}%
              </p>
            </div>
            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <p className="text-sm text-gray-500 mb-1">Monthly production</p>
              <p className="text-3xl font-bold text-gray-900">{overview?.production?.recent_batches}</p>
              <p className="text-sm text-gray-400 mt-1">batches this month</p>
            </div>
          </div>

          {/* Production by Year */}
          {yearlyChartData.length > 0 && (
            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <h3 className="font-semibold text-gray-900 mb-4">Production by Year</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={yearlyChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="year" stroke="#6b7280" />
                  <YAxis stroke="#6b7280" />
                  <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }} />
                  <Bar dataKey="batches" name="Batches" fill="#2563eb" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* Suppliers Tab */}
      {activeTab === 'suppliers' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <p className="text-sm text-gray-500 mb-1">Total suppliers</p>
              <p className="text-3xl font-bold text-gray-900">{suppliers?.total_suppliers}</p>
            </div>
            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <p className="text-sm text-gray-500 mb-1">At-risk suppliers</p>
              <p className="text-3xl font-bold text-red-600">{suppliers?.at_risk}</p>
            </div>
            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <p className="text-sm text-gray-500 mb-1">Average approval rate</p>
              <p className="text-3xl font-bold text-green-600">
                {suppliers?.suppliers?.length > 0
                  ? (suppliers.suppliers.reduce((acc, s) => acc + s.approval_rate, 0) / suppliers.suppliers.length).toFixed(1)
                  : 0}%
              </p>
            </div>
          </div>

          {/* Supplier Table */}
          <div className="bg-white rounded-xl p-6 border border-gray-200">
            <h3 className="font-semibold text-gray-900 mb-4">Performance by Supplier</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 font-medium text-gray-500">Supplier</th>
                    <th className="text-center py-3 font-medium text-gray-500">Deliveries</th>
                    <th className="text-center py-3 font-medium text-gray-500">Approved</th>
                    <th className="text-center py-3 font-medium text-gray-500">Rejected</th>
                    <th className="text-center py-3 font-medium text-gray-500">Quarantine</th>
                    <th className="text-center py-3 font-medium text-gray-500">Rate</th>
                    <th className="text-center py-3 font-medium text-gray-500">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {suppliers?.suppliers?.map((s, i) => (
                    <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 font-medium">{s.supplier_name || s.supplier_id}</td>
                      <td className="text-center py-3">{s.total_deliveries}</td>
                      <td className="text-center py-3 text-green-600">{s.approved}</td>
                      <td className="text-center py-3 text-red-600">{s.rejected}</td>
                      <td className="text-center py-3 text-yellow-600">{s.quarantine}</td>
                      <td className="text-center py-3">
                        <span className={`font-medium ${
                          s.approval_rate >= 98 ? 'text-green-600' :
                          s.approval_rate >= 95 ? 'text-yellow-600' : 'text-red-600'
                        }`}>
                          {s.approval_rate}%
                        </span>
                      </td>
                      <td className="text-center py-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          s.status === 'good' ? 'bg-green-100 text-green-700' :
                          s.status === 'warning' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-red-100 text-red-700'
                        }`}>
                          {s.status === 'good' ? 'Compliant' : s.status === 'warning' ? 'Watch' : 'Critical'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Supplier Distribution Pie */}
          {supplierPieData.length > 0 && (
            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <h3 className="font-semibold text-gray-900 mb-4">Delivery Distribution</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={supplierPieData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {supplierPieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* Equipment Tab */}
      {activeTab === 'equipment' && (
        <div className="space-y-6">
          {equipment?.equipment?.length > 0 && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {equipment.lowest_yield && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
                    <p className="text-sm text-yellow-700 mb-1">Warning: Lowest yield</p>
                    <p className="text-2xl font-bold text-yellow-800">{equipment.lowest_yield.equipment_id}</p>
                    <p className="text-sm text-yellow-600 mt-1">
                      Yield: {equipment.lowest_yield.avg_yield}% | {equipment.lowest_yield.batches} batches
                    </p>
                  </div>
                )}
                {equipment.highest_variability && (
                  <div className="bg-red-50 border border-red-200 rounded-xl p-6">
                    <p className="text-sm text-red-700 mb-1">Warning: Highest variability</p>
                    <p className="text-2xl font-bold text-red-800">{equipment.highest_variability.equipment_id}</p>
                    <p className="text-sm text-red-600 mt-1">
                      Hardness std dev: +/-{equipment.highest_variability.hardness_variability} kp
                    </p>
                  </div>
                )}
              </div>

              <div className="bg-white rounded-xl p-6 border border-gray-200">
                <h3 className="font-semibold text-gray-900 mb-4">Performance by Equipment</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={equipment.equipment}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="equipment_id" stroke="#6b7280" />
                    <YAxis domain={[90, 100]} stroke="#6b7280" />
                    <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }} />
                    <Bar dataKey="avg_yield" name="Yield %" fill="#22c55e" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </>
          )}
        </div>
      )}

      {/* Comparison Tab - Enhanced Multi-Year */}
      {activeTab === 'comparison' && (
        <div className="space-y-6">
          {/* Year Selector */}
          <div className="bg-white rounded-xl p-6 border border-gray-200">
            <h3 className="font-semibold text-gray-900 mb-4">Select Years to Compare</h3>
            <div className="flex flex-wrap gap-2">
              {yearly?.years?.map(y => (
                <button
                  key={y.year}
                  onClick={() => {
                    const years = selectedYears.includes(y.year)
                      ? selectedYears.filter(yr => yr !== y.year)
                      : [...selectedYears, y.year].sort();
                    setSelectedYears(years);
                  }}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    selectedYears.includes(y.year)
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {y.year}
                </button>
              ))}
            </div>
            <p className="text-sm text-gray-500 mt-2">Select 2 or more years to compare</p>
          </div>

          {/* Multi-Year Comparison Charts */}
          {selectedYears.length >= 2 && yearly?.years && (
            <>
              {/* Comparison Table */}
              <div className="bg-white rounded-xl p-6 border border-gray-200 overflow-x-auto">
                <h3 className="font-semibold text-gray-900 mb-4">Detailed Year-over-Year Comparison</h3>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 font-medium text-gray-500">Metric</th>
                      {selectedYears.map(year => (
                        <th key={year} className="text-center py-3 font-medium text-gray-500">{year}</th>
                      ))}
                      <th className="text-center py-3 font-medium text-gray-500">Trend</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { key: 'batches', label: 'Batches Produced', format: v => v?.toLocaleString() },
                      { key: 'avg_yield', label: 'Average Yield (%)', format: v => v?.toFixed(2) + '%' },
                      { key: 'complaints', label: 'Complaints', format: v => v },
                      { key: 'capas', label: 'CAPAs', format: v => v },
                    ].map(metric => {
                      const values = selectedYears.map(year => {
                        const yearData = yearly.years.find(y => y.year === year);
                        return yearData?.[metric.key] || 0;
                      });
                      const trend = values.length >= 2 
                        ? ((values[values.length - 1] - values[0]) / values[0] * 100).toFixed(1)
                        : 0;
                      const trendPositive = metric.key === 'complaints' || metric.key === 'capas'
                        ? trend < 0
                        : trend > 0;
                      
                      return (
                        <tr key={metric.key} className="border-b border-gray-100">
                          <td className="py-3 font-medium">{metric.label}</td>
                          {values.map((v, i) => (
                            <td key={i} className="text-center py-3">{metric.format(v)}</td>
                          ))}
                          <td className={`text-center py-3 font-medium ${trendPositive ? 'text-green-600' : 'text-red-600'}`}>
                            {trend > 0 ? '+' : ''}{trend}%
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Multi-Year Trend Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Production Volume */}
                <div className="bg-white rounded-xl p-6 border border-gray-200">
                  <h3 className="font-semibold text-gray-900 mb-4">Production Volume Trend</h3>
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={yearly.years.filter(y => selectedYears.includes(y.year))}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="year" stroke="#6b7280" />
                      <YAxis stroke="#6b7280" />
                      <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }} />
                      <Bar dataKey="batches" name="Batches" fill="#2563eb" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Yield Evolution */}
                <div className="bg-white rounded-xl p-6 border border-gray-200">
                  <h3 className="font-semibold text-gray-900 mb-4">Yield Evolution</h3>
                  <ResponsiveContainer width="100%" height={250}>
                    <LineChart data={yearly.years.filter(y => selectedYears.includes(y.year))}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="year" stroke="#6b7280" />
                      <YAxis domain={[90, 100]} stroke="#6b7280" />
                      <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }} />
                      <Line type="monotone" dataKey="avg_yield" name="Yield %" stroke="#22c55e" strokeWidth={3} dot={{ fill: '#22c55e', r: 6 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                {/* Quality Issues */}
                <div className="bg-white rounded-xl p-6 border border-gray-200">
                  <h3 className="font-semibold text-gray-900 mb-4">Quality Issues Trend</h3>
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={yearly.years.filter(y => selectedYears.includes(y.year))}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="year" stroke="#6b7280" />
                      <YAxis stroke="#6b7280" />
                      <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }} />
                      <Legend />
                      <Bar dataKey="complaints" name="Complaints" fill="#f97316" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="capas" name="CAPAs" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Multi-metric Radar */}
                <div className="bg-white rounded-xl p-6 border border-gray-200">
                  <h3 className="font-semibold text-gray-900 mb-4">Performance Radar - Latest vs First</h3>
                  {selectedYears.length >= 2 && (
                    <ResponsiveContainer width="100%" height={250}>
                      <RadarChart data={[
                        { 
                          metric: 'Yield', 
                          [selectedYears[0]]: yearly.years.find(y => y.year === selectedYears[0])?.avg_yield || 0,
                          [selectedYears[selectedYears.length - 1]]: yearly.years.find(y => y.year === selectedYears[selectedYears.length - 1])?.avg_yield || 0,
                        },
                        { 
                          metric: 'Production', 
                          [selectedYears[0]]: Math.min(100, (yearly.years.find(y => y.year === selectedYears[0])?.batches || 0) / 100),
                          [selectedYears[selectedYears.length - 1]]: Math.min(100, (yearly.years.find(y => y.year === selectedYears[selectedYears.length - 1])?.batches || 0) / 100),
                        },
                        { 
                          metric: 'Low Complaints', 
                          [selectedYears[0]]: Math.max(0, 100 - (yearly.years.find(y => y.year === selectedYears[0])?.complaints || 0)),
                          [selectedYears[selectedYears.length - 1]]: Math.max(0, 100 - (yearly.years.find(y => y.year === selectedYears[selectedYears.length - 1])?.complaints || 0)),
                        },
                      ]}>
                        <PolarGrid />
                        <PolarAngleAxis dataKey="metric" />
                        <PolarRadiusAxis angle={30} domain={[0, 100]} />
                        <Radar name={selectedYears[0]} dataKey={selectedYears[0]} stroke="#94a3b8" fill="#94a3b8" fillOpacity={0.3} />
                        <Radar name={selectedYears[selectedYears.length - 1]} dataKey={selectedYears[selectedYears.length - 1]} stroke="#2563eb" fill="#2563eb" fillOpacity={0.3} />
                        <Legend />
                      </RadarChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </div>

              {/* Year-over-Year Changes Summary */}
              <div className="bg-gradient-to-r from-primary-50 to-blue-50 rounded-xl p-6 border border-primary-200">
                <h3 className="font-semibold text-primary-900 mb-4">
                  {selectedYears[0]} → {selectedYears[selectedYears.length - 1]} Evolution Summary
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {(() => {
                    const first = yearly.years.find(y => y.year === selectedYears[0]) || {};
                    const last = yearly.years.find(y => y.year === selectedYears[selectedYears.length - 1]) || {};
                    
                    return [
                      { 
                        label: 'Production', 
                        change: first.batches ? ((last.batches - first.batches) / first.batches * 100).toFixed(1) : 0,
                        positive: true
                      },
                      { 
                        label: 'Yield', 
                        change: first.avg_yield ? ((last.avg_yield - first.avg_yield) / first.avg_yield * 100).toFixed(2) : 0,
                        positive: true
                      },
                      { 
                        label: 'Complaints', 
                        change: first.complaints ? ((last.complaints - first.complaints) / first.complaints * 100).toFixed(1) : 0,
                        positive: false
                      },
                      { 
                        label: 'CAPAs', 
                        change: first.capas ? ((last.capas - first.capas) / first.capas * 100).toFixed(1) : 0,
                        positive: false
                      },
                    ].map((item, i) => (
                      <div key={i} className="text-center">
                        <p className={`text-2xl font-bold ${
                          (item.positive ? parseFloat(item.change) >= 0 : parseFloat(item.change) <= 0) 
                            ? 'text-green-600' 
                            : 'text-red-600'
                        }`}>
                          {parseFloat(item.change) >= 0 ? '+' : ''}{item.change}%
                        </p>
                        <p className="text-sm text-gray-600">{item.label}</p>
                      </div>
                    ));
                  })()}
                </div>
              </div>
            </>
          )}

          {/* Original 2-period comparison if no years selected */}
          {selectedYears.length < 2 && comparison && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Period 1 */}
              <div className="bg-white rounded-xl p-6 border border-gray-200">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-gray-900">{comparison.period1?.label}</h3>
                  <span className="text-sm text-gray-500">
                    {comparison.period1?.start} - {comparison.period1?.end}
                  </span>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                    <span>Batches produced</span>
                    <span className="font-bold">{comparison.period1?.batches}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                    <span>Average yield</span>
                    <span className="font-bold text-green-600">{comparison.period1?.avg_yield}%</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                    <span>Average hardness</span>
                    <span className="font-bold">{comparison.period1?.avg_hardness} kp</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                    <span>Complaints</span>
                    <span className="font-bold text-orange-600">{comparison.period1?.complaints}</span>
                  </div>
                </div>
              </div>

              {/* Period 2 */}
              <div className="bg-white rounded-xl p-6 border border-gray-200">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-gray-900">{comparison.period2?.label}</h3>
                  <span className="text-sm text-gray-500">
                    {comparison.period2?.start} - {comparison.period2?.end}
                  </span>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                    <span>Batches produced</span>
                    <span className="font-bold">{comparison.period2?.batches}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                    <span>Average yield</span>
                    <span className="font-bold text-green-600">{comparison.period2?.avg_yield}%</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                    <span>Average hardness</span>
                    <span className="font-bold">{comparison.period2?.avg_hardness} kp</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                    <span>Complaints</span>
                    <span className="font-bold text-orange-600">{comparison.period2?.complaints}</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
