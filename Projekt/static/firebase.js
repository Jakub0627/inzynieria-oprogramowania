import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import {
  getAuth,
  onAuthStateChanged,
  signInWithPopup,
  GoogleAuthProvider,
  signOut
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
import { firebaseConfig } from "./firebase-config.js";

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

  // Odświeżanie portfela co 10 sekund, jeśli funkcja istnieje
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
    .then(() => {
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

export { auth };
