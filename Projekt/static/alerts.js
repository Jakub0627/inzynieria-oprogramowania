import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import { getAuth, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
import { firebaseConfig } from "./firebase-config.js";

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

onAuthStateChanged(auth, async user => {
  if (!user) {
    window.location.href = "/login";
    return;
  }

  const token = await user.getIdToken();

  // Przykład działania: fetch alertów z API (stworzyć odpowiednie endpointy)
  try {
    const res = await fetch("/api/alerts", {
      headers: {
        Authorization: "Bearer " + token
      }
    });

    const data = await res.json();
    const container = document.createElement("div");
    data.alerts.forEach(alert => {
      const p = document.createElement("p");
      p.textContent = alert.message;
      container.appendChild(p);
    });

    document.body.appendChild(container);
  } catch (err) {
    console.error("Błąd ładowania alertów:", err);
  }
});
