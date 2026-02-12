import { useState, useEffect } from 'react';
import { Activity, MessageSquare, Upload, BarChart3, AlertTriangle, CheckCircle, Clock, FileText, Layers, Database } from 'lucide-react';
import { api } from './api';
import Dashboard from './components/Dashboard';
import Chat from './components/Chat';
import DataUpload from './components/DataUpload';
import Trends from './components/Trends';
import Analytics from './components/Analytics';
import Backoffice from './components/Backoffice';

const tabs = [
  { id: 'dashboard', label: 'Dashboard', icon: Activity },
  { id: 'analytics', label: 'Analytics', icon: Layers },
  { id: 'trends', label: 'Trends', icon: BarChart3 },
  { id: 'chat', label: 'AI Assistant', icon: MessageSquare },
  { id: 'upload', label: 'Import Data', icon: Upload },
  { id: 'backoffice', label: 'Generate Data', icon: Database },
];

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3 cursor-pointer" onClick={() => setActiveTab('dashboard')}>
              <img src="/logo-icon.svg" alt="NYOS Logo" className="w-10 h-10" />
              <div>
                <h1 className="text-xl font-bold text-gray-900">NYOS</h1>
                <p className="text-xs text-gray-500">Pharmaceutical Quality Intelligence</p>
              </div>
            </div>
            <nav className="flex gap-1">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                    activeTab === tab.id 
                      ? 'bg-primary-100 text-primary-700 shadow-sm' 
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <tab.icon size={18} />
                  <span className="font-medium">{tab.label}</span>
                </button>
              ))}
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'analytics' && <Analytics />}
        {activeTab === 'trends' && <Trends />}
        {activeTab === 'chat' && <Chat />}
        {activeTab === 'upload' && <DataUpload />}
        {activeTab === 'backoffice' && <Backoffice />}
      </main>
      
      <footer className="border-t border-gray-200 py-4 mt-8">
        <div className="max-w-7xl mx-auto px-4 text-center text-sm text-gray-500">
          NYOS APR v2.0 - Pharmaceutical Quality Analysis Platform
        </div>
      </footer>
    </div>
  );
}
