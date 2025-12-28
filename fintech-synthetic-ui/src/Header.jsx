function Header({ darkMode, setDarkMode }) {
  return (
    <header className="w-full border-b border-slate-200 dark:border-slate-800
                       bg-white dark:bg-[#050B1A]">
      <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">

        {/* Logo + Title */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold">
            🔒
          </div>
          <div>
            <div className="font-semibold text-slate-900 dark:text-white">
              FinSynth
            </div>
            <div className="text-xs tracking-widest text-slate-500 dark:text-slate-400">
              SYNTHETIC DATA ENGINE
            </div>
          </div>
        </div>

        {/* Dark Mode Toggle */}
        <button
          onClick={() => setDarkMode(!darkMode)}
          className="w-11 h-11 rounded-full flex items-center justify-center
                     bg-slate-100 dark:bg-slate-800
                     border border-slate-200 dark:border-slate-700
                     hover:scale-105 transition"
          title="Toggle theme"
        >
          {darkMode ? "☀️" : "🌙"}
        </button>
      </div>
    </header>
  );
}

export default Header;
