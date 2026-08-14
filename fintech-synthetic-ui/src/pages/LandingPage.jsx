import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, Database, Zap, FileJson } from 'lucide-react';

const LandingPage = () => {
  return (
    <div className="min-h-screen bg-surface-950 text-white overflow-x-hidden relative font-sans">
      
      {/* Background Animated Mesh */}
      <div className="absolute inset-0 bg-mesh opacity-50 pointer-events-none"></div>

      {/* Navbar */}
      <nav className="relative z-10 border-b border-white/10 glass-heavy">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-brand-500/20">
              <span className="text-white font-bold text-xl">G</span>
            </div>
            <span className="text-2xl font-black tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
              GALARIX
            </span>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/login" className="btn-ghost text-slate-300 hover:text-white">Log in</Link>
            <Link to="/signup" className="btn-primary">Get Started</Link>
          </div>
        </div>
      </nav>

      <main className="relative z-10">
        {/* Hero Section */}
        <section className="pt-32 pb-20 px-6 max-w-7xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-brand-500/30 bg-brand-500/10 text-brand-300 text-sm font-medium mb-8 animate-fade-in">
            <span className="w-2 h-2 rounded-full bg-brand-400 animate-pulse-soft"></span>
            Galarix Engine v2.0 is Live
          </div>
          
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-8 leading-tight animate-slide-up">
            Generate Statistically Certified <br className="hidden md:block"/>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-400 to-cyan-400">
              Financial Data
            </span> — From a Single Prompt.
          </h1>
          
          <p className="text-lg md:text-xl text-slate-400 max-w-3xl mx-auto mb-12 animate-slide-up" style={{ animationDelay: '100ms' }}>
            Zero real data required. Mathematically grounded. Regulator-ready. 
            Build and test your financial models, apps, and pipelines with infinite synthetic data.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-slide-up" style={{ animationDelay: '200ms' }}>
            <Link to="/signup" className="px-8 py-4 rounded-xl font-bold text-lg text-white bg-gradient-to-r from-brand-500 to-brand-600 hover:from-brand-600 hover:to-brand-700 shadow-[0_0_40px_rgba(99,102,241,0.4)] transition-all transform hover:scale-105 active:scale-95">
              Start Generating Free
            </Link>
            <a href="#how-it-works" className="px-8 py-4 rounded-xl font-bold text-lg text-slate-300 bg-white/5 border border-white/10 hover:bg-white/10 transition-all">
              Watch Demo &rarr;
            </a>
          </div>
        </section>

        {/* Features Grid */}
        <section className="py-20 px-6 bg-slate-900/50 border-y border-white/5">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold mb-4">Enterprise-Grade Generation</h2>
              <p className="text-slate-400">Everything you need to build trust in your synthetic data.</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 stagger-children">
              <div className="card-hover p-6 bg-slate-800/40 border-slate-700/50">
                <div className="w-12 h-12 rounded-lg bg-emerald-500/10 flex items-center justify-center mb-6">
                  <ShieldCheck className="w-6 h-6 text-emerald-400" />
                </div>
                <h3 className="text-xl font-bold mb-2">Zero-Data Architecture</h3>
                <p className="text-slate-400 text-sm">We never see your real data. Generate purely from mathematically derived statistical distributions.</p>
              </div>

              <div className="card-hover p-6 bg-slate-800/40 border-slate-700/50">
                <div className="w-12 h-12 rounded-lg bg-blue-500/10 flex items-center justify-center mb-6">
                  <Database className="w-6 h-6 text-blue-400" />
                </div>
                <h3 className="text-xl font-bold mb-2">20+ Financial Entities</h3>
                <p className="text-slate-400 text-sm">From Credit Cards and Mortgages to complex AML alerts and Trade executions across 7 global regions.</p>
              </div>

              <div className="card-hover p-6 bg-slate-800/40 border-slate-700/50">
                <div className="w-12 h-12 rounded-lg bg-brand-500/10 flex items-center justify-center mb-6">
                  <FileJson className="w-6 h-6 text-brand-400" />
                </div>
                <h3 className="text-xl font-bold mb-2">Trust Certificates</h3>
                <p className="text-slate-400 text-sm">Every dataset ships with a cryptographic audit report proving KS, Chi², and EMD statistical validity.</p>
              </div>

              <div className="card-hover p-6 bg-slate-800/40 border-slate-700/50">
                <div className="w-12 h-12 rounded-lg bg-amber-500/10 flex items-center justify-center mb-6">
                  <Zap className="w-6 h-6 text-amber-400" />
                </div>
                <h3 className="text-xl font-bold mb-2">Blazing Fast</h3>
                <p className="text-slate-400 text-sm">Generate 10,000 complex financial records in under 5 seconds. Pure Python NumPy engine, zero bloat.</p>
              </div>
            </div>
          </div>
        </section>

        {/* How It Works */}
        <section id="how-it-works" className="py-24 px-6 max-w-7xl mx-auto">
          <div className="text-center mb-20">
            <h2 className="text-4xl font-extrabold mb-4">How It Works</h2>
            <p className="text-slate-400 text-lg">Three steps to certified synthetic data.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="relative">
              <div className="absolute top-0 right-0 -mr-4 mt-6 hidden md:block text-slate-700">&rarr;</div>
              <div className="bg-slate-800/40 border border-slate-700/50 rounded-2xl p-8 h-full">
                <div className="text-4xl font-black text-brand-500/30 mb-6">01</div>
                <h3 className="text-2xl font-bold mb-4">The Prompt</h3>
                <p className="text-slate-400">Describe what you need in plain English. e.g. "Generate 10k rows of Indian credit card transactions during a recession."</p>
              </div>
            </div>

            <div className="relative">
              <div className="absolute top-0 right-0 -mr-4 mt-6 hidden md:block text-slate-700">&rarr;</div>
              <div className="bg-slate-800/40 border border-slate-700/50 rounded-2xl p-8 h-full gradient-border">
                <div className="text-4xl font-black text-brand-500/50 mb-6">02</div>
                <h3 className="text-2xl font-bold mb-4">The Engine</h3>
                <p className="text-slate-400">Our engine parses intent, enriches it with Federal reserve statistics, and compiles a mathematical blueprint.</p>
              </div>
            </div>

            <div className="relative">
              <div className="bg-slate-800/40 border border-slate-700/50 rounded-2xl p-8 h-full">
                <div className="text-4xl font-black text-brand-500/30 mb-6">03</div>
                <h3 className="text-2xl font-bold mb-4">The Data</h3>
                <p className="text-slate-400">Download production-ready CSV/JSON datasets, fully verified and mathematically certified.</p>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/10 bg-black py-12 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-3">
            <span className="text-white font-bold">GALARIX</span>
            <span className="text-slate-500 text-sm">© {new Date().getFullYear()}</span>
          </div>
          <p className="text-slate-500 text-sm">
            Built with deterministic mathematics, not black-box AI.
          </p>
          <div className="flex gap-6">
            <a href="#" className="text-slate-400 hover:text-white transition-colors">Documentation</a>
            <a href="#" className="text-slate-400 hover:text-white transition-colors">API</a>
            <a href="#" className="text-slate-400 hover:text-white transition-colors">Security</a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
