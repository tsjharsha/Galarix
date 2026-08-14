import { createContext, useContext, useState, useEffect } from "react";
import { db } from "../firebase";
import { collection, query, where, onSnapshot, addDoc, updateDoc, deleteDoc, doc, orderBy } from "firebase/firestore";
import { useAuth } from "./AuthContext";

const PromptHistoryContext = createContext();

export function PromptHistoryProvider({ children }) {
  const [threads, setThreads] = useState([]);
  const { user } = useAuth();

  /* ================= LOAD THREADS FROM FIRESTORE ================= */
  useEffect(() => {
    if (!user) {
      setThreads([]);
      return;
    }

    const q = query(
      collection(db, "threads"),
      where("userId", "==", user.uid),
      orderBy("createdAt", "desc")
    );

    const unsubscribe = onSnapshot(q, (snapshot) => {
      const loadedThreads = snapshot.docs.map((doc) => ({
        id: doc.id,
        ...doc.data(),
      }));
      setThreads(loadedThreads);
    });

    return () => unsubscribe();
  }, [user]);

  /* ================= CREATE NEW THREAD ================= */
  const createThread = async (prompt) => {
    if (!prompt?.trim() || !user) return null;

    const newThread = {
      userId: user.uid,
      title: prompt.slice(0, 40),
      time: new Date().toLocaleString(),
      createdAt: Date.now(),
      pinned: false,
      messages: [
        {
          role: "user",
          content: prompt,
          time: new Date().toLocaleString(),
        },
      ],
    };

    try {
      const docRef = await addDoc(collection(db, "threads"), newThread);
      return docRef.id;
    } catch (e) {
      console.error("Error creating thread: ", e);
      return null;
    }
  };

  /* ================= ADD MESSAGE ================= */
  const addMessageToThread = async (threadId, message) => {
    if (!user) return;
    const thread = threads.find(t => t.id === threadId);
    if (!thread) return;

    try {
      const threadRef = doc(db, "threads", threadId);
      await updateDoc(threadRef, {
        messages: [...thread.messages, message]
      });
    } catch (e) {
      console.error("Error adding message: ", e);
    }
  };

  /* ================= ADD AI RESPONSE ================= */
  const addAIResponseToThread = async (threadId, responseData) => {
    const message = {
      role: "assistant",
      type: "data_response",
      entity: responseData.entity,
      entities: responseData.entities,
      detected_entities: responseData.detected_entities,
      status: responseData.status,
      confidence: responseData.confidence,
      intent: responseData.intent,
      schema: responseData.schema,
      variables: responseData.variables,
      distributions: responseData.distributions,
      dependencies: responseData.dependencies,
      constraints: responseData.constraints,
      dataContract: responseData.dataContract,
      statisticalModel: responseData.statisticalModel,
      sample_data: responseData.sample_data,
      transactions: responseData.transactions,
      time: new Date().toLocaleString(),
    };

    await addMessageToThread(threadId, message);
  };

  /* ================= TOGGLE PIN ================= */
  const togglePin = async (id) => {
    const thread = threads.find(t => t.id === id);
    if (!thread) return;

    try {
      const threadRef = doc(db, "threads", id);
      await updateDoc(threadRef, { pinned: !thread.pinned });
    } catch (e) {
      console.error("Error toggling pin: ", e);
    }
  };

  /* ================= RENAME THREAD ================= */
  const renameThread = async (id, newTitle) => {
    if (!newTitle?.trim()) return;

    try {
      const threadRef = doc(db, "threads", id);
      await updateDoc(threadRef, { title: newTitle });
    } catch (e) {
      console.error("Error renaming thread: ", e);
    }
  };

  /* ================= DELETE THREAD ================= */
  const deleteThread = async (id) => {
    try {
      await deleteDoc(doc(db, "threads", id));
    } catch (e) {
      console.error("Error deleting thread: ", e);
    }
  };

  /* ================= CLEAR HISTORY ================= */
  const clearHistory = async () => {
    if (!user) return;
    try {
      // In a real production app, deleting all documents in a collection from the client is discouraged.
      // Usually this is done via a backend function. But for pilot, we loop through and delete.
      for (const thread of threads) {
        await deleteDoc(doc(db, "threads", thread.id));
      }
    } catch (e) {
      console.error("Error clearing history: ", e);
    }
  };

  return (
    <PromptHistoryContext.Provider
      value={{
        threads,
        createThread,
        addMessageToThread,
        addAIResponseToThread,
        togglePin,
        renameThread,
        deleteThread,
        clearHistory,
        getThreadById: (id) => threads.find((t) => String(t.id) === String(id)),
      }}
    >
      {children}
    </PromptHistoryContext.Provider>
  );
}

export const usePromptHistory = () => useContext(PromptHistoryContext);