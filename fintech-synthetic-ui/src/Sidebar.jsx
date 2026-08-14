import { useState, useRef } from "react";
import { usePromptHistory } from "./context/PromptHistoryContext";

/* ---------- GROUPING ---------- */
function groupHistoryByDate(threads) {
  const today = [], yesterday = [], older = [];
  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const startOfYesterday = new Date(startOfToday);
  startOfYesterday.setDate(startOfYesterday.getDate() - 1);

  threads.forEach((thread) => {
    const d = new Date(thread.time);
    if (d >= startOfToday) today.push(thread);
    else if (d >= startOfYesterday) yesterday.push(thread);
    else older.push(thread);
  });
  return { today, yesterday, older };
}

function Sidebar({ isOpen, onClose, onSelectThread, onNewSession, activeThreadId }) {
  const [search, setSearch] = useState("");
  const [deleteThreadId, setDeleteThreadId] = useState(null);
  const { threads, clearHistory, togglePin, deleteThread, renameThread } = usePromptHistory();

  const filtered = threads.filter((t) => t.title.toLowerCase().includes(search.toLowerCase()));
  const pinned = filtered.filter((t) => t.pinned);
  const unpinned = filtered.filter((t) => !t.pinned);
  const { today, yesterday, older } = groupHistoryByDate(unpinned);

  return (
    <>
      <div className={`fixed top-0 left-0 h-full w-80 z-40
        bg-white dark:bg-surface-950 border-r border-slate-200 dark:border-white/5
        transform transition-transform duration-300 ease-in-out flex flex-col
        ${isOpen ? "translate-x-0" : "-translate-x-full"}`}
      >
        {/* HEADER */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center">
              <svg className="w-3 h-3 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <span className="text-[11px] font-semibold tracking-widest text-slate-400 dark:text-slate-500 uppercase">
              Sessions
            </span>
          </div>
          <button onClick={onClose}
            className="w-7 h-7 rounded-lg flex items-center justify-center
              hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 transition"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* SEARCH */}
        <div className="px-4 py-3">
          <div className="relative mb-3">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
            </svg>
            <input
              type="text"
              placeholder="Search sessions..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-2 rounded-lg text-xs
                bg-slate-50 dark:bg-slate-900/50
                text-slate-700 dark:text-slate-200
                border border-slate-200 dark:border-white/5
                focus:outline-none focus:ring-1 focus:ring-brand-500 focus:border-brand-500
                placeholder-slate-500 transition"
            />
          </div>
          <button 
            onClick={onNewSession}
            className="w-full py-2.5 rounded-lg text-xs font-semibold text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 transition flex items-center justify-center gap-2"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            New Session
          </button>
        </div>

        {/* SCROLL */}
        <div className="flex-1 overflow-y-auto px-3 py-2">
          {filtered.length === 0 && (
            <div className="text-center py-10">
              <div className="text-3xl mb-2">💬</div>
              <div className="text-xs text-slate-400">No sessions yet</div>
            </div>
          )}

          {pinned.length > 0 && <SectionLabel title="PINNED" />}
          {pinned.map((t) => <ThreadCard key={t.id} thread={t} isActive={String(t.id) === String(activeThreadId)} onSelect={onSelectThread} onDelete={setDeleteThreadId} />)}

          {!search && today.length > 0 && <SectionLabel title="TODAY" />}
          {!search && today.map((t) => <ThreadCard key={t.id} thread={t} isActive={String(t.id) === String(activeThreadId)} onSelect={onSelectThread} onDelete={setDeleteThreadId} />)}

          {!search && yesterday.length > 0 && <SectionLabel title="YESTERDAY" />}
          {!search && yesterday.map((t) => <ThreadCard key={t.id} thread={t} isActive={String(t.id) === String(activeThreadId)} onSelect={onSelectThread} onDelete={setDeleteThreadId} />)}

          {!search && older.length > 0 && <SectionLabel title="OLDER" />}
          {!search && older.map((t) => <ThreadCard key={t.id} thread={t} isActive={String(t.id) === String(activeThreadId)} onSelect={onSelectThread} onDelete={setDeleteThreadId} />)}

          {search && filtered.map((t) => <ThreadCard key={t.id} thread={t} isActive={String(t.id) === String(activeThreadId)} onSelect={onSelectThread} onDelete={setDeleteThreadId} />)}
        </div>

        {/* FOOTER */}
        {threads.length > 0 && (
          <div className="p-4 border-t border-slate-100 dark:border-slate-800">
            <button onClick={clearHistory}
              className="text-[10px] font-medium tracking-widest text-red-400 hover:text-red-500 transition uppercase"
            >
              Clear All
            </button>
          </div>
        )}

        {/* DELETE MODAL */}
        {deleteThreadId && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl shadow-2xl w-80 animate-scale-in border border-slate-200 dark:border-slate-700">
              <div className="text-sm font-semibold text-slate-800 dark:text-white">Delete session?</div>
              <div className="text-xs text-slate-500 mt-1.5">This action cannot be undone.</div>
              <div className="mt-5 flex justify-end gap-2">
                <button onClick={() => setDeleteThreadId(null)} className="btn-ghost text-xs">Cancel</button>
                <button onClick={() => { deleteThread(deleteThreadId); setDeleteThreadId(null); }}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-red-500 text-white hover:bg-red-600 transition">
                  Delete
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Overlay for mobile */}
      {isOpen && (
        <div className="fixed inset-0 z-30 bg-black/20 backdrop-blur-sm lg:hidden" onClick={onClose} />
      )}
    </>
  );
}

/* ---------- SECTION LABEL ---------- */
function SectionLabel({ title }) {
  return (
    <div className="mt-4 mb-2 px-2 text-[10px] font-semibold tracking-widest text-slate-400 dark:text-slate-500 uppercase">
      {title}
    </div>
  );
}

/* ---------- THREAD CARD ---------- */
function ThreadCard({ thread, isActive, onSelect, onDelete }) {
  const lastAI = [...thread.messages].reverse().find((m) => m.role === "assistant" && m.type === "data_response");
  const entities = lastAI?.detected_entities || lastAI?.entities || (lastAI?.entity ? [lastAI.entity] : []);

  return (
    <div
      onClick={() => onSelect(thread.id)}
      className={`group cursor-pointer rounded-xl p-3 mb-1.5 transition-all duration-200
        ${isActive
          ? "bg-brand-50 dark:bg-brand-500/10 border border-brand-200 dark:border-brand-500/20"
          : "hover:bg-slate-50 dark:hover:bg-white/5 border border-transparent"
        }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="text-xs font-medium text-slate-800 dark:text-slate-200 truncate">
            {thread.title}
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5">{thread.time}</div>
        </div>
        <button
          onClick={(e) => { e.stopPropagation(); onDelete(thread.id); }}
          className="opacity-0 group-hover:opacity-100 w-6 h-6 rounded-md flex items-center justify-center
            hover:bg-red-100 dark:hover:bg-red-500/10 text-slate-400 hover:text-red-500 transition"
        >
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
          </svg>
        </button>
      </div>

      {entities.length > 0 && (
        <div className="flex gap-1 mt-2 flex-wrap">
          {entities.map((e) => (
            <span key={e} className="text-[9px] px-1.5 py-0.5 rounded bg-brand-100 dark:bg-brand-900/30 text-brand-600 dark:text-brand-400 font-medium">
              {e.replaceAll("_", " ")}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export default Sidebar;