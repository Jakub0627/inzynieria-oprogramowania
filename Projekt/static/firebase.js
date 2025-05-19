// Firebase SDK - CDN wersja ES module
import {
  initializeApp
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";

import {
  getAuth,
  onAuthStateChanged,
  signInWithPopup,
  GoogleAuthProvider,
  signOut
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";

// Konfiguracja Firebase
const firebaseConfig = {
  apiKey: "AIzaSyD6UCP3A76kHjwjI4KDSVriDTDP89agIzg",
  authDomain: "projekt-krypto-8c5d7.firebaseapp.com",
  projectId: "projekt-krypto-8c5d7",
  storageBucket: "projekt-krypto-8c5d7.appspot.com",
  messagingSenderId: "17200369495",
  appId: "1:17200369495:web:ef2106700b06a9a026f812"
};

// Inicjalizacja
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// Elementy
const loginLink = document.getElementById("login-link");
const logoutButton = document.getElementById("logout-button");
const userInfo = document.getElementById("user-info");

onAuthStateChanged(auth, user => {
  const nav = document.querySelector("nav");

  if (!user) {
    if (nav) nav.style.display = "block";
    if (loginLink) loginLink.style.display = "inline";
    if (logoutButton) logoutButton.style.display = "none";
    if (userInfo) userInfo.textContent = "";

    if (window.location.pathname !== "/login") {
      window.location.href = "/login";
    }
  } else {
    if (loginLink) loginLink.style.display = "none";
    if (logoutButton) logoutButton.style.display = "inline";
    if (userInfo) userInfo.textContent = `👤 Zalogowany jako: ${user.email}`;
  }

  // 🛡️ Bezpieczne odświeżanie portfela co 10 sekund
  setInterval(() => {
    if (auth.currentUser && typeof loadPortfolio === "function") {
      loadPortfolio();
    }
  }, 10000);
});

// Logowanie
function login() {
  const provider = new GoogleAuthProvider();
  signInWithPopup(auth, provider)
    .then(result => {
      window.location.href = "/";
    })
    .catch(error => {
      console.error("Błąd logowania:", error);
      alert("Logowanie nie powiodło się.");
    });
}

// Wylogowanie
function logout() {
  signOut(auth).then(() => {
    window.location.href = "/login";
  });
}

window.login = login;
window.logout = logout;

// 📤 Eksport dla dashboard.js
export { auth };
