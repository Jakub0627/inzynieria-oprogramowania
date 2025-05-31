import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import {
  getAuth,
  onAuthStateChanged
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
import { firebaseConfig } from "./firebase-config.js";

// Inicjalizacja Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

onAuthStateChanged(auth, async user => {
  if (!user) {
    window.location.href = "/login";
    return;
  }

  const token = await user.getIdToken();

  // 📉 Wykres
  const form = document.getElementById("symbol-form");
  const chartImg = document.getElementById("chart-image");

  form.addEventListener("submit", async e => {
    e.preventDefault();
    const symbol = document.getElementById("symbol").value.trim().toUpperCase();
    if (!symbol) return;

    try {
      const res = await fetch(`/chart/${symbol}`);
      const data = await res.json();

      if (data.image_base64) {
        chartImg.src = `data:image/png;base64,${data.image_base64}`;
        chartImg.classList.remove("hidden");
      } else {
        alert("Brak danych do wykresu.");
        chartImg.classList.add("hidden");
      }
    } catch (err) {
      console.error("❌ Błąd ładowania wykresu:", err);
      chartImg.classList.add("hidden");
    }
  });

  // 📅 Prognoza
  try {
    const res = await fetch("/api/forecast", {
      headers: { Authorization: "Bearer " + token }
    });
    const data = await res.json();

    if (!data.forecast) throw new Error("Brak danych forecast");

    const forecastTable = document.getElementById("forecast-table");
    document.getElementById("forecast-loading").remove();

    data.forecast.forEach(row => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="px-4 py-2">${row.days}</td>
        <td class="px-4 py-2">${row.value.toFixed(2)} USD</td>
      `;
      forecastTable.appendChild(tr);
    });
  } catch (err) {
    console.error("Forecast error:", err);
    document.getElementById("forecast-loading").textContent = "❌ Błąd ładowania prognozy.";
  }

  // ⚙️ Optymalizacja
  try {
    const res = await fetch("/api/optimize", {
      method: "POST",
      headers: { Authorization: "Bearer " + token }
    });
    const data = await res.json();

    const list = document.getElementById("optimize-list");
    document.getElementById("optimize-loading").remove();

    if (data.suggestions && data.suggestions.length) {
      data.suggestions.forEach(text => {
        const li = document.createElement("li");
        li.textContent = text;
        list.appendChild(li);
      });
    } else {
      list.innerHTML = "<li>Brak zaleceń optymalizacyjnych.</li>";
    }
  } catch (err) {
    console.error("Optimize error:", err);
    document.getElementById("optimize-loading").textContent = "❌ Błąd ładowania rekomendacji.";
  }
});
