import { useState, useEffect } from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  ReferenceLine, AreaChart, Area, BarChart, Bar, ComposedChart 
} from 'recharts';
import { 
  TrendingUp, TrendingDown, Minus, AlertTriangle, BarChart3, 
  Calendar, RefreshCw, Filter, Activity, Target, Layers
} from 'lucide-react';
import { api } from '../api';

const parameters = [
  { id: 'hardness', label: 'Hardness', unit: 'kp', min: 6, max: 20, target: 12, spec_min: 8, spec_max: 16 },
  { id: 'yield_percent', label: 'Yield', unit: '%', min: 90, max: 100, target: 98, spec_min: 95, spec_max: 100 },
  { id: 'compression_force', label: 'Compression Force', unit: 'kN', min: 10, max: 30, target: 20, spec_min: 15, spec_max: 25 },
  { id: 'weight', label: 'Weight', unit: 'mg', min: 480, max: 520, target: 500, spec_min: 490, spec_max: 510 },
  { id: 'thickness', label: 'Thickness', unit: 'mm', min: 4, max: 6, target: 5, spec_min: 4.5, spec_max: 5.5 },
];

const timeRanges = [
  { value: 7, label: '7 days' },
  { value: 30, label: '30 days' },
  { value: 90, label: '3 months' },
  { value: 180, label: '6 months' },
  { value: 365, label: '1 year' },
  { value: 730, label: '2 years' },
];

function StatBox({ label, value, unit, color = 'gray' }) {
  const colors = {
    gray: 'bg-gray-50 border-gray-200',
    green: 'bg-green-50 border-green-200 text-green-700',
    yellow: 'bg-yellow-50 border-yellow-200 text-yellow-700',
    red: 'bg-red-50 border-red-200 text-red-700',
  };
  
  return (
    <div className={`p-3 rounded-lg border ${colors[color]}`}>
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-lg font-bold">{value}{unit && <span className="text-sm font-normal ml-1">{unit}</span>}</p>
    </div>
  );
}

