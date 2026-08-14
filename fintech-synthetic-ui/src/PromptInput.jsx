import { useState, useEffect, useRef } from "react";
import { usePromptHistory } from "./context/PromptHistoryContext";
import DataDashboard from "./components/DataDashboard";
import { 
  Globe2, ShieldAlert, Fingerprint, Bot, Terminal, Shield, Zap, Sparkles, Activity, CheckCircle
} from "lucide-react";
import DataStreamMatrix from "./components/DataStreamMatrix";
import { audioKinetics } from "./utils/AudioKinetics";

const REGIONS = {
  US: { flag: "🇺🇸", regulator: "FED", label: "US (FED)" },
  UK: { flag: "🇬🇧", regulator: "BOE", label: "UK (BOE)" },
  EU: { flag: "🇪🇺", regulator: "ECB", label: "EU (ECB)" },
  IN: { flag: "🇮🇳", regulator: "RBI", label: "India (RBI)" },
  JP: { flag: "🇯🇵", regulator: "BOJ", label: "Japan (BOJ)" },
  AU: { flag: "🇦🇺", regulator: "RBA", label: "Australia (RBA)" },
  BR: { flag: "🇧🇷", regulator: "BCB", label: "Brazil (BCB)" },
};

function PromptInput({
  prompt, setPrompt, activeThreadId, setActiveThreadId
}) {
  const { createThread, addAIResponseToThread, addMessageToThread, getThreadById } = usePromptHistory();

  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");
  const [region, setRegion] = useState("US");
  const [isShaking, setIsShaking] = useState(false);
  
  const textareaRef = useRef(null);
  const chatEndRef = useRef(null);

  // Auto scroll to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeThreadId, isGenerating, progress]);

  const activeThread = activeThreadId ? getThreadById(activeThreadId) : null;

  /* ================= GENERATE ================= */
  const generateData = async () => {
    if (!prompt?.trim()) return;

    setIsGenerating(true);
    setProgress(0);
    setStatusMessage("Initializing...");
    
    // Start engine hum
    audioKinetics.startEngineHum();

    let threadId = activeThreadId;
    if (!threadId) {
      threadId = createThread(prompt);
      setActiveThreadId(threadId);
    } else {
      addMessageToThread(threadId, {
        role: "user",
        content: prompt,
        time: new Date().toLocaleString(),
      });
    }

    // Clear input
    setPrompt("");

    const backendUrl = import.meta.env.VITE_BACKEND_URL || "http://localhost:5000";
    const eventSource = new EventSource(
      `${backendUrl}/generate-stream?prompt=${encodeURIComponent(prompt)}&region=${region}`
    );

    eventSource.onmessage = (event) => {
      const payload = JSON.parse(event.data);

      if (payload.error) {
        eventSource.close();
        setIsGenerating(false);
        audioKinetics.stopEngineHum();
        audioKinetics.playLockdownThud();
        
        // Trigger shake
        setIsShaking(true);
        setTimeout(() => setIsShaking(false), 500);

        // Firewall Rejection as chat message
        addMessageToThread(threadId, {
          role: "assistant",
          type: "error",
          content: payload.message || "Request rejected by Galarix Firewall.",
          time: new Date().toLocaleString()
        });
        return;
      }

      if (payload.progress !== undefined) {
        setProgress(payload.progress);
        if (payload.progress < 20) setStatusMessage("Routing input...");
        else if (payload.progress < 50) setStatusMessage("Resolving entities & intent...");
        else if (payload.progress < 85) setStatusMessage("Enriching schema...");
        else if (payload.progress < 95) setStatusMessage("Compiling statistical model...");
        else setStatusMessage("Finalizing...");
        return;
      }

      if (payload.done) {
        setIsGenerating(false);
        audioKinetics.stopEngineHum();
        addAIResponseToThread(threadId, payload);
        eventSource.close();
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
      setIsGenerating(false);
      audioKinetics.stopEngineHum();
      audioKinetics.playLockdownThud();
      
      setIsShaking(true);
      setTimeout(() => setIsShaking(false), 500);

      addMessageToThread(threadId, {
        role: "assistant",
        type: "error",
        content: "Network error: Failed to connect to Galarix Engine.",
        time: new Date().toLocaleString()
      });
    };
  };

  return (
    <div className="flex flex-col h-full bg-slate-50 dark:bg-surface-950 font-sans relative">
      {isGenerating && <DataStreamMatrix />}
      
      {/* ================= CHAT HISTORY AREA ================= */}
      <div className="flex-1 min-h-0 overflow-y-auto">
        
        {/* If no thread active, show Welcome & Engine Status */}
        {!activeThread && (
          <div className="max-w-4xl mx-auto px-6 py-12 animate-fade-in mt-6">
            <div className="text-center mb-10">
              <div className="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center shadow-lg shadow-brand-500/20 mb-6">
                <svg className="w-10 h-10 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <h1 className="text-3xl md:text-4xl font-black text-slate-900 dark:text-white tracking-tight mb-4 flex items-center justify-center gap-2">
                GALARIX SYNTHETIC CORE <Sparkles className="text-brand-500" size={24} />
              </h1>
              <p className="text-slate-500 dark:text-slate-400 text-sm max-w-lg mx-auto">
                Ground your analytics pipelines with regulator-ready financial data. Generate mathematically unique datasets purely from intent descriptions.
              </p>
            </div>

            {/* Engine Grid Status with high Pizzazz */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
              
              <div className="card-glow p-5 flex flex-col gap-3 relative overflow-hidden group">
                <div className="absolute top-0 right-0 p-4 opacity-5">
                  <Terminal size={64} />
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Horizon 1 Generator</span>
                </div>
                <h3 className="text-sm font-bold text-slate-800 dark:text-white mt-1">Cross-Sectional Modeling</h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                  Resolves target columns, types, ranges and distribution families (Normal, LogNormal, Student-T, Cauchy).
                </p>
              </div>

              <div className="card p-5 flex flex-col gap-3 relative overflow-hidden group hover:border-brand-500/40 transition-colors">
                <div className="absolute top-0 right-0 p-4 opacity-5">
                  <Shield size={64} />
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Prompt Firewall</span>
                </div>
                <h3 className="text-sm font-bold text-slate-800 dark:text-white mt-1">Regulatory Guardrails</h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                  Blocks PII, malicious scripts, and illegal instructions. Safe for enterprise networks.
                </p>
              </div>

              <div className="card p-5 flex flex-col gap-3 relative overflow-hidden group hover:border-brand-500/40 transition-colors">
                <div className="absolute top-0 right-0 p-4 opacity-5">
                  <Activity size={64} />
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Trust Certificates</span>
                </div>
                <h3 className="text-sm font-bold text-slate-800 dark:text-white mt-1">Mathematical Validation</h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                  Every generation runs through KS and EMD compliance tests against primary financial distributions.
                </p>
              </div>

            </div>

            {/* Quick stats / facts bar */}
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 flex items-center justify-around flex-wrap gap-4 text-center">
              <div>
                <div className="text-lg font-black text-brand-500">20+</div>
                <div className="text-[10px] uppercase font-bold text-slate-400">Financial Models</div>
              </div>
              <div className="w-px h-8 bg-slate-200 dark:bg-slate-800" />
              <div>
                <div className="text-lg font-black text-brand-500">100%</div>
                <div className="text-[10px] uppercase font-bold text-slate-400">PII Clean</div>
              </div>
              <div className="w-px h-8 bg-slate-200 dark:bg-slate-800" />
              <div>
                <div className="text-lg font-black text-brand-500">7 Region</div>
                <div className="text-[10px] uppercase font-bold text-slate-400">Regulatory Rules</div>
              </div>
            </div>
          </div>
        )}

        {/* If thread active, render messages */}
        {activeThread && (
          <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 flex flex-col gap-8">
            {activeThread.messages.map((msg, idx) => (
              <div key={idx} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                
                {/* Assistant Avatar */}
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-500 to-cyan-500 flex items-center justify-center shrink-0 shadow-sm mt-1">
                    <Bot size={16} className="text-white" />
                  </div>
                )}

                {/* Message Bubble */}
                <div className={`max-w-[85%] ${msg.role === 'user' ? 'bg-slate-800 text-white rounded-2xl rounded-tr-sm px-5 py-3.5 shadow-sm' : ''}`}>
                  
                  {/* USER MESSAGE */}
                  {msg.role === 'user' && (
                    <div className="text-[15px] leading-relaxed">{msg.content}</div>
                  )}

                  {/* ASSISTANT MESSAGE - ERROR (FIREWALL) */}
                  {msg.role === 'assistant' && msg.type === 'error' && (
                    <div className="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 rounded-2xl rounded-tl-sm px-5 py-4 shadow-sm animate-fade-in">
                      <div className="flex items-center gap-2 text-red-600 dark:text-red-400 font-bold text-sm mb-1">
                        <ShieldAlert size={16} /> Firewall Rejection
                      </div>
                      <p className="text-sm text-red-700 dark:text-red-300 leading-relaxed">
                        {msg.content}
                      </p>
                    </div>
                  )}

                  {/* ASSISTANT MESSAGE - DATA DASHBOARD */}
                  {msg.role === 'assistant' && msg.type === 'data_response' && (
                    <div className="w-full animate-fade-in">
                      <DataDashboard payload={msg} prompt={activeThread.messages[idx-1]?.content} region={region} genRows={1000} />
                    </div>
                  )}
                  
                </div>

                {/* User Avatar */}
                {msg.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-slate-600 to-slate-800 flex items-center justify-center shrink-0 shadow-sm mt-1">
                    <span className="text-white text-xs font-bold">U</span>
                  </div>
                )}

              </div>
            ))}

            {/* GENERATING INDICATOR */}
            {isGenerating && (
              <div className="flex gap-4">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-500 to-cyan-500 flex items-center justify-center shrink-0 shadow-sm mt-1">
                  <Bot size={16} className="text-white" />
                </div>
                <div className="max-w-[85%] bg-white dark:bg-surface-900 border border-slate-200 dark:border-slate-800 rounded-2xl rounded-tl-sm p-5 shadow-sm animate-fade-in w-[400px]">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <svg className="animate-spin h-4 w-4 text-brand-500" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">{statusMessage}</span>
                    </div>
                    <span className="text-xs font-mono font-bold text-brand-500">{progress}%</span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                    <div className="h-full bg-brand-500 rounded-full transition-all duration-300" style={{ width: `${progress}%` }} />
                  </div>
                </div>
              </div>
            )}
            
            <div ref={chatEndRef} />
          </div>
        )}
      </div>

      {/* ================= INPUT AREA ================= */}
      <div className="shrink-0 w-full bg-slate-50 dark:bg-surface-950 pt-4 pb-6 px-4 md:px-8 border-t border-slate-200 dark:border-slate-800">
        <div className="max-w-4xl mx-auto">
          
          {/* Prominent Jurisdiction Region Selector Pills */}
          <div className="flex items-center gap-2 mb-3 overflow-x-auto py-1 custom-scrollbar shrink-0">
            <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest whitespace-nowrap flex items-center gap-1.5">
              <Globe2 size={12} /> Target Jurisdiction:
            </span>
            <div className="flex items-center gap-1.5">
              {Object.entries(REGIONS).map(([code, r]) => (
                <button
                  key={code}
                  onClick={() => setRegion(code)}
                  className={`flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold transition-all duration-200 border
                    ${region === code
                      ? "bg-brand-500/10 border-brand-500 text-brand-600 dark:text-brand-400 shadow-sm"
                      : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 hover:border-slate-300 dark:hover:border-slate-700"
                    }`}
                >
                  <span>{r.flag}</span>
                  <span>{code}</span>
                  <span className="text-[9px] opacity-60 font-semibold">{r.regulator}</span>
                </button>
              ))}
            </div>
          </div>

          <div className={`bg-white dark:bg-surface-900 border border-slate-200 dark:border-slate-800 shadow-xl rounded-2xl p-3 flex flex-col gap-2 relative z-10 ${isShaking ? 'animate-shake border-red-500 shadow-red-500/20' : ''}`}>
            <textarea
              ref={textareaRef}
              className="w-full resize-none bg-transparent border-0 text-slate-800 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-0 text-sm leading-relaxed px-2 py-1 max-h-[150px] overflow-y-auto"
              placeholder="Message Galarix... (e.g., Generate 1000 rows of credit card transactions)"
              rows={1}
              value={prompt}
              onChange={(e) => {
                setPrompt(e.target.value);
                e.target.style.height = 'auto';
                e.target.style.height = e.target.scrollHeight + 'px';
              }}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); generateData(); } }}
            />
            
            <div className="flex items-center justify-between px-2 pt-2 border-t border-slate-100 dark:border-slate-800">
              <div className="flex items-center gap-1.5 text-xs text-emerald-500 font-semibold">
                <CheckCircle size={14} /> Ready for input
              </div>

              <button
                onClick={generateData}
                disabled={!prompt?.trim() || isGenerating}
                className="w-8 h-8 rounded-full bg-brand-600 hover:bg-brand-500 flex items-center justify-center text-white disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-md shadow-brand-500/20"
              >
                {isGenerating ? (
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 10.5L12 3m0 0l7.5 7.5M12 3v18" />
                  </svg>
                )}
              </button>
            </div>
          </div>
          <div className="text-center mt-3 text-[10px] text-slate-400">
            Galarix can make mistakes. Verify critical datasets.
          </div>
        </div>
      </div>
    </div>
  );
}

export default PromptInput;