import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, Plus, Trash2, MessageSquare, ChevronLeft, History } from 'lucide-react';
import { api } from '../api';

function parseMarkdown(text) {
  if (!text) return '';
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br/>');
}

export default function Chat() {
  const [conversations, setConversations] = useState([]);
  const [currentConvId, setCurrentConvId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => { loadConversations(); }, []);
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  async function loadConversations() {
    try {
      const convs = await api.getConversations();
      setConversations(convs);
      if (convs.length > 0 && !currentConvId) selectConversation(convs[0].id);
    } catch (e) { console.error(e); }
  }

  async function selectConversation(convId) {
    setCurrentConvId(convId);
    setSidebarOpen(false);
    try {
      const history = await api.getChatHistory(convId);
      setMessages(history);
    } catch (e) { setMessages([]); }
  }

  async function createNewConversation() {
    try {
      const conv = await api.createConversation();
      setConversations(prev => [conv, ...prev]);
      setCurrentConvId(conv.id);
      setMessages([]);
      setSidebarOpen(false);
    } catch (e) { console.error(e); }
  }

  async function deleteConversation(convId) {
    try {
      await api.deleteConversation(convId);
      setConversations(prev => prev.filter(c => c.id !== convId));
      if (currentConvId === convId) { setCurrentConvId(null); setMessages([]); }
    } catch (e) { console.error(e); }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!input.trim() || loading) return;
    let convId = currentConvId;
    if (!convId) {
      const conv = await api.createConversation();
      setConversations(prev => [conv, ...prev]);
      convId = conv.id;
      setCurrentConvId(convId);
    }
    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    try {
      const response = await api.chat(convId, input);
      setMessages(prev => [...prev, { role: 'assistant', content: response.response }]);
      loadConversations();
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: "Connection error." }]);
    } finally { setLoading(false); }
  }

  const suggestions = ["What is the overall status?", "Concerning trends?", "Customer complaints", "Press-A performance"];

  return (
    <div className="flex h-[calc(100vh-160px)] sm:h-[calc(100vh-180px)] gap-0 sm:gap-4 relative">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/50 z-40 sm:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <div className={`
        fixed sm:relative inset-y-0 left-0 z-50 sm:z-auto
        w-72 sm:w-64 bg-white rounded-none sm:rounded-xl border-r sm:border border-gray-200 flex flex-col
        transform transition-transform duration-200 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full sm:translate-x-0'}
      `}>
        <div className="p-3 border-b border-gray-200">
          <button onClick={createNewConversation} className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
            <Plus size={18} /> New conversation
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {conversations.map(conv => (
            <div key={conv.id} className={`group flex items-center gap-2 p-2 rounded-lg cursor-pointer ${currentConvId === conv.id ? 'bg-primary-100' : 'hover:bg-gray-100'}`} onClick={() => selectConversation(conv.id)}>
              <MessageSquare size={16} className="text-gray-400 flex-shrink-0" />
              <span className="flex-1 text-sm truncate">{conv.title}</span>
              <button onClick={(e) => { e.stopPropagation(); deleteConversation(conv.id); }} className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 rounded">
                <Trash2 size={14} className="text-red-500" />
              </button>
            </div>
          ))}
          {conversations.length === 0 && <p className="text-sm text-gray-400 text-center py-4">No conversations</p>}
        </div>
      </div>

      {/* Main chat area */}
      <div className="flex-1 bg-white rounded-xl border border-gray-200 flex flex-col min-w-0">
        <div className="p-3 sm:p-4 border-b border-gray-200 flex items-center gap-3">
          <button
            className="sm:hidden p-1.5 rounded-lg text-gray-500 hover:bg-gray-100"
            onClick={() => setSidebarOpen(true)}
          >
            <History size={20} />
          </button>
          <h2 className="font-semibold text-gray-900 flex items-center gap-2"><Bot className="text-primary-600" size={20} /> Assistant NYOS</h2>
        </div>
        <div className="flex-1 overflow-y-auto p-3 sm:p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-6 sm:py-8">
              <Bot className="mx-auto text-gray-300 mb-4" size={48} />
              <p className="text-gray-500 mb-4 sm:mb-6">Start by asking a question</p>
              <div className="flex flex-wrap gap-2 justify-center px-2">
                {suggestions.map((s, i) => (<button key={i} onClick={() => setInput(s)} className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg text-xs sm:text-sm hover:bg-gray-200">{s}</button>))}
              </div>
            </div>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-2 sm:gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'user' ? 'bg-primary-600' : 'bg-gray-200'}`}>
                {msg.role === 'user' ? <User size={14} className="text-white" /> : <Bot size={14} className="text-gray-600" />}
              </div>
              <div className={`max-w-[85%] sm:max-w-[70%] rounded-xl px-3 sm:px-4 py-2 sm:py-3 text-sm sm:text-base ${msg.role === 'user' ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-800'}`}>
                <div dangerouslySetInnerHTML={{ __html: parseMarkdown(msg.content) }} />
              </div>
            </div>
          ))}
          {loading && (<div className="flex gap-2 sm:gap-3"><div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-gray-200 flex items-center justify-center"><Bot size={14} className="text-gray-600" /></div><div className="bg-gray-100 rounded-xl px-4 py-3"><Loader2 className="animate-spin text-gray-500" size={20} /></div></div>)}
          <div ref={messagesEndRef} />
        </div>
        <form onSubmit={handleSubmit} className="p-3 sm:p-4 border-t border-gray-200">
          <div className="flex gap-2">
            <input type="text" value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask a question..." className="flex-1 px-3 sm:px-4 py-2.5 sm:py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm sm:text-base" disabled={loading} />
            <button type="submit" disabled={loading || !input.trim()} className="px-4 sm:px-6 py-2.5 sm:py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"><Send size={18} /></button>
          </div>
        </form>
      </div>
    </div>
  );
}
