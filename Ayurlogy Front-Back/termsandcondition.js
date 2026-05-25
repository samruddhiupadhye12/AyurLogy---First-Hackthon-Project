
function showTerms() {
    document.getElementById("termsBox").style.display = "block";
}

function goToContinue() {
    const agree = document.getElementById("agree").checked;
    if (!agree) {
        toastWarning("Please agree to Terms & Conditions");
        return;
    }

    const username = (document.getElementById("username") && document.getElementById("username").value) || "";
    const password = (document.getElementById("password") && document.getElementById("password").value) || "";
    if (!username || !password) {
        toastWarning("Please enter username and password");
        return;
    }

    const btn = document.querySelector(".accept-btn");
    if (btn) { btn.disabled = true; btn.textContent = "Signing in..."; }

    fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ username: username.trim(), password: password })
    })
        .then(function (res) { return res.json().then(function (data) { return { ok: res.ok, data: data }; }); })
        .then(function (result) {
            if (result.ok) {
                toastSuccess("Login successful!");
                setTimeout(() => {
                    window.location.href = "continue.html";
                }, 1000);
            } else {
                toastError(result.data.error || "Login failed");
                if (btn) { btn.disabled = false; btn.textContent = "Continue"; }
            }
        })
        .catch(function (err) {
            toastError("Network error. Please try again.");
            if (btn) { btn.disabled = false; btn.textContent = "Continue"; }
        });
}

// Disable Ctrl + Mouse Wheel Zoom
document.addEventListener("wheel", function(e) {
    if (e.ctrlKey) {
        e.preventDefault();
    }
}, { passive: false });

// Disable Ctrl + + and Ctrl + -
document.addEventListener("keydown", function(e) {
    if (e.ctrlKey && (e.key === "+" || e.key === "-" || e.key === "=")) {
        e.preventDefault();
    }
});