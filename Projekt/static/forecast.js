import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import { getAuth, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";

// Konfiguracja Firebase (TAKIE SAME DANE jak w innych plikach!)
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
    const res = await fetch("/api/forecast", {
      headers: {
        Authorization: "Bearer " + token
      }
    });

    if (!res.ok) {
      throw new Error("Błąd pobierania danych");
    }

    const data = await res.json();
    const tbody = document.querySelector("tbody");
    tbody.innerHTML = "";

    data.forecast.forEach(row => {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${row.days}</td><td>${row.value.toFixed(2)} USD</td>`;
      tbody.appendChild(tr);
    });

    document.getElementById("loading").style.display = "none";

  } catch (err) {
    console.error("Błąd:", err);
    document.getElementById("loading").textContent = "❌ Nie udało się pobrać danych.";
  }
});
