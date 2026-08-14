import { useAuth } from "./context/AuthContext";
import { Link } from "react-router-dom";
import { useState, useRef, useEffect } from "react";

const ENTITY_COLORS = {
  credit_card_activity: "from-blue-500 to-cyan-500",
  investment_statement: "from-emerald-500 to-teal-500",
  payroll: "from-purple-500 to-violet-500",
  saas_billing: "from-amber-500 to-yellow-500",
  insurance_claims: "from-red-500 to-rose-500",
  loans: "from-indigo-500 to-blue-500",
  bank_account_statement: "from-sky-500 to-blue-500",
  wire_transfers: "from-cyan-500 to-teal-500",
  atm_withdrawals: "from-orange-500 to-amber-500",
  mortgage_records: "from-violet-500 to-purple-500",
  buy_now_pay_later: "from-pink-500 to-rose-500",
  kyc_records: "from-lime-500 to-green-500",
  aml_transaction_alerts: "from-red-600 to-orange-500",
  crypto_trading_log: "from-yellow-500 to-orange-500",
  forex_transactions: "from-teal-500 to-cyan-500",
  options_trading: "from-fuchsia-500 to-pink-500",
  expense_reports: "from-slate-500 to-zinc-500",
  tax_records_w2: "from-green-500 to-emerald-500",
  pnl_statement: "from-blue-600 to-indigo-500",
  invoice_financing: "from-amber-600 to-yellow-500",
  generic: "from-slate-500 to-gray-500",
};

const ENTITY_LABELS = {
  credit_card_activity: "Credit Cards",
  investment_statement: "Investments",
  payroll: "Payroll",
  saas_billing: "SaaS Billing",
  insurance_claims: "Insurance",
  loans: "Loans",
  bank_account_statement: "Bank Statements",
  wire_transfers: "Wire Transfers",
  atm_withdrawals: "ATM",
  mortgage_records: "Mortgages",
  buy_now_pay_later: "BNPL",
  kyc_records: "KYC",
  aml_transaction_alerts: "AML Alerts",
  crypto_trading_log: "Crypto",
  forex_transactions: "Forex",
  options_trading: "Options",
  expense_reports: "Expenses",
  tax_records_w2: "Tax W-2",
  pnl_statement: "P&L",
  invoice_financing: "Invoice Finance",
  generic: "Generic",
};

const REGION_FLAGS = {
  US: { flag: "US", name: "United States" },
  UK: { flag: "UK", name: "United Kingdom" },
  EU: { flag: "EU", name: "European Union" },
  IN: { flag: "IN", name: "India" },
  JP: { flag: "JP", name: "Japan" },
  AU: { flag: "AU", name: "Australia" },
  BR: { flag: "BR", name: "Brazil" },
};

