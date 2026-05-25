function hideAll() {
  document.getElementById("choiceScreen").classList.add("hidden");
  document.getElementById("signupScreen").classList.add("hidden");
  document.getElementById("emailSignupScreen").classList.add("hidden");
  document.getElementById("loginScreen").classList.add("hidden");
}

// On load: if URL has #signup or #login, go directly to that screen
(function initFromHash() {
  var hash = (window.location.hash || "").toLowerCase();
  if (hash === "#signup" || hash === "#create") {
    showSignup();
  } else if (hash === "#login") {
    showLogin();
  }
})();

function showSignup() {
  hideAll();
  document.getElementById("signupScreen").classList.remove("hidden");
}

function showLogin() {
  hideAll();
  document.getElementById("loginScreen").classList.remove("hidden");
}

function showEmailSignup() {
  hideAll();
  document.getElementById("emailSignupScreen").classList.remove("hidden");
}

// Prefer same-origin /api when served by Flask; fall back to localhost:5000 for file:// or other dev servers
let API_BASE = "/api";
try {
  const loc = window.location;
  if (loc.protocol === "file:") {
    // Opened directly as a file – talk to Flask on 127.0.0.1:5000
    API_BASE = "http://127.0.0.1:5000/api";
  } else if (loc.port && loc.port !== "5000") {
    // Frontend served on another port (e.g. Live Server) – still use Flask on :5000
    API_BASE = `${loc.protocol}//${loc.hostname}:5000/api`;
  }
} catch (e) {
  API_BASE = "http://127.0.0.1:5000/api";
}

// ========== Regex rules (SAME as backend) ==========
// Username: starts with letter, 4–20 chars, letters/numbers/underscore only
const REGEX_USERNAME = /^[a-zA-Z][a-zA-Z0-9_]{3,19}$/;
// Email: standard email format
const REGEX_EMAIL = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
// Password: min 8 chars; validated by rules below (uppercase, lowercase, number, special)
const PASSWORD_MIN_LENGTH = 8;

function validateUsername(username) {
  if (!username || username.length < 4) {
    return "Username must be 4–20 characters and start with a letter (letters, numbers, underscore only).";
  }
  if (!REGEX_USERNAME.test(username)) {
    return "Username must start with a letter, 4–20 characters, only letters, numbers and underscore.";
  }
  return null;
}

function validateEmail(email) {
  if (!email) return "Email is required.";
  if (!REGEX_EMAIL.test(email)) return "Please enter a valid email address.";
  return null;
}

function validatePassword(password) {
  if (!password) return "Password is required.";
  if (password.length < PASSWORD_MIN_LENGTH) {
    return "Password must be at least 8 characters.";
  }
  if (!/[A-Z]/.test(password)) return "Password must contain at least one uppercase letter.";
  if (!/[a-z]/.test(password)) return "Password must contain at least one lowercase letter.";
  if (!/\d/.test(password)) return "Password must contain at least one number.";
  if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
    return "Password must contain at least one special character (e.g. !@#$%^&*).";
  }
  return null;
}

async function createAccount() {
  const username = document.getElementById("username").value.trim();
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value.trim();

  if (!username || !email || !password) {
    toastWarning("All fields are required");
    return;
  }

  var err = validateUsername(username);
  if (err) { toastWarning(err); return; }
  err = validateEmail(email);
  if (err) { toastWarning(err); return; }
  err = validatePassword(password);
  if (err) { toastWarning(err); return; }

  try {
    const res = await fetch(`${API_BASE}/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password }),
    });

    const data = await res.json();

    if (res.ok && data.ok) {
      toastSuccess("Account created successfully 🎉");
      showLogin();
    } else {
      toastError(data.error || "Signup failed");
    }
  } catch (err) {
    console.error(err);
    toastError("Could not reach the server. Make sure app.py is running.");
  }
}

// Show the Terms & Conditions box before final account creation
function showTermsBox() {
  const box = document.getElementById("termsBox");
  if (box) {
    box.classList.remove("hidden");
  }
}

// User confirms Terms & Conditions, then actually creates the account
async function confirmSignup() {
  const agree = document.getElementById("agree");
  if (!agree || !agree.checked) {
    toastWarning("Please agree to the Terms & Conditions before creating your account.");
    return;
  }
  // Call the actual signup logic
  await createAccount();
}


/* LOGIN */
async function loginUser() {
  const username = document.getElementById("loginUsername").value.trim();
  const password = document.getElementById("loginPassword").value.trim();

  if (!username || !password) {
    toastWarning("Username & password required");
    return;
  }

  var loginErr = validateUsername(username);
  if (loginErr) { toastWarning(loginErr); return; }

  const res = await fetch(`${API_BASE}/login`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  credentials: "include",
  body: JSON.stringify({ username, password })
});


  const data = await res.json();

  if (data.ok) {
    toastSuccess("Login successful ✅");
    var nextUrl = "/chat";
    try {
      var params = new URLSearchParams(window.location.search);
      if (params.get("next") && params.get("next").startsWith("/")) {
        nextUrl = params.get("next");
      }
    } catch (e) {}
    setTimeout(function () {
      window.location.href = nextUrl;
    }, 1000);
  } else {
    toastError(data.error || "Invalid login");
  }
}
