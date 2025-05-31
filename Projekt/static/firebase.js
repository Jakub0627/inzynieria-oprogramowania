// firebase.js

import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import {
  getAuth,
  onAuthStateChanged,
  signInWithPopup,
  GoogleAuthProvider,
  signOut
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";

import {
  getFirestore,
  doc,
  setDoc,
  getDoc
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";
import { firebaseConfig } from "./firebase-config.js";

// 🔧 Inicjalizacja Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

// 🔗 Elementy UI
const loginLink = document.getElementById("login-link");
const logoutButton = document.getElementById("logout-button");
const userInfo = document.getElementById("user-info");
const nav = document.querySelector("nav");

// 🔐 Obsługa stanu logowania
onAuthStateChanged(auth, async user => {
  if (user) {
    // 👤 Zapis użytkownika do Firestore
    const uid = user.uid;
    const userDocRef = doc(db, "users", uid);
    const docSnap = await getDoc(userDocRef);

    if (!docSnap.exists()) {
      await setDoc(userDocRef, {
        email: user.email,
        createdAt: new Date()
      });
    }

    // UI
    if (loginLink) loginLink.style.display = "none";
    if (logoutButton) logoutButton.style.display = "inline";
    if (userInfo) userInfo.textContent = `👤 Zalogowany jako: ${user.email}`;
  } else {
    // Niezalogowany
    if (nav) nav.style.display = "block";
    if (loginLink) loginLink.style.display = "inline";
    if (logoutButton) logoutButton.style.display = "none";
    if (userInfo) userInfo.textContent = "";

    if (window.location.pathname !== "/login") {
      window.location.href = "/login";
    }
  }
});

// 🔄 Odświeżanie portfela co 10 sekund
setInterval(() => {
  if (auth.currentUser && typeof loadPortfolio === "function") {
    loadPortfolio();
  }
}, 10000);

// 🔑 Logowanie
function login() {
  const provider = new GoogleAuthProvider();
  signInWithPopup(auth, provider)
    .then(() => {
      window.location.href = "/";
    })
    .catch(error => {
      console.error("Błąd logowania:", error);
      alert("Logowanie nie powiodło się.");
    });
}

// 🚪 Wylogowanie
function logout() {
  signOut(auth).then(() => {
    window.location.href = "/login";
  });
}

// 🌍 Globalne funkcje
window.login = login;
window.logout = logout;

// 📤 Eksport
export { auth };
