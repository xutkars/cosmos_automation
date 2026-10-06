// ==========================================
// COSMOS AUTOMATION - FRONTEND JAVASCRIPT
// ==========================================

let statusInterval = null;


// ==========================================
// GET HTML ELEMENTS
// ==========================================

const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password");

const startButton = document.getElementById("startAutomation");
const stopButton = document.getElementById("stopAutomation");

const systemStatus = document.getElementById("systemStatus");

const progressText = document.getElementById("progressText");
const progressFill = document.getElementById("progressFill");

const currentPage = document.getElementById("currentPage");
const processed = document.getElementById("processed");
const submitted = document.getElementById("submitted");
const errors = document.getElementById("errors");

const currentProposal = document.getElementById("currentProposal");

const activityTitle = document.getElementById("activityTitle");
const activityMessage = document.getElementById("activityMessage");

const resultsTable = document.getElementById("resultsTable");


// ==========================================
// START AUTOMATION
// ==========================================

startButton.addEventListener("click", async function () {

    const username = usernameInput.value.trim();
    const password = passwordInput.value;

    // Validate username
    if (!username) {
        alert("Please enter your COSMOS username.");
        usernameInput.focus();
        return;
    }

    // Validate password
    if (!password) {
        alert("Please enter your COSMOS password.");
        passwordInput.focus();
        return;
    }

    // Disable inputs while running
    usernameInput.disabled = true;
    passwordInput.disabled = true;

    startButton.disabled = true;
    stopButton.disabled = false;

    // Reset UI
    systemStatus.textContent = "Starting";
    progressText.textContent = "Starting automation...";
    progressFill.style.width = "0%";

    currentPage.textContent = "0";
    processed.textContent = "0";
    submitted.textContent = "0";
    errors.textContent = "0";

    currentProposal.textContent = "-";

    activityTitle.textContent = "Automation Starting";
    activityMessage.textContent = "Connecting to COSMOS...";

    try {

        const response = await fetch("/api/start", {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                username: username,
                password: password
            })
        });


        const data = await response.json();


        if (!response.ok || !data.success) {

            throw new Error(
                data.message || "Failed to start automation."
            );
        }


        // Start polling backend status
        startStatusPolling();


    } catch (error) {

        console.error("Start error:", error);

        systemStatus.textContent = "Error";

        activityTitle.textContent = "Failed to Start";
        activityMessage.textContent = error.message;

        progressText.textContent = error.message;

        // Enable fields again
        usernameInput.disabled = false;
        passwordInput.disabled = false;

        startButton.disabled = false;
        stopButton.disabled = true;
    }
});


// ==========================================
// POLL STATUS
// ==========================================

function startStatusPolling() {

    // Clear existing polling
    if (statusInterval) {
        clearInterval(statusInterval);
    }

    // Immediately get status
    getStatus();

    // Then check every second
    statusInterval = setInterval(
        getStatus,
        1000
    );
}


// ==========================================
// GET STATUS FROM FLASK
// ==========================================

async function getStatus() {

    try {

        const response = await fetch("/api/status", {
            method: "GET",
            cache: "no-store"
        });


        if (!response.ok) {
            throw new Error("Unable to get automation status.");
        }


        const data = await response.json();

        updateUI(data);


        // Stop polling when automation finishes
        if (
            data.status === "Completed" ||
            data.status === "Error"
        ) {

            stopStatusPolling();

        }


    } catch (error) {

        console.error("Status error:", error);

        activityMessage.textContent =
            "Unable to communicate with backend.";

    }
}


// ==========================================
// UPDATE UI
// ==========================================

function updateUI(data) {

    // --------------------------------------
    // System status
    // --------------------------------------

    systemStatus.textContent =
        data.status || "Unknown";


    // --------------------------------------
    // Activity message
    // --------------------------------------

    activityMessage.textContent =
        data.message || "";


    // --------------------------------------
    // Current proposal
    // --------------------------------------

    currentProposal.textContent =
        data.current_proposal || "-";


    // --------------------------------------
    // Statistics
    // --------------------------------------

    processed.textContent =
        data.processed ?? 0;

    submitted.textContent =
        data.submitted ?? 0;

    errors.textContent =
        data.errors ?? 0;

    currentPage.textContent =
        data.current_page ?? 0;


    // --------------------------------------
    // Progress
    // --------------------------------------

    const page = Number(data.current_page || 0);
    const totalPages = Number(data.total_pages || 0);

    let percentage = 0;

    if (totalPages > 0) {

        percentage =
            Math.round((page / totalPages) * 100);

    }

    // Don't show more than 100%
    percentage = Math.min(percentage, 100);

    progressFill.style.width =
        percentage + "%";


    if (totalPages > 0) {

        progressText.textContent =
            `Page ${page} of ${totalPages} (${percentage}%)`;

    } else {

        progressText.textContent =
            data.message || "Processing...";
    }


    // --------------------------------------
    // Activity title
    // --------------------------------------

    if (data.status === "Running") {

        activityTitle.textContent =
            "Automation Running";

    } else if (data.status === "Completed") {

        activityTitle.textContent =
            "Automation Completed";

        progressFill.style.width = "100%";
        progressText.textContent =
            "Automation completed successfully.";

    } else if (data.status === "Error") {

        activityTitle.textContent =
            "Automation Error";

    } else {

        activityTitle.textContent =
            data.status || "Automation";
    }


    // --------------------------------------
    // Buttons
    // --------------------------------------

    if (data.running) {

        startButton.disabled = true;
        stopButton.disabled = false;

        usernameInput.disabled = true;
        passwordInput.disabled = true;

    } else {

        startButton.disabled = false;
        stopButton.disabled = true;

        usernameInput.disabled = false;
        passwordInput.disabled = false;
    }
}


// ==========================================
// STOP AUTOMATION
// ==========================================

stopButton.addEventListener("click", async function () {

    try {

        const response = await fetch("/api/stop", {
            method: "POST"
        });

        const data = await response.json();

        activityMessage.textContent =
            data.message || "Stop request sent.";

    } catch (error) {

        console.error("Stop error:", error);

        activityMessage.textContent =
            "Unable to stop automation.";
    }
});


// ==========================================
// STOP STATUS POLLING
// ==========================================

function stopStatusPolling() {

    if (statusInterval) {

        clearInterval(statusInterval);

        statusInterval = null;
    }
}


// ==========================================
// INITIAL STATUS CHECK
// ==========================================

window.addEventListener("DOMContentLoaded", function () {

    // Make sure Stop is disabled initially
    stopButton.disabled = true;

    // Check whether an automation is already running
    getStatus();

});