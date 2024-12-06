document.addEventListener("DOMContentLoaded", () => {
    const latitudeInput = document.getElementById("latitude");
    const longitudeInput = document.getElementById("longitude");
    const countdownElement = document.getElementById("countdown");
    let countdown = 5;

    // Countdown function
    function startCountdown(callback) {
        countdownElement.style.display = "block";
        const interval = setInterval(() => {
            countdownElement.textContent = `Requesting location in ${countdown}...`;
            countdown -= 1;
            if (countdown < 0) {
                clearInterval(interval);
                countdownElement.style.display = "none";
                callback();
            }
        }, 1000);
    }

    // Function to fetch the location
    function fetchLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    latitudeInput.value = position.coords.latitude;
                    longitudeInput.value = position.coords.longitude;
                    alert("Location fetched successfully!");
                },
                (error) => {
                    switch (error.code) {
                        case error.PERMISSION_DENIED:
                            alert("Location access denied. Please enable GPS!");
                            break;
                        case error.POSITION_UNAVAILABLE:
                            alert("Location unavailable. Please try again later.");
                            break;
                        case error.TIMEOUT:
                            alert("Location request timed out. Please retry.");
                            break;
                        default:
                            alert("An unknown error occurred.");
                    }
                },
                { timeout: 10000 } // Set a timeout of 10 seconds
            );
        } else {
            alert("Geolocation is not supported by this browser.");
        }
    }

    // Start the countdown and fetch the location
    startCountdown(fetchLocation);
});

window.addEventListener("scroll", function() {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 1000) {
        navbar.style.backgroundColor = '#060913';
    } else {
        navbar.style.backgroundColor = 'transparent';
    }
}, false);
