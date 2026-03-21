(function () {
  "use strict";

  if (localStorage.getItem("access_token")) {
    window.location.href = "/app";
    return;
  }

  const tabs = document.querySelectorAll(".auth-tab");
  const formSignin = document.getElementById("form-signin");
  const formSignup = document.getElementById("form-signup");
  const errorBox = document.getElementById("auth-error");

  // ── Tab switching ────────────────────────────────────────────
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      hideError();

      if (tab.dataset.tab === "signup") {
        formSignin.classList.add("hidden");
        formSignup.classList.remove("hidden");
      } else {
        formSignup.classList.add("hidden");
        formSignin.classList.remove("hidden");
      }
    });
  });

  // ── Helpers ──────────────────────────────────────────────────
  function showError(msg) {
    errorBox.textContent = msg;
    errorBox.classList.add("visible");
  }

  function hideError() {
    errorBox.textContent = "";
    errorBox.classList.remove("visible");
  }

  function setLoading(btn, loading) {
    const label = btn.querySelector(".btn-label");
    if (loading) {
      btn.disabled = true;
      label.dataset.original = label.textContent;
      label.innerHTML = '<span class="spinner"></span>';
    } else {
      btn.disabled = false;
      label.textContent = label.dataset.original || label.textContent;
    }
  }

  // ── Sign In ──────────────────────────────────────────────────
  formSignin.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideError();

    const email = document.getElementById("signin-email").value.trim();
    const password = document.getElementById("signin-password").value;
    const btn = document.getElementById("btn-signin");

    if (!email || !password) {
      showError("Please fill in all fields.");
      return;
    }

    setLoading(btn, true);

    try {
      const res = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Login failed.");
      }

      localStorage.setItem("access_token", data.access_token);
      if (data.refresh_token) {
        localStorage.setItem("refresh_token", data.refresh_token);
      }
      localStorage.setItem("user_id", data.user_id);

      window.location.href = "/app";
    } catch (err) {
      showError(err.message);
    } finally {
      setLoading(btn, false);
    }
  });

  // ── Sign Up ──────────────────────────────────────────────────
  formSignup.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideError();

    const email = document.getElementById("signup-email").value.trim();
    const password = document.getElementById("signup-password").value;
    const btn = document.getElementById("btn-signup");

    if (!email || !password) {
      showError("Please fill in all fields.");
      return;
    }

    if (password.length < 6) {
      showError("Password must be at least 6 characters.");
      return;
    }

    setLoading(btn, true);

    try {
      const res = await fetch("/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Signup failed.");
      }

      if (data.access_token) {
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("user_id", data.user_id);
        window.location.href = "/app";
      } else {
        // Email confirmation required
        tabs[0].click();
        showError(
          "Account created! Check your email to confirm, then sign in."
        );
        errorBox.style.borderColor = "rgba(34,197,94,0.3)";
        errorBox.style.background = "rgba(34,197,94,0.08)";
        errorBox.style.color = "#86efac";
      }
    } catch (err) {
      showError(err.message);
    } finally {
      setLoading(btn, false);
    }
  });
})();