function Header({
  darkMode,
  setDarkMode,
  sidebarOpen,
  setSidebarOpen,
  activeEntities = [],
  onNewSession,
  activeRegion,
  onTemplateSelect,
}) {
  const { user, logout } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <header
      className={`
        fixed top-0 z-50 h-16
        border-b border-slate-200/80 dark:border-slate-800/80
        bg-white/80 dark:bg-surface-950/80
        backdrop-blur-xl
        transition-all duration-300 ease-in-out
        ${sidebarOpen ? "left-80 w-[calc(100%-20rem)]" : "left-0 w-full"}
      `}
    >
      <div className="h-full px-5 flex items-center justify-between">

        {/* LEFT */}
        <div className="flex items-center gap-3">
          {/* Sidebar Toggle */}
          <button
            id="sidebar-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="w-9 h-9 rounded-lg flex items-center justify-center
              hover:bg-slate-100 dark:hover:bg-slate-800
              text-slate-500 dark:text-slate-400
              transition-all duration-200"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            </svg>
          </button>

          {/* Back to Dashboard */}
          <Link to="/dashboard" className="flex items-center gap-2.5 px-3 py-1.5 rounded-xl hover:bg-slate-100 dark:hover:bg-white/5 transition-all">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center shadow-md shadow-brand-500/20">
              <svg className="w-4 h-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
              </svg>
            </div>
            <div className="hidden md:block">
              <div className="font-bold text-sm text-slate-900 dark:text-white tracking-tight">
                Dashboard
              </div>
            </div>
          </Link>

          {/* Divider */}
          <div className="hidden md:block w-px h-6 bg-slate-200 dark:bg-slate-700 mx-1" />

          {/* New Session */}
          <button
            id="new-session-btn"
            onClick={onNewSession}
            className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-lg
              text-xs font-medium text-brand-600 dark:text-brand-400
              hover:bg-brand-50 dark:hover:bg-brand-500/10
              transition-all duration-200"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            New
          </button>
        </div>

        {/* CENTER - Templates & Entities */}
        <div className="hidden lg:flex items-center gap-4">
          
          {/* Template Dropdown */}
          <div className="relative" ref={dropdownRef}>
            <button 
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 transition"
            >
              Select Template ▼
            </button>
            
            {dropdownOpen && (
              <div className="absolute top-full mt-2 left-0 w-64 max-h-96 overflow-y-auto bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl shadow-2xl z-50 custom-scrollbar">
                <div className="p-2">
                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider px-2 py-1 mb-1">Financial Entities</div>
                  {Object.entries(ENTITY_LABELS).filter(([k]) => k !== 'generic').map(([key, label]) => (
                    <button
                      key={key}
                      onClick={() => {
                        onTemplateSelect?.(`Generate 1000 rows of ${label.toLowerCase()} data for the US region.`);
                        setDropdownOpen(false);
                      }}
                      className="w-full text-left px-3 py-2 text-xs text-slate-700 dark:text-slate-300 hover:bg-brand-50 dark:hover:bg-brand-500/10 hover:text-brand-600 dark:hover:text-brand-400 rounded-lg transition-colors flex items-center gap-2"
                    >
                      <div className={`w-2 h-2 rounded-full bg-gradient-to-r ${ENTITY_COLORS[key]}`} />
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="w-px h-6 bg-slate-200 dark:bg-slate-800 mx-1"></div>

          {/* Active Generation Indicators */}
          {activeRegion && REGION_FLAGS[activeRegion] && (
            <span className="px-2.5 py-1 rounded-lg text-[11px] font-bold text-slate-700 dark:text-slate-200
              bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
              {REGION_FLAGS[activeRegion].flag} {REGION_FLAGS[activeRegion].name}
            </span>
          )}
          {activeEntities.length > 0 && activeEntities.slice(0, 3).map((entity) => (
            <span
              key={entity}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-medium text-white
                bg-gradient-to-r ${ENTITY_COLORS[entity] || ENTITY_COLORS.generic}
                shadow-sm`}
            >
              {ENTITY_LABELS[entity] || entity.replaceAll("_", " ")}
            </span>
          ))}
          {activeEntities.length > 3 && (
            <span className="px-2 py-1 rounded-lg text-[11px] font-medium text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800">
              +{activeEntities.length - 3}
            </span>
          )}
        </div>

        {/* RIGHT */}
        <div className="flex items-center gap-2">
          {/* Hardened Badge */}
          <span className="hidden md:flex items-center gap-1 px-2 py-1 rounded-md text-[9px] font-bold tracking-wider uppercase
            bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20">
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
            </svg>
            Hardened
          </span>

          {/* Dark Mode */}
          <button
            id="theme-toggle"
            onClick={() => setDarkMode(!darkMode)}
            className="w-9 h-9 rounded-lg flex items-center justify-center
              hover:bg-slate-100 dark:hover:bg-slate-800
              text-slate-500 dark:text-slate-400
              transition-all duration-200"
          >
            {darkMode ? (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
              </svg>
            )}
          </button>

          {/* User Menu */}
          <div className="flex items-center gap-2 pl-2 border-l border-slate-200 dark:border-slate-700">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-400 to-purple-500 flex items-center justify-center text-white text-xs font-bold shadow-sm">
              {user?.name?.charAt(0) || "U"}
            </div>
            <span className="hidden md:block text-xs font-medium text-slate-600 dark:text-slate-300">
              {user?.name || "User"}
            </span>
            <button
              id="logout-btn"
              onClick={logout}
              className="ml-1 w-8 h-8 rounded-lg flex items-center justify-center
                hover:bg-red-50 dark:hover:bg-red-500/10
                text-slate-400 hover:text-red-500
                transition-all duration-200"
              title="Logout"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;