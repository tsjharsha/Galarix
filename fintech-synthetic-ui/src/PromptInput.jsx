import { useEffect, useState } from "react";

/* ================= TEMPLATE DATA ================= */
const TEMPLATE_GROUPS = {
  "Credit Card Activity": [
    "Simulate 50 realistic credit card transactions for a single user over 30 days, including groceries, dining, utilities, and one large airline ticket purchase.",
    "Generate daily credit card transactions with recurring subscriptions and occasional high-value electronics purchases.",
  ],
  "Investment Statements": [
    "Create an investment portfolio statement showing monthly recurring stock buys (DCA), dividend reinvestments, and portfolio value over 12 months.",
    "Simulate mutual fund investments with SIP contributions and quarterly returns.",
  ],
  "Payroll Simulation": [
    "Generate payroll transactions for a startup with 5 employees including monthly salaries, tax deductions, and reimbursements.",
    "Simulate bi-weekly payroll payments with bonuses and deductions.",
  ],
  "SaaS Billing": [
    "Generate subscription billing data for a B2B SaaS platform including monthly renewals, upgrades, downgrades, and churn.",
    "Simulate SaaS invoices with tiered pricing and annual subscriptions.",
  ],
};


function PromptInput() {
  const [prompt, setPrompt] = useState("");
  const [data, setData] = useState([]);
  const [history, setHistory] = useState([]);
  
 





  /* ===== Template UI State ===== */
  const [showTemplates, setShowTemplates] = useState(false);
  const [activeCategory, setActiveCategory] = useState("Credit Card Activity");
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);

  /* ===== Pagination ===== */
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 3;

  const paginatedHistory = history.slice(
    (page - 1) * PAGE_SIZE,
    page * PAGE_SIZE
  );
  const generateData = () => {
  if (!prompt.trim()) return;

  setIsGenerating(true);
  setProgress(0);
  setData([]);

  const eventSource = new EventSource(
    `http://127.0.0.1:5000/generate-stream?prompt=${encodeURIComponent(prompt)}`
  );

  let finalTransactions = [];

  eventSource.onmessage = (event) => {
    const payload = JSON.parse(event.data);

    // 🔁 Progress updates
    if (payload.progress !== undefined) {
      setProgress(payload.progress);
    }

    // ✅ Done event
    if (payload.done) {
      finalTransactions = payload.transactions;
      setData(finalTransactions);

      eventSource.close();
      setIsGenerating(false);

      // 🔥 THIS WAS MISSING
      loadHistory();   // ✅ history now refreshes
      setPage(1);
    }
  };

  eventSource.onerror = () => {
    console.error("SSE error");
    eventSource.close();
    setIsGenerating(false);
  };
};

  /* ===== Load History ===== */
  const loadHistory = async () => {
    const res = await fetch("http://127.0.0.1:5000/history");
    const json = await res.json();
    setHistory(json);
  };

  /* ===== Clear History ===== */
  const clearHistory = async () => {
    await fetch("http://127.0.0.1:5000/history/clear", { method: "POST" });
    setHistory([]);
    setPage(1);
  };

  /* ===== Download CSV ===== */
  const downloadCSV = async () => {
    const res = await fetch("http://127.0.0.1:5000/download-csv", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transactions: data }),
    });

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "transactions.csv";
    a.click();
  };

  useEffect(() => {
    loadHistory();
  }, []);

  return (
    <div className="min-h-screen bg-white dark:bg-slate-950 transition-colors">
      <div className="max-w-6xl mx-auto px-6 py-10 text-slate-800 dark:text-slate-200">

        

        {/* ================= PROMPT CARD ================= */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-sm p-6 relative">

          {/* ===== Simulation Parameters ===== */}
          <div className="mb-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs tracking-widest text-slate-400">
                SIMULATION PARAMETERS
              </span>

              <button
                onClick={() => setShowTemplates(!showTemplates)}
                className="text-xs font-medium text-blue-600"
              >
                TEMPLATES {showTemplates ? "▲" : "▼"}
              </button>
            </div>

            {/* Category Pills */}
            <div className="flex gap-2 flex-wrap">
              {Object.keys(TEMPLATE_GROUPS).map((cat) => (
                <button
                  key={cat}
                  onClick={() => setActiveCategory(cat)}
                  className={`px-3 py-1 rounded-full text-xs border transition ${
                    activeCategory === cat
                      ? "bg-blue-600 text-white border-blue-600"
                      : "bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700"
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          {/* ===== Templates Dropdown ===== */}
          {showTemplates && (
            <div className="absolute right-6 z-20 w-96 bg-white dark:bg-slate-900
                            border border-slate-200 dark:border-slate-700
                            rounded-xl shadow-lg p-3 max-h-64 overflow-y-auto">
              {TEMPLATE_GROUPS[activeCategory].map((tpl, i) => (
                <div
                  key={i}
                  onClick={() => {
                    setPrompt(tpl);
                    setShowTemplates(false);
                  }}
                  className="p-3 rounded-lg cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  <div className="font-medium text-sm">
                    {activeCategory}
                  </div>
                  <div className="text-xs text-slate-500 mt-1 line-clamp-2">
                    {tpl}
                  </div>
                </div>
              ))}
            </div>
          )}

        {/* ===== Textarea with Clear Button ===== */}
<div className="relative">
  <textarea
    className="w-full h-32 resize-none rounded-xl border-2 border-blue-500
               bg-white dark:bg-slate-950
               p-4 pr-12 text-sm placeholder-slate-400
               focus:outline-none focus:ring-2 focus:ring-blue-400"
    placeholder="Describe the fintech dataset you want to generate..."
    value={prompt}
    onChange={(e) => setPrompt(e.target.value)}
  />
   {/* ===== Progress Bar (ADDED) ===== */}



  {/* Clear Prompt Button */}
  {prompt.trim() && (
    <button
      onClick={() => setPrompt("")}
      className="absolute top-3 right-3 w-7 h-7
                 flex items-center justify-center
                 rounded-full
                 text-slate-400 hover:text-slate-700
                 dark:text-slate-500 dark:hover:text-slate-200
                 hover:bg-slate-100 dark:hover:bg-slate-800
                 transition"
      title="Clear prompt"
    >
      ✕
    </button>
  )}
</div>
{isGenerating && (
  <div className="mt-4">
    <div className="w-full bg-slate-200 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
      <div
        className="h-2 bg-blue-600 transition-all duration-300"
        style={{ width: `${progress}%` }}
      />
    </div>
    <div className="text-xs text-slate-400 mt-1">
      Generating data… {progress}%
    </div>
  </div>
)}


          {/* ===== Generate Button ===== */}
          <div className="flex justify-end mt-6">
            <button
               onClick={generateData}
               disabled={!prompt.trim() || isGenerating}
               className={`px-6 py-3 rounded-xl text-sm font-medium transition ${
               !prompt.trim() || isGenerating
               ? "bg-slate-100 dark:bg-slate-800 text-slate-400 cursor-not-allowed"
               : "bg-blue-600 text-white hover:bg-blue-700"
        }`}
>
  {isGenerating ? "Generating..." : "Generate Synthetic Data"}
</button>

          </div>
        </div>

        {/* ================= EMPTY STATE ================= */}
        {data.length === 0 && !isGenerating && (
        <div className="mt-12 border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-2xl p-16 text-center text-slate-500">
          <div className="text-lg font-semibold mb-2">
             No Transactions Generated Yet
          </div>
          <p className="text-sm">
             The backend is ready to accept your prompt.
          </p>
  </div>
)}


        {/* ================= TABLE ================= */}
        {data.length > 0 && (
          <>
            <div className="flex justify-end mt-8">
              <button
                onClick={downloadCSV}
                className="px-4 py-2 text-sm rounded-lg bg-slate-800 text-white hover:bg-slate-900"
              >
                ⬇ Download CSV
              </button>
            </div>

            <div className="overflow-hidden rounded-xl border border-slate-200 dark:border-slate-700 mt-4">
              <table className="w-full border-collapse bg-white dark:bg-slate-900 text-sm">
                <thead className="bg-slate-100 dark:bg-slate-800">
                  <tr>
                    <th className="px-4 py-3 text-left">Date</th>
                    <th className="px-4 py-3 text-left">Amount</th>
                    <th className="px-4 py-3 text-left">Type</th>
                  </tr>
                </thead>
                <tbody>
                  {data.map((row, i) => (
                    <tr key={i} className="border-t dark:border-slate-700">
                      <td className="px-4 py-3">{row.date}</td>
                      <td className="px-4 py-3">{row.amount}</td>
                      <td className="px-4 py-3">{row.type}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}

        {/* ================= ACTIVITY LEDGER ================= */}
        <div className="mt-16">
          <div className="flex items-center justify-between mb-6">
            <div className="text-xs tracking-widest text-slate-400">
              PROMPT HISTORY
            </div>

            {history.length > 0 && (
              <button
                onClick={clearHistory}
                className="text-xs tracking-widest text-red-500 hover:underline"
              >
                CLEAR HISTORY
              </button>
            )}
          </div>

          {paginatedHistory.map((h, i) => (
            <div
              key={i}
              className="max-w-xl bg-white dark:bg-slate-900
                         border border-slate-200 dark:border-slate-700
                         rounded-2xl p-5 mb-4 shadow-sm"
            >
              <div className="text-xs text-slate-400 mb-2">{h.time}</div>
              <p className="text-sm leading-relaxed">{h.prompt}</p>
            </div>
          ))}

          {history.length > PAGE_SIZE && (
            <div className="flex items-center gap-4 mt-6 text-sm">
              <button
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
                className="px-3 py-1 rounded border disabled:opacity-40"
              >
                Prev
              </button>

              <span className="text-slate-500">
                Page {page} of {Math.ceil(history.length / PAGE_SIZE)}
              </span>

              <button
                disabled={page * PAGE_SIZE >= history.length}
                onClick={() => setPage(page + 1)}
                className="px-3 py-1 rounded border disabled:opacity-40"
              >
                Next
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default PromptInput;
