import { useState } from 'react';
import { Activity, MessageSquare, Upload, BarChart3, Layers, Database, Menu, X } from 'lucide-react';
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
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleTabChange = (tabId) => {
    setActiveTab(tabId);
    setMobileMenuOpen(false);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-3 sm:px-4">
          <div className="flex items-center justify-between h-14 sm:h-16">
            <div className="flex items-center gap-2 sm:gap-3 cursor-pointer" onClick={() => handleTabChange('dashboard')}>
              <img src="/logo-icon.svg" alt="NYOS Logo" className="w-8 h-8 sm:w-10 sm:h-10" />
              <div>
                <h1 className="text-lg sm:text-xl font-bold text-gray-900">NYOS</h1>
                <p className="text-xs text-gray-500 hidden sm:block">Pharmaceutical Quality Intelligence</p>
              </div>
            </div>

            {/* Desktop navigation */}
            <nav className="hidden md:flex gap-1">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => handleTabChange(tab.id)}
                  className={`flex items-center gap-2 px-3 lg:px-4 py-2 rounded-lg transition-all text-sm lg:text-base ${
                    activeTab === tab.id
                      ? 'bg-primary-100 text-primary-700 shadow-sm'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <tab.icon size={18} />
                  <span className="font-medium hidden lg:inline">{tab.label}</span>
                </button>
              ))}
            </nav>

            {/* Mobile menu button */}
            <button
              className="md:hidden p-2 rounded-lg text-gray-600 hover:bg-gray-100"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>

        {/* Mobile navigation dropdown */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-gray-100 bg-white shadow-lg">
            <nav className="grid grid-cols-3 gap-1 p-2">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => handleTabChange(tab.id)}
                  className={`flex flex-col items-center gap-1 px-2 py-3 rounded-lg transition-all text-xs ${
                    activeTab === tab.id
                      ? 'bg-primary-100 text-primary-700'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <tab.icon size={20} />
                  <span className="font-medium">{tab.label}</span>
                </button>
              ))}
            </nav>
          </div>
        )}
      </header>

      <main className="max-w-7xl mx-auto px-3 sm:px-4 py-4 sm:py-6">
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'analytics' && <Analytics />}
        {activeTab === 'trends' && <Trends />}
        {activeTab === 'chat' && <Chat />}
        {activeTab === 'upload' && <DataUpload />}
        {activeTab === 'backoffice' && <Backoffice />}
      </main>

      <footer className="border-t border-gray-200 py-4 mt-8">
        <div className="max-w-7xl mx-auto px-3 sm:px-4 text-center text-sm text-gray-500">
          NYOS APR v2.0 - Pharmaceutical Quality Analysis Platform
        </div>
      </footer>
    </div>
  );
}
