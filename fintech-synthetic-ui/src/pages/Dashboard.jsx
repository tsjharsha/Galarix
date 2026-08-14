import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { usePromptHistory } from '../context/PromptHistoryContext';
import { Zap, Database, TrendingUp, Cpu, LogOut, Clock, Play } from 'lucide-react';
import { ApiKeyManager } from '../components/ApiKeyManager';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const { threads } = usePromptHistory();

  // Sort threads to get recent ones
  const recentThreads = [...threads].sort((a, b) => b.updatedAt - a.updatedAt).slice(0, 5);

  return (
    <div className="min-h-screen bg-surface-950 text-white font-sans overflow-y-auto">
      
      {/* Navbar */}
      <nav className="border-b border-white/5 glass-heavy sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-brand-500/20">
              <span className="text-white font-bold text-sm">G</span>
            </div>
            <span className="text-xl font-bold tracking-tight text-white">GALARIX</span>
          </div>
          
          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-400">Welcome, {user?.name || "User"}</span>
            <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center">
              👤
            </div>
            <button onClick={logout} className="text-slate-500 hover:text-white transition-colors" title="Log out">
              <LogOut size={18} />
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-12">
        
        <header className="mb-12 animate-slide-up">
          <h1 className="text-4xl font-bold mb-2">Workspace</h1>
          <p className="text-slate-400">Select a service to start generating mathematically certified data.</p>
        </header>

        {/* Services Grid */}
        <section className="mb-16 animate-slide-up" style={{ animationDelay: '100ms' }}>
          <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
            <Database className="w-5 h-5 text-brand-400" />
            Core Services
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Main Service - Active */}
            <Link to="/studio" className="block relative group">
              <div className="absolute inset-0 bg-gradient-to-br from-brand-500/20 to-cyan-500/20 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              <div className="card h-full p-6 relative z-10 border-slate-700 hover:border-brand-500/50 bg-slate-800/40 hover:bg-slate-800/60 transition-all duration-300">
                <div className="flex justify-between items-start mb-6">
                  <div className="w-12 h-12 rounded-xl bg-brand-500/10 flex items-center justify-center border border-brand-500/20">
                    <Zap className="w-6 h-6 text-brand-400" />
                  </div>
                  <span className="px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    Live
                  </span>
                </div>
                <h3 className="text-xl font-bold mb-2 text-white group-hover:text-brand-400 transition-colors">Synthetic Data Generator</h3>
                <p className="text-slate-400 text-sm leading-relaxed mb-6">
                  Generate enterprise-grade financial datasets from a single prompt. Mathematically certified.
                </p>
                <div className="flex items-center text-brand-400 text-sm font-medium gap-1 opacity-0 group-hover:opacity-100 transition-opacity translate-x-[-10px] group-hover:translate-x-0 transform duration-300">
                  Enter Studio <Play size={14} />
                </div>
              </div>
            </Link>

            {/* Coming Soon Services */}
            <div className="card h-full p-6 border-slate-800 bg-slate-900/50 opacity-70">
              <div className="flex justify-between items-start mb-6">
                <div className="w-12 h-12 rounded-xl bg-slate-800 flex items-center justify-center border border-slate-700">
                  <TrendingUp className="w-6 h-6 text-slate-500" />
                </div>
                <span className="px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider bg-slate-800 text-slate-500 border border-slate-700">
                  Coming Soon
                </span>
              </div>
              <h3 className="text-xl font-bold mb-2 text-slate-300">Causal Simulator</h3>
              <p className="text-slate-500 text-sm leading-relaxed">
                Run "what-if" macroeconomic shock simulations on your portfolio models.
              </p>
            </div>

            <div className="card h-full p-6 border-slate-800 bg-slate-900/50 opacity-70">
              <div className="flex justify-between items-start mb-6">
                <div className="w-12 h-12 rounded-xl bg-slate-800 flex items-center justify-center border border-slate-700">
                  <Cpu className="w-6 h-6 text-slate-500" />
                </div>
                <span className="px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider bg-slate-800 text-slate-500 border border-slate-700">
                  Coming Soon
                </span>
              </div>
              <h3 className="text-xl font-bold mb-2 text-slate-300">Relational Fabric</h3>
              <p className="text-slate-500 text-sm leading-relaxed">
                Generate multi-table relational databases with mathematically preserved foreign keys.
              </p>
            </div>
          </div>
        </section>

        {/* Recent Generations */}
        {recentThreads.length > 0 && (
          <section className="animate-slide-up" style={{ animationDelay: '200ms' }}>
            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
              <Clock className="w-5 h-5 text-slate-400" />
              Recent Generations
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {recentThreads.map(thread => (
                <Link key={thread.id} to={`/studio/${thread.id}`} className="card p-4 hover:border-brand-500/30 hover:bg-slate-800/60 transition-colors flex items-start gap-4">
                  <div className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center shrink-0 border border-slate-700">
                    <span className="text-lg">📊</span>
                  </div>
                  <div className="overflow-hidden">
                    <h4 className="text-sm font-semibold text-slate-200 truncate">{thread.title}</h4>
                    <p className="text-xs text-slate-500 mt-1">
                      {new Date(thread.updatedAt).toLocaleDateString()}
                    </p>
                  </div>
                </Link>
              ))}
            </div>
          </section>
        )}

        {/* API Key Management */}
        <ApiKeyManager />
      </main>
    </div>
  );
};

export default Dashboard;
