import React, { useState, useEffect } from 'react';
import { Key, Copy, Check, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { db } from '../firebase';
import { collection, query, where, getDocs, addDoc, serverTimestamp } from 'firebase/firestore';

export function ApiKeyManager() {
  const { user } = useAuth();
  const [apiKey, setApiKey] = useState(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    async function fetchApiKey() {
      if (!user) return;
      
      // Set a 3-second timeout in case Firestore hangs on initial connection
      const timeoutId = setTimeout(() => {
        if (isMounted && loading) {
          console.warn("Firestore connection timeout. Falling back to generate button.");
          setLoading(false);
        }
      }, 3000);

      try {
        const q = query(collection(db, 'api_keys'), where('userId', '==', user.uid));
        const querySnapshot = await getDocs(q);
        if (isMounted && !querySnapshot.empty) {
          setApiKey(querySnapshot.docs[0].data().key);
        }
      } catch (err) {
        console.error("Error fetching API key:", err);
        if (isMounted) setError("Failed to load API key. Ensure Firestore is properly configured.");
      } finally {
        clearTimeout(timeoutId);
        if (isMounted) setLoading(false);
      }
    }
    fetchApiKey();
    return () => { isMounted = false; };
  }, [user]);

  const generateKey = async () => {
    if (!user) return;
    setLoading(true);
    setError(null);
    
    try {
      // Generate a random token
      const randomString = Array.from(crypto.getRandomValues(new Uint8Array(24)))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
      const newKey = `gx_live_${randomString}`;

      // Optimistically update the UI instantly
      setApiKey(newKey);
      setLoading(false);

      // Save to Firestore in the background
      await addDoc(collection(db, 'api_keys'), {
        userId: user.uid,
        key: newKey,
        createdAt: serverTimestamp()
      });

    } catch (err) {
      console.error("Error generating API key:", err);
      setError("Failed to save API key to cloud. It may only exist locally for now.");
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(apiKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!user) return null;

  return (
    <div className="bg-[#12141c] border border-gray-800 rounded-lg p-6 mb-8 mt-8">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-8 h-8 rounded-full bg-emerald-500/10 flex items-center justify-center">
          <Key className="w-4 h-4 text-emerald-400" />
        </div>
        <div>
          <h2 className="text-lg font-medium text-gray-100">API Access</h2>
          <p className="text-sm text-gray-400">Generate a secret key to authenticate your programmatic requests to the Galarix API.</p>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 flex items-start gap-2 text-red-400 text-sm">
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {loading ? (
        <div className="animate-pulse flex gap-2 items-center">
          <div className="h-10 bg-gray-800 rounded w-full max-w-md"></div>
        </div>
      ) : apiKey ? (
        <div className="space-y-3">
          <div className="flex items-center gap-2 max-w-xl">
            <div className="flex-1 bg-gray-900 border border-gray-700 rounded-md px-3 py-2 font-mono text-sm text-gray-300 break-all">
              {apiKey}
            </div>
            <button
              onClick={copyToClipboard}
              className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded-md transition-colors border border-gray-700"
            >
              {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
              {copied ? 'Copied' : 'Copy'}
            </button>
          </div>
          <p className="text-xs text-amber-500/80 max-w-xl">
            Keep this key secret. Do not expose it in client-side code or public repositories.
          </p>
        </div>
      ) : (
        <button
          onClick={generateKey}
          className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-md text-sm font-medium transition-colors"
        >
          Generate Secret Key
        </button>
      )}
    </div>
  );
}
