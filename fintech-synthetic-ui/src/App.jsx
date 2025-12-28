import { useEffect, useState } from "react";
import Header from "./Header";
import PromptInput from "./PromptInput";

function App() {
  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem("theme") === "dark";
  });

  useEffect(() => {
    const root = document.documentElement;
    if (darkMode) {
      root.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      root.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  }, [darkMode]);

  return (
    <div className="min-h-screen bg-white dark:bg-[#050B1A] transition-colors">
      <Header darkMode={darkMode} setDarkMode={setDarkMode} />
      <PromptInput />
    </div>
  );
}

export default App;
