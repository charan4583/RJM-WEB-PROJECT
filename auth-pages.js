(function () {
  "use strict";

  var otpEmail = "";
  var verifiedOtp = "";
  var otpTimer = null;

  function pageName() {
    return document.body.getAttribute("data-auth-page") || "";
  }

  async function fetchJson(url, options) {
    var response = await fetch(url, options);
    var data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Request failed.");
    }
    return data;
  }

  function message(id, text, isSuccess) {
    var el = document.getElementById(id);
    if (!el) {
      return;
    }
    el.textContent = text;
    el.style.color = isSuccess ? "var(--accent)" : "var(--accent-3)";
  }

  function clearForm(form) {
    if (form) {
      form.reset();
    }
  }

  function initLogin() {
    var form = document.getElementById("loginForm");
    var tryAgain = document.getElementById("tryAgainBtn");
    var forgot = document.getElementById("forgotBtn");
    var signup = document.getElementById("showSignupBtn");
    if (!form) {
      return;
    }
    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      var email = document.getElementById("loginEmail").value.trim();
      var password = document.getElementById("loginPassword").value;
      clearForm(form);
      tryAgain.hidden = true;
      try {
        var data = await fetchJson("/api/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: email, password: password })
        });
        localStorage.setItem("skillbridge-token", data.token);
        localStorage.setItem("skillbridge-email", data.email);
        message("loginMessage", "Login successful. Opening main website page...", true);
        window.setTimeout(function () {
          window.location.href = "index.html";
        }, 650);
      } catch (error) {
        message("loginMessage", error.message, false);
        tryAgain.hidden = false;
      }
    });
    tryAgain.addEventListener("click", function () {
      message("loginMessage", "", true);
      tryAgain.hidden = true;
      clearForm(form);
      document.getElementById("loginEmail").focus();
    });
    forgot.addEventListener("click", function () {
      clearForm(form);
      window.location.href = "forgot-password.html";
    });
    signup.addEventListener("click", function () {
      clearForm(form);
      window.location.href = "signup.html";
    });
  }

  function initSignup() {
    var form = document.getElementById("signupForm");
    var back = document.getElementById("backToLoginFromSignup");
    if (!form) {
      return;
    }
    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      var email = document.getElementById("signupEmail").value.trim();
      var password = document.getElementById("signupPassword").value;
      var confirmPassword = document.getElementById("signupConfirm").value;
      clearForm(form);
      try {
        await fetchJson("/api/signup", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: email, password: password, confirmPassword: confirmPassword })
        });
        message("signupMessage", "Your account was created successfully. Opening login page...", true);
        window.setTimeout(function () {
          window.location.href = "login.html";
        }, 800);
      } catch (error) {
        message("signupMessage", error.message, false);
      }
    });
    back.addEventListener("click", function () {
      clearForm(form);
      window.location.href = "login.html";
    });
  }

  function startOtpCountdown(seconds) {
    var remaining = seconds;
    var resend = document.getElementById("resendOtpBtn");
    resend.disabled = true;
    window.clearInterval(otpTimer);
    otpTimer = window.setInterval(function () {
      remaining -= 1;
      if (remaining <= 0) {
        window.clearInterval(otpTimer);
        resend.disabled = false;
        message("otpMessage", "OTP expired or not received. Click Resend OTP.", false);
      }
    }, 1000);
  }

  function setForgotControls(otpEnabled, passwordEnabled) {
    var otpInput = document.getElementById("otpInput");
    var verify = document.getElementById("verifyOtpBtn");
    var password = document.getElementById("newPassword");
    var confirm = document.getElementById("confirmNewPassword");
    var update = document.getElementById("updatePasswordBtn");
    if (otpInput) {
      otpInput.disabled = !otpEnabled;
    }
    if (verify) {
      verify.disabled = !otpEnabled;
    }
    if (password) {
      password.disabled = !passwordEnabled;
    }
    if (confirm) {
      confirm.disabled = !passwordEnabled;
    }
    if (update) {
      update.disabled = !passwordEnabled;
    }
  }

  async function sendOtp() {
    var emailInput = document.getElementById("forgotEmail");
    var typedEmail = emailInput.value.trim();
    if (typedEmail) {
      otpEmail = typedEmail;
    }
    emailInput.value = "";
    verifiedOtp = "";
    setForgotControls(false, false);
    if (!otpEmail) {
      message("otpMessage", "Enter your Gmail username before sending OTP.", false);
      return;
    }
    try {
      var data = await fetchJson("/api/password/otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: otpEmail })
      });
      message("otpMessage", data.message + " Complete verification within 60 seconds.", true);
      document.getElementById("otpInput").value = "";
      setForgotControls(true, false);
      startOtpCountdown(data.expiresIn || 60);
    } catch (error) {
      message("otpMessage", error.message, false);
      document.getElementById("resendOtpBtn").disabled = false;
    }
  }

  async function verifyOtp() {
    var otpInput = document.getElementById("otpInput");
    var otp = otpInput.value.trim();
    otpInput.value = "";
    if (!otpEmail || !otp) {
      message("forgotMessage", "Enter the OTP from your email first.", false);
      return;
    }
    try {
      var data = await fetchJson("/api/password/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: otpEmail, otp: otp })
      });
      verifiedOtp = otp;
      setForgotControls(false, true);
      message("forgotMessage", data.message, true);
    } catch (error) {
      verifiedOtp = "";
      setForgotControls(true, false);
      message("forgotMessage", error.message, false);
    }
  }

  function initForgotPassword() {
    var form = document.getElementById("forgotForm");
    var send = document.getElementById("sendOtpBtn");
    var resend = document.getElementById("resendOtpBtn");
    var verify = document.getElementById("verifyOtpBtn");
    var back = document.getElementById("backToLoginFromForgot");
    if (!form) {
      return;
    }
    setForgotControls(false, false);
    send.addEventListener("click", sendOtp);
    resend.addEventListener("click", sendOtp);
    verify.addEventListener("click", verifyOtp);
    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      var password = document.getElementById("newPassword").value;
      var confirmPassword = document.getElementById("confirmNewPassword").value;
      document.getElementById("newPassword").value = "";
      document.getElementById("confirmNewPassword").value = "";
      if (!verifiedOtp) {
        message("forgotMessage", "Verify OTP before updating your password.", false);
        return;
      }
      try {
        var data = await fetchJson("/api/password/update", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: otpEmail, otp: verifiedOtp, password: password, confirmPassword: confirmPassword })
        });
        window.clearInterval(otpTimer);
        verifiedOtp = "";
        setForgotControls(false, false);
        message("forgotMessage", data.message + " Opening login page...", true);
        window.setTimeout(function () {
          window.location.href = "login.html";
        }, 900);
      } catch (error) {
        message("forgotMessage", error.message, false);
      }
    });
    back.addEventListener("click", function () {
      clearForm(form);
      setForgotControls(false, false);
      window.location.href = "login.html";
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (pageName() === "login") {
      initLogin();
    } else if (pageName() === "signup") {
      initSignup();
    } else if (pageName() === "forgot") {
      initForgotPassword();
    }
  });
}());
