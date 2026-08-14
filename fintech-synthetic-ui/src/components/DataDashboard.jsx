// This file will hold the complex data generation dashboard UI
import React, { useState } from 'react';
import { 
  Activity, Target, Key, ShieldAlert, Fingerprint, Lock, CheckCircle2,
  TableProperties, Type, AlignLeft, AlertTriangle, Network, DownloadCloud,
  ShieldCheck, Database, Zap, FileJson, LineChart, FileText, X
} from "lucide-react";
import * as XLSX from "xlsx";

/* ================= DISTRIBUTION BADGE ================= */
function DistBadge({ family }) {
  const map = {
    normal: { class: "badge-normal", label: "Normal" },
    lognormal: { class: "badge-lognormal", label: "LogNormal" },
    student_t: { class: "badge-student-t", label: "Student-T" },
    cauchy: { class: "badge-cauchy", label: "Cauchy" },
    categorical: { class: "badge-categorical", label: "Categorical" },
    beta: { class: "badge-beta", label: "Beta" },
    string: { class: "bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300", label: "String" },
  };
  const info = map[family] || map.string;
  return <span className={`px-2 py-0.5 rounded-md text-[10px] font-semibold ${info.class}`}>{info.label}</span>;
}

/* ================= CONFIDENCE GAUGE ================= */
function ConfidenceGauge({ value }) {
  const pct = Math.round(value * 100);
  const radius = 36;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value * circumference);
  const color = pct >= 80 ? "#10b981" : pct >= 50 ? "#f59e0b" : "#ef4444";

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width="88" height="88" className="gauge-ring">
        <circle cx="44" cy="44" r={radius} stroke="currentColor" className="text-slate-200 dark:text-slate-700" strokeWidth="5" fill="none" />
        <circle cx="44" cy="44" r={radius} stroke={color} strokeWidth="5" fill="none"
          strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 1s ease-out" }} />
      </svg>
      <div className="absolute text-center">
        <div className="text-lg font-bold text-slate-800 dark:text-white">{pct}%</div>
        <div className="text-[9px] text-slate-500 uppercase tracking-wider">Conf.</div>
      </div>
    </div>
  );
}

/* ================= MINI BAR ================= */
function MiniBar({ label, value, max, color }) {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div className="flex items-center gap-2">
      <span className="text-[10px] text-slate-400 w-12 shrink-0">{label}</span>
      <div className="flex-1 h-1.5 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
        <div className={`h-full rounded-full bg-gradient-to-r ${color}`}
          style={{ width: `${pct}%`, transition: "width 1s ease-out" }} />
      </div>
      <span className="text-[10px] font-mono text-slate-500 w-12 text-right">{typeof value === 'number' ? value.toFixed(2) : value}</span>
    </div>
  );
}

