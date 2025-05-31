import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import {
  getAuth,
  onAuthStateChanged
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
import { firebaseConfig } from "./firebase-config.js";

// Inicjalizacja Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// Po zalogowaniu użytkownika
onAuthStateChanged(auth, async user => {
  if (!user) {
    window.location.href = "/login";
    return;
  }

  const token = await user.getIdToken();

  // Obsługa formularza
  const form = document.getElementById("alert-form");
  form.addEventListener("submit", async e => {
    e.preventDefault();
    const symbol = document.getElementById("crypto").value.toUpperCase();
    const threshold = parseFloat(document.getElementById("threshold").value);

    try {
      const res = await fetch("/api/alerts", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer " + token
        },
        body: JSON.stringify({ symbol, threshold })
      });

      if (res.ok) {
        document.getElementById("status").textContent = "✅ Alert dodany!";
        form.reset();
        loadAlerts(token);
      } else {
        throw new Error("Błąd dodawania alertu");
      }
    } catch (err) {
      console.error("❌ Błąd dodawania alertu:", err);
      document.getElementById("status").textContent = "❌ Błąd serwera.";
    }
  });

  // Wczytaj istniejące alerty
  loadAlerts(token);
});

async function loadAlerts(token) {
  const tbody = document.querySelector("tbody");
  tbody.innerHTML = "";
  try {
    const res = await fetch("/api/alerts", {
      headers: {
        Authorization: "Bearer " + token
      }
    });

    const text = await res.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch (parseErr) {
      console.error("❌ Niepoprawny JSON:", parseErr);
      console.error("↩️ Treść odpowiedzi:", text);
      document.getElementById("status").textContent = "❌ Błąd parsowania danych z serwera.";
      return;
    }

    if (!data.alerts) {
      document.getElementById("status").textContent = "❌ Błąd: brak danych o alertach.";
      return;
    }

    data.alerts.forEach(alert => {
      const tr = document.createElement("tr");

      const symbol = alert.symbol || "?";
      const threshold = alert.target !== undefined ? `${alert.target.toFixed(2)} USD` : "-";
      const status = alert.sent ? "✅ Wysłano" : "⏳ Oczekuje";
      let created = "Nieznana";
      if (alert.timestamp) {
        if (typeof alert.timestamp === "string" || alert.timestamp instanceof String) {
          created = new Date(alert.timestamp).toLocaleString("pl-PL");
        } else if (alert.timestamp.seconds) {
          created = new Date(alert.timestamp.seconds * 1000).toLocaleString("pl-PL");
        }
      }

      tr.innerHTML = `
        <td>${symbol}</td>
        <td>${threshold}</td>
        <td>${status}</td>
        <td>${created}</td>
        <td><button class="delete-alert" data-id="${alert.id}">🗑️</button></td>
      `;
      tbody.appendChild(tr);

      // Obsługa usuwania alertu
      tr.querySelector(".delete-alert").addEventListener("click", async () => {
        if (!confirm("Na pewno chcesz usunąć ten alert?")) return;

        try {
          const res = await fetch(`/api/alerts/${alert.id}`, {
            method: "DELETE",
            headers: {
              Authorization: "Bearer " + token
            }
          });

          if (res.ok) {
            loadAlerts(token);
          } else {
            alert("❌ Błąd usuwania alertu");
          }
        } catch (err) {
          console.error("❌ Błąd podczas usuwania:", err);
          alert("❌ Błąd serwera");
        }
      });
    });

    document.getElementById("status").textContent = "";
  } catch (err) {
    console.error("❌ Błąd pobierania alertów:", err);
    document.getElementById("status").textContent = "❌ Błąd pobierania alertów.";
  }
}
