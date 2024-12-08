document.addEventListener("DOMContentLoaded", () => {
    const latitudeInput = document.getElementById("latitude");
    const longitudeInput = document.getElementById("longitude");
    const markButton = document.getElementById("mark-btn");
    const unmarkButton = document.getElementById("unmark-btn");
    const countdownDisplay = document.getElementById("countdown"); // Display countdown

    let countdown = 5; // Countdown seconds
    let locationFetched = false; // Flag to check if location is fetched

    // Apply initial styles for countdown
    countdownDisplay.style.color = "red";
    countdownDisplay.style.fontWeight = "bold";

    // Disable buttons initially
    markButton.disabled = true;
    unmarkButton.disabled = true;

    // Start countdown
    const countdownInterval = setInterval(() => {
        if (locationFetched) {
            clearInterval(countdownInterval); // Stop countdown if location is fetched
            return;
        }

        countdownDisplay.textContent = `Location will be fetched in ${countdown} seconds...`;
        countdown--;

        if (countdown < 0) {
            clearInterval(countdownInterval);
            fetchLocation();
        }
    }, 1000);

    // Function to fetch the location
    function fetchLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    latitudeInput.value = position.coords.latitude;
                    longitudeInput.value = position.coords.longitude;

                    // Mark location as fetched
                    locationFetched = true;

                    // Clear the countdown text
                    countdownDisplay.textContent = "";

                    // Enable buttons after fetching location
                    markButton.disabled = false;
                    unmarkButton.disabled = false;
                },
                (error) => {
                    // Handle location errors
                    if (error.code === error.PERMISSION_DENIED) {
                        alert("Location permission is required. Please enable GPS.");
                    } else {
                        alert("Error retrieving location. Please try again!");
                    }

                    // Optionally, retry fetching location if necessary
                    countdownDisplay.textContent = "Error retrieving location. Retrying...";
                    fetchLocation(); // Retry fetching location
                }
            );
        } else {
            alert("Geolocation is not supported by this browser.");
            countdownDisplay.textContent = "Geolocation not supported.";
        }
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