/* ================= AUDIT CHECK CARD ================= */
function AuditCheckCard({ title, score, detail }) {
  const numScore = typeof score === 'number' ? score : 0;
  const color = numScore >= 90 ? 'emerald' : numScore >= 70 ? 'amber' : 'red';
  return (
    <div className={`rounded-xl p-3.5 border transition-all duration-200
      bg-${color}-50/50 dark:bg-${color}-900/10
      border-${color}-200/50 dark:border-${color}-500/20`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-slate-700 dark:text-slate-200">{title}</span>
        <span className={`text-xs font-bold text-${color}-600 dark:text-${color}-400`}>{numScore}/100</span>
      </div>
      <div className="h-1.5 rounded-full bg-slate-200/50 dark:bg-slate-700/50 overflow-hidden mb-1.5">
        <div className={`h-full rounded-full bg-${color}-500 transition-all duration-700 ease-out`}
          style={{ width: `${numScore}%` }} />
      </div>
      <div className="text-[10px] text-slate-500 dark:text-slate-400">{detail}</div>
    </div>
  );
}

export default function DataDashboard({ payload, prompt, region, genRows: propGenRows }) {
  const [activeTab, setActiveTab] = useState("overview");
  const [fullData, setFullData] = useState(null);
  const [isGeneratingData, setIsGeneratingData] = useState(false);
  const [genProgressText, setGenProgressText] = useState("Initializing generator...");
  const [toast, setToast] = useState(null); // { message, type: 'error' | 'success' }

  const showToast = (message, type = "error") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };

  const { 
    schema, sample_data: data = [], statisticalModel: statModel, variables, 
    distributions, constraints, detected_entities: detectedEntities = [], 
    confidence = 0, intent, data_sources: dataSources 
  } = payload;

  const genRows = propGenRows || payload.num_rows || intent?.num_rows || 1000;
  const activeRegion = region || payload.region || intent?.region || "US";

  const TABS = [
    { id: "overview", label: "Overview", icon: <Activity size={14} /> },
    { id: "schema", label: "Schema", icon: <TableProperties size={14} /> },
    { id: "model", label: "Statistical Model", icon: <LineChart size={14} /> },
    { id: "provenance", label: "Provenance", icon: <ShieldCheck size={14} /> },
    { id: "data", label: "Preview", icon: <Database size={14} /> },
    { id: "generated", label: "Generated Data", icon: <Zap size={14} /> },
    { id: "raw", label: "Raw Contract", icon: <FileJson size={14} /> },
  ];

  const behavior = statModel?.behavior_used || {};
  const tensorSig = behavior.tensor_signature || statModel?.meta?.tensor_signature || "";
  const covariance = statModel?.covariance || [];
  const params = statModel?.parameters || {};
  const morphedVars = Object.entries(params).filter(([, d]) => d.family === "student_t" || d.family === "cauchy");
  const hasMorphing = morphedVars.length > 0;

  const downloadCSV = () => {
    if (!data.length) return;
    const headers = Object.keys(data[0]);
    const csvRows = [headers.join(","), ...data.map((row) => headers.map((f) => `"${row[f] ?? ""}"`).join(","))];
    const blob = new Blob([csvRows.join("\n")], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `galarix_${detectedEntities[0] || "data"}_preview.csv`;
    a.click();
  };

  const downloadJSON = () => {
    if (!statModel) return;
    const blob = new Blob([JSON.stringify(statModel, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `galarix_model.json`;
    a.click();
  };

  /* ================= EXCEL DOWNLOAD ================= */
  const downloadExcel = () => {
    if (!fullData?.data?.length) return;
    const worksheet = XLSX.utils.json_to_sheet(fullData.data);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Data");
    XLSX.writeFile(workbook, `galarix_${detectedEntities[0] || 'data'}_${fullData.rows_generated || data.length}rows.xlsx`);
  };

  /* ================= GENERATE FULL DATASET ================= */
  const generateFullDataset = async () => {
    if (isGeneratingData) return;
    setIsGeneratingData(true);
    setFullData(null);
    setGenProgressText("Compiling statistical model...");
    
    // Cycle progress text for UX
    const steps = [
      "Running Monte Carlo simulations...",
      "Enforcing regional constraints...",
      "Injecting targeted anomalies...",
      "Validating covariance matrix...",
      "Generating output tensors..."
    ];
    let stepIdx = 0;
    const interval = setInterval(() => {
      setGenProgressText(steps[stepIdx]);
      stepIdx = (stepIdx + 1) % steps.length;
    }, 1500);

    try {
      const backendUrl = import.meta.env.VITE_BACKEND_URL || "http://localhost:5000";
      const res = await fetch(`${backendUrl}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          prompt: prompt || `Generate synthetic ${detectedEntities[0] || 'data'}`, 
          rows: genRows, 
          variation: 0, 
          include_audit: true, 
          region: activeRegion 
        }),
      });
      const result = await res.json();
      if (result.status === "success") {
        setFullData(result);
        setActiveTab("generated");
        showToast("Generation completed successfully!", "success");
      } else {
        showToast("Generation failed: " + (result.message || "Unknown error"), "error");
      }
    } catch (e) {
      showToast("Connection error: " + e.message, "error");
    } finally {
      clearInterval(interval);
      setIsGeneratingData(false);
    }
  };

  return (
    <div className="w-full text-left animate-slide-up">
      {/* Tab Bar */}
      <div className="flex gap-1 mb-6 p-1 rounded-xl bg-slate-100 dark:bg-slate-800/50 overflow-x-auto custom-scrollbar">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold whitespace-nowrap transition-all duration-200
              ${activeTab === tab.id
                ? "bg-white dark:bg-slate-700 text-brand-600 dark:text-brand-400 shadow-sm"
                : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
              }`}
          >
            <span className="text-sm">{tab.icon}</span>
            {tab.label}
            {tab.id === "model" && hasMorphing && (
              <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse ml-1" />
            )}
          </button>
        ))}
      </div>

      {/* OVERVIEW TAB */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div className="card-glow p-6 flex flex-col items-center justify-center relative overflow-hidden group">
            <div className="absolute inset-0 bg-gradient-to-br from-brand-500/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <ConfidenceGauge value={confidence} />
            <div className="mt-4 flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 font-medium">
              <Activity size={14} className="text-brand-500" />
              {schema?.method || "Engine"} Engine
            </div>
          </div>
          
          <div className="card p-6 relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 opacity-10">
              <Target size={64} />
            </div>
            <div className="flex items-center gap-2 mb-4">
              <Key size={16} className="text-slate-400" />
              <h3 className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">Detection Parameters</h3>
            </div>
            <div className="space-y-3 relative z-10">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-2">
                <span className="text-[11px] font-medium text-slate-400">Entity</span>
                <div className="flex flex-wrap gap-1 justify-end">
                  {detectedEntities.map((e) => (
                    <span key={e} className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-brand-50 text-brand-700 dark:bg-brand-500/10 dark:text-brand-400 shadow-sm border border-brand-100 dark:border-brand-500/20">
                      {e.replaceAll("_", " ")}
                    </span>
                  ))}
                </div>
              </div>
              {intent && (
                <>
                  <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-2">
                    <span className="text-[11px] font-medium text-slate-400">Scale</span>
                    <span className="text-[11px] font-bold text-slate-700 dark:text-slate-200">{intent.scale || "—"}</span>
                  </div>
                  <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-2">
                    <span className="text-[11px] font-medium text-slate-400">Risk Profile</span>
                    <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider ${
                      intent.risk === "extreme" ? "bg-red-50 text-red-700 dark:bg-red-500/10 dark:text-red-400 border border-red-200 dark:border-red-500/20 shadow-sm" :
                      intent.risk === "high" ? "bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400 border border-amber-200 dark:border-amber-500/20 shadow-sm" :
                      "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20 shadow-sm"
                    }`}>
                      {intent.risk === "extreme" && <ShieldAlert size={10} className="inline mr-1" />}
                      {intent.risk || "—"}
                    </span>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Tensor Signature */}
          <div className="card p-6 bg-gradient-to-br from-slate-50 to-white dark:from-slate-800/50 dark:to-slate-900/50 border-slate-200 dark:border-slate-700">
            <div className="flex items-center gap-2 mb-4">
              <Fingerprint size={16} className="text-brand-500" />
              <h3 className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">Tensor Signature</h3>
              <div className="ml-auto flex items-center gap-1 px-2 py-0.5 rounded text-[9px] font-bold bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20 uppercase tracking-widest">
                <CheckCircle2 size={10} /> Verified
              </div>
            </div>
            {tensorSig && (
              <div className="relative p-3 rounded-xl bg-slate-900 dark:bg-black/40 border border-slate-800 shadow-inner overflow-hidden group">
                <div className="absolute top-0 left-0 w-full h-[1px] bg-brand-500/50 shadow-[0_0_8px_2px_rgba(99,102,241,0.5)] transform -translate-y-full group-hover:translate-y-[100px] transition-transform duration-1500 ease-in-out" />
                <div className="font-mono text-sm md:text-base font-bold text-brand-400 tracking-widest break-all leading-tight">
                  {tensorSig}
                </div>
              </div>
            )}
            <div className="mt-3 flex items-start gap-2 text-[10px] text-slate-500 dark:text-slate-400 leading-relaxed">
              <Lock size={12} className="shrink-0 mt-0.5 opacity-70" />
              <span>Unique deterministic hash. Ensures cryptographic reproducibility.</span>
            </div>
          </div>
        </div>
      )}

      {/* SCHEMA TAB */}
      {activeTab === "schema" && variables && (
        <div className="card overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 flex items-center gap-2">
            <TableProperties size={16} className="text-brand-500" />
            <h3 className="text-sm font-bold text-slate-700 dark:text-slate-300">Generated Data Schema</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900/50">
                  <th className="text-left px-5 py-3 text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    <div className="flex items-center gap-1.5"><Type size={12} /> Variable</div>
                  </th>
                  <th className="text-left px-5 py-3 text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    <div className="flex items-center gap-1.5"><Activity size={12} /> Type</div>
                  </th>
                  <th className="text-left px-5 py-3 text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    <div className="flex items-center gap-1.5"><AlignLeft size={12} /> Description</div>
                  </th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(variables).map(([name, def], i) => (
                  <tr key={name} className={`border-b border-slate-100 dark:border-slate-800/50 hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors ${i % 2 === 0 ? 'bg-white dark:bg-slate-900/20' : 'bg-slate-50/30 dark:bg-slate-800/10'}`}>
                    <td className="px-5 py-3.5 font-mono text-xs font-semibold text-brand-600 dark:text-brand-400">{name}</td>
                    <td className="px-5 py-3.5"><DistBadge family={def.type === "continuous" ? (distributions?.[name]?.family || "normal") : def.type} /></td>
                    <td className="px-5 py-3.5 text-xs text-slate-600 dark:text-slate-400">{def.description || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* STAT MODEL TAB */}
      {activeTab === "model" && (
        <div className="space-y-5">
          {hasMorphing && (
            <div className="morphing-alert rounded-xl p-5 animate-fade-in relative overflow-hidden group">
              <div className="absolute -right-4 -top-4 opacity-10 transform group-hover:scale-110 transition-transform duration-500">
                <AlertTriangle size={120} />
              </div>
              <div className="flex items-center gap-2 mb-2 relative z-10">
                <AlertTriangle size={20} className="text-red-500" />
                <span className="text-sm font-bold text-red-600 dark:text-red-400 tracking-wide uppercase">Black Swan Morphing Active</span>
              </div>
              <p className="text-xs text-red-500/80 dark:text-red-400/60 mb-3">
                Extreme variance detected. {morphedVars.length} distribution{morphedVars.length > 1 ? "s" : ""} morphed to heavy-tailed families.
              </p>
              <div className="flex flex-wrap gap-2">
                {morphedVars.map(([name, dist]) => (
                  <span key={name} className={`px-2.5 py-1 rounded-lg text-[10px] font-bold ${
                    dist.family === "cauchy" ? "bg-red-500/20 text-red-400" : "bg-amber-500/20 text-amber-400"
                  }`}>
                    {name.split("_").slice(-2).join("_")} → {dist.family.toUpperCase()}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="card">
            <div className="px-5 py-3 border-b border-slate-200 dark:border-slate-700">
              <h3 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Distribution Parameters</h3>
            </div>
            <div className="divide-y divide-slate-100 dark:divide-slate-800">
              {Object.entries(params).map(([name, dist]) => (
                <div key={name} className="px-5 py-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs text-brand-600 dark:text-brand-400">{name}</span>
                    <DistBadge family={dist.family} />
                  </div>
                  <div className="font-mono text-[11px] text-slate-500 dark:text-slate-400">
                    {dist.params ? Object.entries(dist.params).map(([k, v]) => `${k}=${typeof v === 'number' ? v.toFixed(2) : v}`).join(" · ") : "—"}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <button onClick={downloadJSON} className="btn-outline flex items-center gap-2 mt-4 ml-auto">
            <DownloadCloud size={14} /> Download Model JSON
          </button>
        </div>
      )}

      {/* PROVENANCE TAB */}
      {activeTab === "provenance" && dataSources && (
        <div className="space-y-5 animate-fade-in">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {dataSources.map((ds, i) => (
              <div key={i} className="border border-slate-100 dark:border-slate-700/50 rounded-xl p-4 bg-slate-50/50 dark:bg-slate-800/20">
                <div className="flex items-start justify-between mb-2">
                  <span className="px-2 py-1 bg-brand-100 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400 rounded text-[10px] font-bold tracking-wide uppercase">
                    {ds.source}
                  </span>
                  <span className="text-[10px] font-mono text-slate-400">{ds.dataset}</span>
                </div>
                <p className="text-xs text-slate-600 dark:text-slate-400 mb-3">{ds.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* PREVIEW TAB */}
      {activeTab === "data" && data.length > 0 && (
        <div className="space-y-4 animate-fade-in">
          <div className="flex justify-between">
            <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">{data.length} Preview Rows</span>
            <button onClick={downloadCSV} className="btn-outline text-xs flex items-center gap-2">
              <DownloadCloud size={14} /> Download CSV
            </button>
          </div>
          <div className="card overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-700">
                  {Object.keys(data[0]).filter(k => k !== '_is_anomaly').map((k) => (
                    <th key={k} className="text-left px-4 py-3 text-[10px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider whitespace-nowrap">{k.replace(/_/g, ' ')}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.map((row, i) => (
                  <tr key={i} className={`border-b border-slate-100 dark:border-slate-800 ${row._is_anomaly ? 'bg-red-50/60 dark:bg-red-900/10' : ''}`}>
                    {Object.entries(row).filter(([k]) => k !== '_is_anomaly').map(([k, v], j) => (
                      <td key={j} className={`px-4 py-2.5 whitespace-nowrap font-mono ${row._is_anomaly ? 'text-red-600 dark:text-red-400' : 'text-slate-700 dark:text-slate-300'}`}>{v ?? "—"}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="card-glow p-5 text-center mt-4">
            <button onClick={generateFullDataset} disabled={isGeneratingData} className="btn-primary flex items-center gap-2 mx-auto">
              {isGeneratingData ? "Generating..." : "⚡ Generate Full Dataset"}
            </button>
          </div>
        </div>
      )}

      {/* GENERATED TAB */}
      {activeTab === "generated" && (
        <div className="space-y-4">
          {!fullData && !isGeneratingData && (
            <div className="card-glow p-8 text-center">
              <div className="text-4xl mb-4">⚡</div>
              <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-2">Generate Synthetic Data</h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-6 max-w-md mx-auto">
                Run the full Stage 3 generation pipeline to create a complete dataset with quality audit.
              </p>
              <button onClick={generateFullDataset} className="btn-primary flex items-center gap-2 mx-auto">
                ⚡ Generate {genRows.toLocaleString()} Rows
              </button>
            </div>
          )}
          
          {isGeneratingData && (
            <div className="card p-8 text-center animate-fade-in">
              <svg className="animate-spin h-8 w-8 mx-auto mb-4 text-brand-500" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <p className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-1">Generating {genRows.toLocaleString()} rows...</p>
              <p className="text-xs text-brand-500 animate-pulse">{genProgressText}</p>
            </div>
          )}
          
          {fullData && (
            <div className="space-y-4 animate-fade-in">
              {/* Quality + Stats Bar */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3 stagger-children">
                <div className="stat-card">
                  <div className="stat-value text-brand-500">{fullData.rows_generated?.toLocaleString()}</div>
                  <div className="stat-label uppercase tracking-wider text-[10px] text-slate-400">Rows Generated</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value text-red-500">{fullData.audit_report?.anomaly_check?.actual_count || 0}</div>
                  <div className="stat-label uppercase tracking-wider text-[10px] text-slate-400">Anomalies Injected</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value text-slate-700 dark:text-slate-200">{fullData.columns?.length || 0}</div>
                  <div className="stat-label uppercase tracking-wider text-[10px] text-slate-400">Total Columns</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value text-emerald-500">{fullData.audit_report?.nan_check?.score || 0}%</div>
                  <div className="stat-label uppercase tracking-wider text-[10px] text-slate-400">Audit Score</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value text-indigo-500">{fullData.trust_badge?.trust_score?.toFixed(0) || 0}%</div>
                  <div className="stat-label uppercase tracking-wider text-[10px] text-slate-400">Trust Score</div>
                </div>
              </div>

              {/* Audit Checklist Section */}
              {fullData.audit_report && (
                <div className="card p-5 mt-4">
                  <div className="flex items-center gap-2 mb-4">
                    <ShieldCheck size={18} className="text-emerald-500" />
                    <h3 className="text-sm font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">Engine Quality Audit Checklist</h3>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                    {fullData.audit_report.nan_check && (
                      <AuditCheckCard 
                        title="NaN/Inf Check" 
                        score={fullData.audit_report.nan_check.score} 
                        detail={`${fullData.audit_report.nan_check.total_nans || 0} NaN values found`} 
                      />
                    )}
                    {fullData.audit_report.bounds_check && (
                      <AuditCheckCard 
                        title="Bounds Compliance" 
                        score={fullData.audit_report.bounds_check.score} 
                        detail={`${fullData.audit_report.bounds_check.violations || 0} violations`} 
                      />
                    )}
                    {fullData.audit_report.distribution_check && (
                      <AuditCheckCard 
                        title="Distribution Fit" 
                        score={fullData.audit_report.distribution_check.score} 
                        detail={`${fullData.audit_report.distribution_check.vars_checked || 0} variables checked`} 
                      />
                    )}
                    {fullData.audit_report.anomaly_check && (
                      <AuditCheckCard 
                        title="Anomaly Injection" 
                        score={fullData.audit_report.anomaly_check.score} 
                        detail={`${fullData.audit_report.anomaly_check.actual_count || 0} of ${fullData.audit_report.anomaly_check.expected_count || 0} expected`} 
                      />
                    )}
                  </div>
                </div>
              )}

              {/* Trust Certificate Section */}
              {fullData.trust_certificate && fullData.trust_certificate.trust_certificate && (
                <div className="card p-5 animate-fade-in mt-4 bg-gradient-to-br from-indigo-50/50 to-blue-50/30 dark:from-indigo-900/10 dark:to-blue-900/10 border-indigo-200 dark:border-indigo-800">
                  <div className="flex items-center gap-2 mb-4">
                    <ShieldCheck size={18} className="text-indigo-600 dark:text-indigo-400" />
                    <h3 className="text-sm font-bold text-indigo-900 dark:text-indigo-200">Regional Trust Certificate</h3>
                    <span className={`ml-auto px-3 py-1 rounded-lg text-xs font-bold shadow-sm ${
                      fullData.trust_badge?.verdict === 'TRUSTED' ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-700' :
                      fullData.trust_badge?.verdict === 'ACCEPTABLE' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300 border border-blue-200 dark:border-blue-700' :
                      fullData.trust_badge?.verdict === 'REGIONAL MISMATCH' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-300 border border-amber-200 dark:border-amber-700' :
                      'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300 border border-red-200 dark:border-red-700'
                    }`}>
                      {fullData.trust_badge?.verdict || 'UNTRUSTED'} ({fullData.trust_badge?.trust_score?.toFixed(1) || 0}/100)
                    </span>
                  </div>
                  <div className="text-xs text-slate-600 dark:text-slate-300 mb-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-slate-500">Validated Region:</span>
                      <span className="font-bold text-indigo-700 dark:text-indigo-300">{fullData.trust_certificate.trust_certificate.region?.name || 'Unknown'}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-slate-500">Central Bank Provenance:</span>
                      <span className="font-bold text-indigo-700 dark:text-indigo-300">{fullData.trust_certificate.trust_certificate.region?.central_bank || 'None'}</span>
                    </div>
                  </div>
                  <button 
                    onClick={async () => {
                      try {
                        const backendUrl = import.meta.env.VITE_BACKEND_URL || "http://localhost:5000";
                        const res = await fetch(`${backendUrl}/trust-report`, {
                          method: "POST",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({ prompt, rows: genRows, region: activeRegion, format: "pdf" }),
                        });
                        if (!res.ok) throw new Error("Failed to download");
                        const blob = await res.blob();
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement("a");
                        a.href = url;
                        a.download = `TrustReport_${detectedEntities[0] || 'data'}_${activeRegion}.pdf`;
                        document.body.appendChild(a);
                        a.click();
                        window.URL.revokeObjectURL(url);
                        showToast("Report downloaded successfully", "success");
                      } catch (e) {
                        showToast("Failed to download trust report: " + e.message, "error");
                      }
                    }}
                    className="w-full mt-2 py-2 flex items-center justify-center gap-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition-colors shadow-sm"
                  >
                    <FileText size={14} />
                    Download PDF Trust Report
                  </button>
                </div>
              )}

              {/* Tensor + Actions */}
              <div className="flex items-center justify-between flex-wrap gap-3 mt-4">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-xs text-slate-400">Tensor: {fullData.tensor_signature || tensorSig}</span>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => { const d = fullData.data; if(!d?.length) return; const h = Object.keys(d[0]).filter(k=>k!=='_is_anomaly'); const csv = [h.join(','), ...d.map(r => h.map(f => `"${r[f]??''}"`).join(','))].join('\n'); const b = new Blob([csv],{type:'text/csv'}); const a = document.createElement('a'); a.href=URL.createObjectURL(b); a.download=`galarix_${detectedEntities[0]}_${fullData.rows_generated}rows.csv`; a.click(); }} className="btn-primary text-xs flex items-center gap-1.5">
                    <DownloadCloud size={14} /> CSV
                  </button>
                  <button onClick={() => { const b = new Blob([JSON.stringify(fullData.data,null,2)],{type:'application/json'}); const a = document.createElement('a'); a.href=URL.createObjectURL(b); a.download=`galarix_${detectedEntities[0]}_${fullData.rows_generated}rows.json`; a.click(); }} className="btn-outline text-xs flex items-center gap-1.5">
                    <DownloadCloud size={14} /> JSON
                  </button>
                  <button onClick={downloadExcel} className="btn-outline text-xs flex items-center gap-1.5 border-emerald-200 text-emerald-700 hover:bg-emerald-50 dark:border-emerald-800 dark:text-emerald-400 dark:hover:bg-emerald-900/30">
                    <DownloadCloud size={14} /> Excel (XLSX)
                  </button>
                </div>
              </div>

              {/* Data Table */}
              <div className="card overflow-x-auto" style={{maxHeight:'480px', overflowY:'auto'}}>
                <table className="w-full text-xs">
                  <thead className="sticky top-0 bg-white dark:bg-surface-900 z-10">
                    <tr className="border-b border-slate-200 dark:border-slate-700">
                      <th className="text-left px-3 py-3 text-[10px] font-semibold text-slate-500 uppercase">#</th>
                      {fullData.columns?.filter(k => k !== '_is_anomaly').map((k) => (
                        <th key={k} className="text-left px-3 py-3 text-[10px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider whitespace-nowrap">{k.replace(/_/g, ' ')}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {(fullData.data || []).slice(0, 200).map((row, i) => (
                      <tr key={i} className={`border-b border-slate-100 dark:border-slate-800 ${
                        row._is_anomaly ? 'bg-red-50/70 dark:bg-red-900/15' : i % 2 === 0 ? '' : 'bg-slate-50/50 dark:bg-slate-800/30'
                      }`}>
                        <td className="px-3 py-2 text-slate-400 font-mono">{i+1}{row._is_anomaly ? ' ⚠️' : ''}</td>
                        {fullData.columns?.filter(k => k !== '_is_anomaly').map((k, j) => (
                          <td key={j} className={`px-3 py-2 whitespace-nowrap font-mono ${row._is_anomaly ? 'text-red-600 dark:text-red-400' : 'text-slate-700 dark:text-slate-300'}`}>{row[k] ?? '—'}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                {(fullData.data?.length || 0) > 200 && (
                  <div className="px-4 py-3 text-center text-xs text-slate-400 border-t border-slate-200 dark:border-slate-700">
                    Showing 200 of {fullData.data.length.toLocaleString()} rows. Download for full dataset.
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* RAW TAB */}
      {activeTab === "raw" && (
        <div className="card overflow-hidden bg-slate-900 p-5 max-h-[500px] overflow-auto">
          <pre className="text-[11px] font-mono text-emerald-400 whitespace-pre-wrap">
            {JSON.stringify(payload, null, 2)}
          </pre>
        </div>
      )}

      {/* TOAST NOTIFICATION */}
      {toast && (
        <div className={`fixed bottom-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 animate-fade-in
          ${toast.type === 'error' ? 'bg-red-600 text-white' : 'bg-emerald-600 text-white'}`}>
          <div className="text-sm font-semibold">{toast.message}</div>
          <button onClick={() => setToast(null)} className="opacity-80 hover:opacity-100">
            <X size={16} />
          </button>
        </div>
      )}
    </div>
  );
}