export default function Trends() {
  const [selectedParams, setSelectedParams] = useState(['hardness']);
  const [days, setDays] = useState(90);
  const [trendsData, setTrendsData] = useState({});
  const [loading, setLoading] = useState(true);
  const [comparison, setComparison] = useState(null);
  const [equipment, setEquipment] = useState(null);
  const [showMultiParam, setShowMultiParam] = useState(false);

  useEffect(() => {
    loadTrends();
    loadComparison();
    loadEquipment();
  }, [selectedParams, days]);

  async function loadTrends() {
    setLoading(true);
    try {
      const promises = selectedParams.map(param => 
        api.getTrends(param, days).then(data => ({ param, data }))
      );
      const results = await Promise.all(promises);
      const newData = {};
      results.forEach(({ param, data }) => {
        newData[param] = data;
      });
      setTrendsData(newData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function loadComparison() {
    try {
      const data = await api.getPeriodComparison();
      setComparison(data);
    } catch (e) {
      console.error(e);
    }
  }

  async function loadEquipment() {
    try {
      const data = await api.getEquipmentAnalysis();
      setEquipment(data);
    } catch (e) {
      console.error(e);
    }
  }

  const toggleParam = (paramId) => {
    if (selectedParams.includes(paramId)) {
      if (selectedParams.length > 1) {
        setSelectedParams(selectedParams.filter(p => p !== paramId));
      }
    } else {
      if (showMultiParam) {
        setSelectedParams([...selectedParams, paramId]);
      } else {
        setSelectedParams([paramId]);
      }
    }
  };

  const mainParam = parameters.find(p => p.id === selectedParams[0]);
  const mainData = trendsData[selectedParams[0]];
  
  const chartData = mainData?.dates?.map((date, i) => {
    const point = { date: date.slice(5) };
    selectedParams.forEach((param, idx) => {
      if (trendsData[param]?.values) {
        point[param] = trendsData[param].values[i];
      }
    });
    return point;
  }) || [];

  const colors = ['#2563eb', '#22c55e', '#f97316', '#8b5cf6', '#ec4899'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Trend Analysis</h2>
          <p className="text-xs sm:text-sm text-gray-500">Monitoring critical production parameters</p>
        </div>
        <div className="flex items-center gap-2 sm:gap-3">
          <button
            onClick={() => setShowMultiParam(!showMultiParam)}
            className={`flex items-center gap-1.5 px-2.5 sm:px-3 py-2 rounded-lg border transition-colors text-sm ${
              showMultiParam ? 'bg-primary-100 border-primary-300 text-primary-700' : 'bg-white border-gray-300 text-gray-600'
            }`}
          >
            <Layers size={16} />
            <span className="hidden sm:inline">Multi-parameter</span>
            <span className="sm:hidden">Multi</span>
          </button>
          <button onClick={loadTrends} className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg">
            <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-xl p-4 border border-gray-200">
        <div className="flex flex-wrap items-center gap-4">
          {/* Parameters */}
          <div className="flex-1">
            <p className="text-xs text-gray-500 mb-2 flex items-center gap-1">
              <Filter size={12} /> Parameters
            </p>
            <div className="flex flex-wrap gap-2">
              {parameters.map(p => (
                <button
                  key={p.id}
                  onClick={() => toggleParam(p.id)}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                    selectedParams.includes(p.id)
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* Time Range */}
          <div>
            <p className="text-xs text-gray-500 mb-2 flex items-center gap-1">
              <Calendar size={12} /> Period
            </p>
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {timeRanges.map(t => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Alert Banner */}
      {mainData?.alert && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 flex items-center gap-3">
          <AlertTriangle className="text-yellow-500 flex-shrink-0" size={24} />
          <div>
            <p className="font-semibold text-yellow-800">Significant trend detected</p>
            <p className="text-yellow-600 text-sm">
              {mainParam?.label} shows a {mainData.trend_direction === 'hausse' ? 'upward' : 'downward'} trend over this period
            </p>
          </div>
        </div>
      )}

      {/* Main Chart */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 sm:mb-6">
          <div>
            <h3 className="font-semibold text-gray-900">
              {showMultiParam ? 'Multi-parameter Comparison' : mainParam?.label}
            </h3>
            <p className="text-xs sm:text-sm text-gray-500">
              Last {days} days
              {mainData?.values?.length > 0 && ` - ${mainData.values.length} data points`}
            </p>
          </div>

          {/* Stats */}
          {mainData && !mainData.error && (
            <div className="flex items-center gap-2 sm:gap-3">
              <StatBox label="Average" value={mainData.average} unit={mainParam?.unit} />
              <StatBox
                label="Trend"
                value={mainData.trend_direction === 'hausse' ? '\u2191' : mainData.trend_direction === 'baisse' ? '\u2193' : '\u2192'}
                color={mainData.alert ? 'yellow' : 'green'}
              />
            </div>
          )}
        </div>

        {loading ? (
          <div className="h-80 flex items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        ) : mainData?.error ? (
          <div className="h-80 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <AlertTriangle size={48} className="mx-auto mb-3 text-yellow-500" />
              <p>{mainData.error}</p>
              <p className="text-sm mt-2">Import data to view trends</p>
            </div>
          </div>
        ) : chartData.length === 0 ? (
          <div className="h-80 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <BarChart3 size={48} className="mx-auto mb-3 text-gray-300" />
              <p>No data available</p>
            </div>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <ComposedChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="date" 
                stroke="#6b7280" 
                fontSize={12}
                tickLine={false}
              />
              <YAxis 
                stroke="#6b7280" 
                fontSize={12}
                domain={[mainParam?.min || 'auto', mainParam?.max || 'auto']}
                tickLine={false}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'white', 
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
              />
              
              {/* Spec limits */}
              {mainParam?.spec_min && (
                <ReferenceLine 
                  y={mainParam.spec_min} 
                  stroke="#ef4444" 
                  strokeDasharray="5 5" 
                  label={{ value: 'Min', position: 'left', fill: '#ef4444', fontSize: 10 }}
                />
              )}
              {mainParam?.spec_max && (
                <ReferenceLine 
                  y={mainParam.spec_max} 
                  stroke="#ef4444" 
                  strokeDasharray="5 5" 
                  label={{ value: 'Max', position: 'left', fill: '#ef4444', fontSize: 10 }}
                />
              )}
              {mainParam?.target && (
                <ReferenceLine 
                  y={mainParam.target} 
                  stroke="#22c55e" 
                  strokeDasharray="3 3" 
                  label={{ value: 'Target', position: 'left', fill: '#22c55e', fontSize: 10 }}
                />
              )}
              
              {/* Data lines */}
              {selectedParams.map((param, i) => (
                <Line 
                  key={param}
                  type="monotone" 
                  dataKey={param} 
                  name={parameters.find(p => p.id === param)?.label}
                  stroke={colors[i % colors.length]} 
                  strokeWidth={2}
                  dot={chartData.length < 50}
                  activeDot={{ r: 6 }}
                />
              ))}
            </ComposedChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Period Comparison */}
      {comparison && !comparison.error && (
        <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Activity size={20} /> Period Comparison
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
            <div className="p-3 sm:p-4 bg-gray-50 rounded-lg">
              <p className="text-xs sm:text-sm text-gray-500 mb-1">Batches produced</p>
              <p className="text-xl sm:text-2xl font-bold">{comparison.period1?.batches}</p>
              <p className={`text-sm ${comparison.changes?.batches_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {comparison.changes?.batches_pct >= 0 ? '+' : ''}{comparison.changes?.batches_pct}% vs previous period
              </p>
            </div>
            <div className="p-3 sm:p-4 bg-gray-50 rounded-lg">
              <p className="text-xs sm:text-sm text-gray-500 mb-1">Average yield</p>
              <p className="text-xl sm:text-2xl font-bold">{comparison.period1?.avg_yield}%</p>
              <p className={`text-sm ${comparison.changes?.yield_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {comparison.changes?.yield_pct >= 0 ? '+' : ''}{comparison.changes?.yield_pct}%
              </p>
            </div>
            <div className="p-3 sm:p-4 bg-gray-50 rounded-lg">
              <p className="text-xs sm:text-sm text-gray-500 mb-1">Average hardness</p>
              <p className="text-xl sm:text-2xl font-bold">{comparison.period1?.avg_hardness} kp</p>
              <p className={`text-sm ${comparison.changes?.hardness_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {comparison.changes?.hardness_pct >= 0 ? '+' : ''}{comparison.changes?.hardness_pct}%
              </p>
            </div>
            <div className="p-3 sm:p-4 bg-gray-50 rounded-lg">
              <p className="text-xs sm:text-sm text-gray-500 mb-1">Complaints</p>
              <p className="text-xl sm:text-2xl font-bold">{comparison.period1?.complaints}</p>
              <p className={`text-sm ${comparison.changes?.complaints_pct <= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {comparison.changes?.complaints_pct >= 0 ? '+' : ''}{comparison.changes?.complaints_pct}%
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Equipment Performance */}
      {equipment?.equipment?.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-6">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2 text-sm sm:text-base">
            <Target size={18} /> Performance by Equipment
          </h3>
          <div className="overflow-x-auto -mx-4 sm:mx-0">
            <table className="w-full text-xs sm:text-sm min-w-[420px]">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 font-medium text-gray-500">Equipment</th>
                  <th className="text-center py-2 font-medium text-gray-500">Batches</th>
                  <th className="text-center py-2 font-medium text-gray-500">Avg. Yield</th>
                  <th className="text-center py-2 font-medium text-gray-500">Avg. Hardness</th>
                  <th className="text-center py-2 font-medium text-gray-500">Variability</th>
                </tr>
              </thead>
              <tbody>
                {equipment.equipment.map((eq, i) => (
                  <tr key={i} className="border-b border-gray-100">
                    <td className="py-2 font-medium">{eq.equipment_id}</td>
                    <td className="text-center py-2">{eq.batches}</td>
                    <td className="text-center py-2">
                      <span className={eq.avg_yield < 95 ? 'text-red-600' : eq.avg_yield < 98 ? 'text-yellow-600' : 'text-green-600'}>
                        {eq.avg_yield}%
                      </span>
                    </td>
                    <td className="text-center py-2">{eq.avg_hardness} kp</td>
                    <td className="text-center py-2">
                      <span className={eq.hardness_variability > 10 ? 'text-red-600' : eq.hardness_variability > 5 ? 'text-yellow-600' : 'text-green-600'}>
                        +/-{eq.hardness_variability}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {equipment.lowest_yield && (
            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-700">
                Warning: <strong>{equipment.lowest_yield.equipment_id}</strong> has the lowest yield ({equipment.lowest_yield.avg_yield}%)
              </p>
            </div>
          )}
        </div>
      )}

      {/* Legend */}
      <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Legend</h4>
        <div className="flex flex-wrap gap-4 text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <span className="w-6 h-0.5 bg-green-500" style={{ borderStyle: 'dashed', height: '2px' }}></span>
            Target value
          </div>
          <div className="flex items-center gap-2">
            <span className="w-6 h-0.5 bg-red-500" style={{ borderStyle: 'dashed', height: '2px' }}></span>
            Specification limits
          </div>
          <div className="flex items-center gap-2">
            <span className="w-6 h-0.5 bg-blue-600"></span>
            Measured value
          </div>
        </div>
      </div>
    </div>
  );
}
