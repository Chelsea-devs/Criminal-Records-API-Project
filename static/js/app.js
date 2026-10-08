const toggle = document.querySelector(".menu-toggle");
const nav = document.querySelector(".nav");
if (toggle && nav) toggle.addEventListener("click", () => nav.classList.toggle("open"));
setTimeout(() => document.querySelectorAll(".message").forEach(el => el.classList.add("fade")), 5000);
