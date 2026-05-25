// layout.js
document.addEventListener("DOMContentLoaded", function () {
  // Load header
  fetch("header.html")
    .then(response => response.text())
    .then(data => {
      document.getElementById("header").innerHTML = data;
      // Netflix-style: if coming from landing, logo was hidden - animate it "landing"
      if (sessionStorage.getItem("fromLanding") === "true") {
        sessionStorage.removeItem("fromLanding");
        const logoEl = document.querySelector(".header .logo");
        if (logoEl) {
          logoEl.classList.add("logo-just-landed");
        }
      }
    });

  // Load footer
  fetch("footer.html")
    .then(response => response.text())
    .then(data => {
      document.getElementById("footer").innerHTML = data;
    });
});
