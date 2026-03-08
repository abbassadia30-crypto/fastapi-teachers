import { PorcupineManager } from '@picovoice/porcupine-capacitor';
import { WebVoiceProcessor } from '@picovoice/web-voice-processor';

async function setupStarbrain() {
const accessKey = "YOUR_PICOVOICE_ACCESS_KEY"; // Get from console.picovoice.ai

try {
const porcupineManager = await PorcupineManager.fromBuiltInKeywords(
accessKey,
["PORCUPINE"], // You can train 'Starbrain' on their console and use the file path here
(keywordIndex) => {
if (keywordIndex === 0) {
console.log("Wake word detected!");
// Switch to your Starbrain Animation Page
window.location.href = '/starbrain-vault';
}
}
);

// Start the process
await porcupineManager.start();
console.log("Starbrain is lurking in the background...");

} catch (err) {
console.error("Starbrain failed to start:", err);
}
}

// Start listening when the app is ready
document.addEventListener('deviceready', setupStarbrain);

import { SpeechRecognition } from '@capgo/capacitor-speech-recognition';

async function startBackgroundListener() {
    // Check permissions first
    const { available } = await SpeechRecognition.available();
    if (!available) return;

    await SpeechRecognition.requestPermissions();

    // Start listening continuously
    SpeechRecognition.start({
        language: "en-US",
        partialResults: true, // Crucial for "Hey Starbrain" detection
        popup: false,        // Keep it invisible
    });

    SpeechRecognition.addListener('partialResults', (data) => {
        const text = data.matches[0].toLowerCase();

        // Logical check for your wake-word
        if (text.includes("starbrain") || text.includes("hey star")) {
            // 1. Stop this listener to free the mic for the command
            SpeechRecognition.stop();

            // 2. Redirect to your Starbrain UI Page
            window.location.href = "/starbrain-active";
        }
    });
}

// Start when app is ready
async function sendToStarbrain(voiceText) {
    const feedbackBox = document.getElementById('feedback-box');

    // 1. Check Internet (Institutional apps in Pakistan need this for reliability)
    if (!navigator.onLine) {
        showSignBox("No Internet Connection. Starbrain is offline.", "error");
        return;
    }

    // 2. Start 'Working' Animation
    setStarbrainWorking("CONSULTING STARBRAIN...");

    try {
        const response = await fetch('https://your-fastapi-url.render.com/starbrain', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: voiceText })
        });

        if (response.ok) {
            const data = await response.json();
            finishStarbrain(true, data.message || "Task Completed!");
        } else {
            throw new Error("Starbrain is busy.");
        }
    } catch (err) {
        // 3. The Red Sign Box (Direct Correction)
        finishStarbrain(false, "Connection Lost. Please try again.");
    }
}

function showSignBox(msg, type) {
    const box = document.getElementById('feedback-box');
    box.innerText = msg;
    box.className = `sign-box ${type}`; // 'success' or 'error'
    box.style.display = 'block';
    setTimeout(() => { box.style.display = 'none'; }, 5000);
}


document.addEventListener('deviceready', startBackgroundListener);