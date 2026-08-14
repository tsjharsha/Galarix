import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: "AIzaSyBQ7gPi0IxxW2fycdIq_cs_Pf4bC8BI6Uo",
  authDomain: "galarix-945f3.firebaseapp.com",
  projectId: "galarix-945f3",
  storageBucket: "galarix-945f3.firebasestorage.app",
  messagingSenderId: "114889769987",
  appId: "1:114889769987:web:740cf9312296b8931bfa36",
  measurementId: "G-5BB23CVPH1"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
export const db = getFirestore(app, "galarixdb");
