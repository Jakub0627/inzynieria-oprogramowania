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
  try {
    const res = await fetch("/api/optimize", {
      method: "POST",
      headers: {
        Authorization: "Bearer " + token
      }
    });

    const data = await res.json();
    const div = document.createElement("div");
    data.suggestions.forEach(suggestion => {
      const p = document.createElement("p");
      p.textContent = suggestion;
      div.appendChild(p);
    });

    document.body.appendChild(div);
  } catch (err) {
    console.error("Błąd optymalizacji:", err);
  }
});
