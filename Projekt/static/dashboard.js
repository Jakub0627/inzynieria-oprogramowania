import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import { getAuth, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
import { firebaseConfig } from "./firebase-config.js";

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// Fade-in efekt dla wierszy
function fadeInRow(row) {
  row.classList.add("opacity-0", "transition-opacity", "duration-500");
  requestAnimationFrame(() => {
    row.classList.remove("opacity-0");
  });
}

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

    if (!crypto || isNaN(amount)) return alert("❌ Nieprawidłowe dane!");

    try {
      const res = await fetch("/api/add", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer " + token
        },
        body: JSON.stringify({ crypto, amount })
      });

      if (res.ok) {
        document.getElementById("add-form").reset();
        loadPortfolio();
      } else {
        alert("❌ Błąd dodawania kryptowaluty.");
      }
    } catch (err) {
      console.error("❌ Błąd żądania:", err);
      alert("❌ Błąd sieci.");
    }
  });

  window.loadPortfolio = async function () {
    try {
      const res = await fetch("/api/portfolio", {
        headers: { Authorization: "Bearer " + token }
      });

      const data = await res.json();
      const tbody = document.querySelector("#portfolio-table tbody");
      tbody.innerHTML = "";

      data.assets.forEach(asset => {
        const row = document.createElement("tr");
        fadeInRow(row);

        row.innerHTML = `
          <td class="px-4 py-2">${asset.crypto_name}</td>
          <td class="px-4 py-2">${asset.amount}</td>
          <td class="px-4 py-2">${asset.price.toFixed(2)} USD</td>
          <td class="px-4 py-2">${asset.value.toFixed(2)} USD</td>
          <td class="px-4 py-2 flex gap-2">
            <input type="number" min="0" step="any" placeholder="Ilość"
                   class="delete-amount bg-gray-800 border border-gray-600 rounded px-2 py-1 text-white w-24 text-sm">
            <button data-symbol="${asset.crypto_name}"
                    class="delete-btn bg-red-600 hover:bg-red-700 text-white px-2 py-1 rounded text-xs shadow transition">
              🗑️
            </button>
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

          if (isNaN(amount) || amount <= 0) {
            alert("❌ Podaj poprawną ilość.");
            return;
          }

          try {
            const res = await fetch(`/api/delete/${symbol}`, {
              method: "DELETE",
              headers: {
                "Content-Type": "application/json",
                Authorization: "Bearer " + token
              },
              body: JSON.stringify({ amount })
            });

            if (res.ok) {
              loadPortfolio();
            } else {
              alert("❌ Błąd usuwania kryptowaluty.");
            }
          } catch (err) {
            console.error("❌ Błąd żądania:", err);
            alert("❌ Błąd sieci.");
          }
        });
      });
    } catch (err) {
      console.error("❌ Błąd pobierania portfela:", err);
    }
  };

  loadPortfolio();
});
