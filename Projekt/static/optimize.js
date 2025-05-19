import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import { getAuth, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";

// Konfiguracja Firebase
const firebaseConfig = {
  apiKey: "AIzaSyD6UCP3A76kHjwjI4KDSVriDTDP89agIzg",
  authDomain: "projekt-krypto-8c5d7.firebaseapp.com",
  projectId: "projekt-krypto-8c5d7",
  storageBucket: "projekt-krypto-8c5d7.appspot.com",
  messagingSenderId: "17200369495",
  appId: "1:17200369495:web:ef2106700b06a9a026f812"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

onAuthStateChanged(auth, async user => {
  if (!user) {
    window.location.href = "/login";
    return;
  }

  const token = await user.getIdToken();

  try {
    const res = await fetch("/api/optimize", {
      method: "POST",
      headers: {
        Authorization: "Bearer " + token
      }
    });

    if (!res.ok) throw new Error("Błąd zapytania");

    const data = await res.json();
    const ul = document.getElementById("suggestions");
    ul.innerHTML = "";

    data.suggestions.forEach(text => {
      const li = document.createElement("li");
      li.textContent = text;
      ul.appendChild(li);
    });

    document.getElementById("loading").style.display = "none";

  } catch (err) {
    console.error(err);
    document.getElementById("loading").textContent = "❌ Nie udało się pobrać danych.";
  }
});
