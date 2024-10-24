const togglePassword = document.getElementById("togglePassword");
const passwordInput = document.getElementById("password");
const eyeIcon = document.getElementById("eyeIcon");

togglePassword.addEventListener("click", function() {
    const type = passwordInput.getAttribute("type") === "password" ? "text" : "password";
    passwordInput.setAttribute("type", type)
    
    eyeIcon.src = type === "password" ? "static/eye-closed.png" : "static/eye-open.png";
});

const toggleConfirmation = document.getElementById("toggleConfirmation");
const confirmationInput = document.getElementById("confirmation");
const eyeIconConfirmation = document.getElementById("eyeIconConfirmation");

toggleConfirmation.addEventListener("click", function() {
    const type = confirmationInput.getAttribute("type") === "password" ? "text" : "password";
    confirmationInput.setAttribute("type", type);
    eyeIconConfirmation.src = type === "password" ? "static/eye-closed.png" : "static/eye-open.png"

});