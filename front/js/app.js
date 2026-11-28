/* =========================================================
   app.js - the ONLY JavaScript file in this project.
   It has just 3 small functions.
   ========================================================= */


/* ---------------------------------------------------------
   1. callBackend(api, message)
   Every button that needs data from the server calls this.
   For now it only shows a pop-up saying which backend API
   will be called. The Python team will later replace the
   inside of this function with a real fetch() call.

   Example (in HTML):
   <button onclick="callBackend('POST /api/faculty', 'Save new faculty')">Save</button>
   --------------------------------------------------------- */
function callBackend(api, message) {
  // find the pop-up box, or make it the first time
  var box = document.getElementById("apiPopup");
  if (box == null) {
    box = document.createElement("div");
    box.id = "apiPopup";
    box.className = "api-popup";
    document.body.appendChild(box);
  }

  // put the text inside and show it
  box.innerHTML =
    '<i class="bi bi-plug-fill text-warning me-1"></i> <b>Backend will be called here</b><br>' +
    "<code>" + api + "</code><br>" +
    '<small class="opacity-75">' + message + "</small>";
  box.classList.add("show");

  // also print it in the browser console (F12) for the backend team
  console.log("BACKEND TODO:", api, "-", message);

  // hide the pop-up after 4 seconds
  setTimeout(function () {
    box.classList.remove("show");
  }, 4000);
}


/* ---------------------------------------------------------
   2. login()
   Used only on index.html.
   Users are hard-coded for now:
     Admin   : admin / admin123
     Faculty : priya@college.edu / faculty123
   BACKEND: replace the if-checks with  POST /api/login
   --------------------------------------------------------- */
function login() {
  var username = document.getElementById("username").value;
  var password = document.getElementById("password").value;
  var isAdmin = document.getElementById("roleAdmin").checked;

  console.log("BACKEND TODO: POST /api/login", username);

  if (isAdmin && username == "admin" && password == "admin123") {
    window.location.href = "admin-dashboard.html";
  } else if (!isAdmin && username == "priya@college.edu" && password == "faculty123") {
    window.location.href = "faculty-dashboard.html";
  } else {
    document.getElementById("loginError").classList.remove("d-none");
  }
  return false; // stops the form from reloading the page
}


/* ---------------------------------------------------------
   3. toggleMenu()
   On mobile the sidebar is hidden. The menu button (☰)
   calls this to show / hide it.
   --------------------------------------------------------- */
function toggleMenu() {
  document.getElementById("sidebar").classList.toggle("show");
}
