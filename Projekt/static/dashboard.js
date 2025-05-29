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
  document.getElementById("add-form").addEventListener("submit", async (e) => {
    e.preventDefault();

    const crypto = document.getElementById("crypto").value.trim().toUpperCase();
    const amount = parseFloat(document.getElementById("amount").value);

    if (!crypto || isNaN(amount)) return alert("Nieprawidłowe dane");

    const res = await fetch("/api/add", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer " + token
      },
      body: JSON.stringify({ crypto, amount })
    });

    if (res.ok) {
      loadPortfolio();
      document.getElementById("add-form").reset();
    } else {
      alert("Błąd dodawania kryptowaluty.");
    }
  });

  window.loadPortfolio = async function () {
    const res = await fetch("/api/portfolio", {
      headers: { Authorization: "Bearer " + token }
    });

    const data = await res.json();
    const tbody = document.querySelector("#portfolio-table tbody");
    tbody.innerHTML = "";

    data.assets.forEach(asset => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${asset.crypto_name}</td>
        <td>${asset.amount}</td>
        <td>${asset.price.toFixed(2)} USD</td>
        <td>${asset.value.toFixed(2)} USD</td>
        <td>
          <input type="number" min="0" step="any" placeholder="Ilość" class="delete-amount">
          <button data-symbol="${asset.crypto_name}" class="delete-btn">🗑️</button>
        </td>
      `;
      tbody.appendChild(row);
    });

    document.getElementById("total-value").textContent = `${data.total_value.toFixed(2)} USD`;

    document.querySelectorAll(".delete-btn").forEach(btn => {
      btn.addEventListener("click", async (e) => {
        const symbol = btn.getAttribute("data-symbol");
        const input = btn.parentElement.querySelector(".delete-amount");
        const amount = parseFloat(input.value);

        if (isNaN(amount) || amount <= 0) return alert("Podaj poprawną ilość");

        const res = await fetch(`/api/delete/${symbol}`, {
          method: "DELETE",
          headers: {
            Authorization: "Bearer " + token
          },
          body: JSON.stringify({ amount })
        });

        if (res.ok) loadPortfolio();
        else alert("Błąd usuwania kryptowaluty.");
      });
    });
  };

  loadPortfolio();
});
