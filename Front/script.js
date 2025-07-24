// script.js (Final Version - Connected to Live Backend)

document.addEventListener('DOMContentLoaded', () => {
    // Check which page is currently loaded and run the appropriate logic
    if (document.querySelector('.auth-container')) {
        handleLoginPage();
    } else if (document.querySelector('.chat-container')) {
        handleChatPage();
    }
});

// --- LOGIN PAGE LOGIC (No changes needed here) ---
function handleLoginPage() {
    const loginForm = document.getElementById('login-form');
    const loginError = document.getElementById('login-error');

    loginForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        // This is a simple mock login for demonstration purposes.
        if (username && password) {
            console.log('Login successful');
            sessionStorage.setItem('isLoggedIn', 'true');
            window.location.href = 'chat.html';
        } else {
            loginError.textContent = 'Please enter both username and password.';
        }
    });
}


// --- CHAT PAGE LOGIC (All new logic is here) ---
function handleChatPage() {
    // Redirect to login if not authenticated
    if (sessionStorage.getItem('isLoggedIn') !== 'true') {
        window.location.href = 'index.html';
        return; // Stop further execution
    }

    const sendBtn = document.getElementById('send-btn');
    const userInputElement = document.getElementById('user-input');
    const logoutBtn = document.getElementById('logout-btn');

    // Add event listeners for sending messages
    sendBtn.addEventListener('click', handleUserInput);
    userInputElement.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            handleUserInput();
        }
    });

    // Add event listener for logout
    logoutBtn.addEventListener('click', () => {
        sessionStorage.removeItem('isLoggedIn');
        window.location.href = 'index.html';
    });

    // Display a welcome message when the chat page loads
    displayMessage("Hello! I'm your AI assistant. How can I help you today?", 'bot');
}


// --- Core function to send a message to the backend ---
async function handleUserInput() {
    // === CONFIGURATION: This is your backend URL ===
    const backendUrl = 'https://vigilant-pancake-g4q5wp744xwghwg57-5000.app.github.dev/';
    // ===============================================

    const userInputElement = document.getElementById('user-input');
    const text = userInputElement.value.trim();

    if (text) {
        displayMessage(text, 'user');
        userInputElement.value = ''; // Clear the input field immediately

        // Show a "thinking..." indicator for better user experience
        const typingIndicator = displayMessage("AI is thinking...", 'bot', true);

        try {
            // Make the network call to your backend server
            const response = await fetch(`${backendUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: text })
            });

            // Remove the "thinking..." indicator once we get a response
            typingIndicator.remove();

            if (!response.ok) {
                // Handle server-side errors (like 500)
                const errorData = await response.json();
                throw new Error(errorData.error || `Server error: ${response.status}`);
            }

            const data = await response.json();
            
            // Display the bot's actual response
            if (data.response) {
                displayMessage(data.response, 'bot');
            } else {
                throw new Error("Received an empty response from the server.");
            }

        } catch (error) {
            // Handle network errors (like server being down or unreachable)
            console.error("Error connecting to the backend:", error);
            if (typingIndicator) typingIndicator.remove(); // Make sure indicator is removed on error
            displayMessage(`Sorry, there was a problem connecting to the AI. Please try again later.`, 'bot');
        }
    }
}


// --- Utility function to add messages to the chat window ---
// This version includes a flag for the "typing" indicator styling
function displayMessage(text, sender, isTyping = false) {
    const chatWindow = document.getElementById('chat-window');
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', sender);
    
    // Add a special class for the typing indicator for potential styling
    if (isTyping) {
        messageElement.classList.add('typing');
    }
    
    messageElement.textContent = text;
    chatWindow.appendChild(messageElement);
    // Scroll to the latest message
    chatWindow.scrollTop = chatWindow.scrollHeight;
    
    return messageElement; // Return the element so we can remove it later
}
