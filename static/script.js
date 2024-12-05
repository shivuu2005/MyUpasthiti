document.addEventListener("DOMContentLoaded", () => {
    const latitudeInput = document.getElementById("latitude");
    const longitudeInput = document.getElementById("longitude");

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                latitudeInput.value = position.coords.latitude;
                longitudeInput.value = position.coords.longitude;
            },
            (error) => {
                alert("Error retrieving location. Please enable GPS!");
            }
        );
    } else {
        alert("Geolocation is not supported by this browser.");
    }
});

window.addEventListener("scroll", function() {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 1000) {
        navbar.style.backgroundColor = '#060913';
    } else {
        navbar.style.backgroundColor = 'transparent';
    }
}, false);
