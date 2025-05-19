import { auth } from "./firebase.js";
import { onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("add-form");

  onAuthStateChanged(auth, (user) => {
    if (user) {
      loadPortfolio();

      // Automatyczne odświeżanie co 10s
      setInterval(() => {
        if (auth.currentUser) loadPortfolio();
      }, 10000);

      // Obsługa formularza dodawania
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const symbol = document.getElementById("crypto").value.toUpperCase();
        const amount = parseFloat(document.getElementById("amount").value);

        try {
          const token = await user.getIdToken();
          const res = await fetch("/api/add", {
            method: "POST",
            headers: {
              "Authorization": "Bearer " + token,
              "Content-Type": "application/json"
            },
            body: JSON.stringify({ crypto: symbol, amount })
          });

          if (!res.ok) throw new Error("Błąd dodawania");

          await loadPortfolio();
          form.reset();
        } catch (err) {
          alert("Błąd: " + err.message);
        }
      });
    }
  });
});

async function loadPortfolio() {
  try {
    const user = auth.currentUser;
    if (!user) return;

    const token = await user.getIdToken();
    const res = await fetch("/api/portfolio", {
      headers: { "Authorization": "Bearer " + token }
    });

    if (!res.ok) throw new Error("Błąd pobierania danych portfela");

    const data = await res.json();
    const table = document.querySelector("#portfolio-table tbody");
    table.innerHTML = "";

    data.assets.forEach(asset => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${asset.crypto_name}</td>
        <td>${asset.amount}</td>
        <td>${asset.price.toFixed(2)}</td>
        <td>${asset.value.toFixed(2)}</td>
        <td>
          <form class="delete-form" data-symbol="${asset.crypto_name}">
            <input type="number" name="amount" min="0.00000001" max="${asset.amount}" step="any" required>
            <button type="submit">Usuń</button>
          </form>
        </td>
      `;
      table.appendChild(row);
    });

    document.getElementById("total-value").textContent = `${data.total_value.toFixed(2)} USD`;

    // Obsługa formularzy usuwania
    document.querySelectorAll(".delete-form").forEach(form => {
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const symbol = form.dataset.symbol;
        const amount = parseFloat(form.amount.value);
        const confirmed = confirm(`Usunąć ${amount} ${symbol}?`);
        if (!confirmed) return;

        const delRes = await fetch(`/api/delete/${symbol}`, {
          method: "DELETE",
          headers: {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ amount })
        });

        if (delRes.ok) {
          loadPortfolio();
        } else {
          alert("Błąd usuwania.");
        }
      });
    });

  } catch (err) {
    console.error("Błąd ładowania portfela:", err);
  }
}
