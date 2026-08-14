import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Header from "../Header";
import PromptInput from "../PromptInput";
import Sidebar from "../Sidebar";
import { usePromptHistory } from "../context/PromptHistoryContext";
import { useAuth } from "../context/AuthContext";

function Studio() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const { threadId } = useParams();
  const { getThreadById } = usePromptHistory();

  const [prompt, setPrompt] = useState("");
  const [activeThreadId, setActiveThreadId] = useState(threadId || null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // States for restored data
  const [restoredSchema, setRestoredSchema] = useState(null);
  const [restoredData, setRestoredData] = useState([]);
  const [restoredDataContract, setRestoredDataContract] = useState(null);
  const [restoredStatModel, setRestoredStatModel] = useState(null);
  const [restoredVariables, setRestoredVariables] = useState(null);
  const [restoredDistributions, setRestoredDistributions] = useState(null);
  const [restoredDependencies, setRestoredDependencies] = useState(null);
  const [restoredConstraints, setRestoredConstraints] = useState(null);
  const [restoredDetectedEntities, setRestoredDetectedEntities] = useState([]);
  const [restoredConfidence, setRestoredConfidence] = useState(0);
  const [restoredIntent, setRestoredIntent] = useState(null);

  // Sync activeThreadId with URL params
  useEffect(() => {
    if (threadId && threadId !== activeThreadId) {
      handleSelectThread(threadId);
    }
  }, [threadId]);

  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem("theme");
    return saved ? saved === "dark" : true; // Default to dark mode
  });

  /* ================= THEME ================= */
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

  /* ================= AUTH GATE ================= */
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
    }
  }, [isAuthenticated, navigate]);

  if (!isAuthenticated) return null;

  /* ================= THREAD SELECT ================= */
  const handleSelectThread = (id) => {
    setActiveThreadId(id);
    setPrompt("");
    if (id !== threadId) {
      navigate(`/studio/${id}`);
    }

    const thread = getThreadById(id);
    if (!thread) return;

    const lastAssistant = [...thread.messages]
      .reverse()
      .find((m) => m.role === "assistant" && m.type === "data_response");

    if (!lastAssistant) return;

    setRestoredSchema(lastAssistant.schema || null);
    setRestoredData(lastAssistant.sample_data || lastAssistant.transactions || []);
    setRestoredDataContract(lastAssistant.dataContract || null);
    setRestoredStatModel(lastAssistant.statisticalModel || null);
    setRestoredVariables(lastAssistant.variables || null);
    setRestoredDistributions(lastAssistant.distributions || null);
    setRestoredDependencies(lastAssistant.dependencies || null);
    setRestoredConstraints(lastAssistant.constraints || null);
    setRestoredDetectedEntities(lastAssistant.detected_entities || []);
    setRestoredConfidence(lastAssistant.confidence || 0);
    setRestoredIntent(lastAssistant.intent || null);
  };

  const handleNewSession = () => {
    setActiveThreadId(null);
    setPrompt("");
    navigate('/studio');
    setRestoredSchema(null);
    setRestoredData([]);
    setRestoredDataContract(null);
    setRestoredStatModel(null);
    setRestoredVariables(null);
    setRestoredDistributions(null);
    setRestoredDependencies(null);
    setRestoredConstraints(null);
    setRestoredDetectedEntities([]);
    setRestoredConfidence(0);
    setRestoredIntent(null);
  };

  return (
    <div className="h-screen overflow-hidden bg-white dark:bg-surface-950 font-sans">
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        activeThreadId={activeThreadId}
        onSelectThread={handleSelectThread}
      />

      <Header
        darkMode={darkMode}
        setDarkMode={setDarkMode}
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        activeEntities={restoredDetectedEntities}
        onNewSession={handleNewSession}
        activeRegion={restoredIntent?.region}
        onTemplateSelect={setPrompt}
      />

      <main
        className={`
          flex flex-col
          relative pt-[72px] h-screen overflow-hidden
          transition-all duration-300 ease-in-out
          ${sidebarOpen ? "ml-80" : "ml-0"}
        `}
      >
        <div className="flex-1 min-h-0 w-full relative">
          <PromptInput
            prompt={prompt}
          setPrompt={setPrompt}
          activeThreadId={activeThreadId}
          setActiveThreadId={(id) => {
            setActiveThreadId(id);
            navigate(`/studio/${id}`);
          }}
          restoredSchema={restoredSchema}
          restoredData={restoredData}
          restoredDataContract={restoredDataContract}
          restoredStatModel={restoredStatModel}
          restoredVariables={restoredVariables}
          restoredDistributions={restoredDistributions}
          restoredDependencies={restoredDependencies}
          restoredConstraints={restoredConstraints}
          restoredDetectedEntities={restoredDetectedEntities}
          restoredConfidence={restoredConfidence}
          restoredIntent={restoredIntent}
        />
        </div>
      </main>
    </div>
  );
}

export default Studio;
