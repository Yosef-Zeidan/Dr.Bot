document.addEventListener('DOMContentLoaded', () => {

    // Check which page is currently loaded
    if (document.querySelector('.auth-container')) {
        handleLoginPage();
    } else if (document.querySelector('.chat-container')) {
        handleChatPage();
    }

});

// --- LOGIN PAGE LOGIC ---
function handleLoginPage() {
    const loginForm = document.getElementById('login-form');
    const loginError = document.getElementById('login-error');

    loginForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        // --- IMPORTANT ---
        // This is a mock login. In a real application, you would send these
        // credentials to your backend for verification.
        if (username && password) {
            console.log('Login successful');
            // Store a "session" token to indicate the user is logged in
            sessionStorage.setItem('isLoggedIn', 'true');
            // Redirect to the chat page
            window.location.href = 'chat.html';
        } else {
            loginError.textContent = 'Please enter both username and password.';
        }
    });
}

// --- CHAT PAGE LOGIC ---
function handleChatPage() {
    // Redirect to login if not authenticated
    if (sessionStorage.getItem('isLoggedIn') !== 'true') {
        window.location.href = 'index.html';
        return; // Stop further execution
    }

    const chatWindow = document.getElementById('chat-window');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const logoutBtn = document.getElementById('logout-btn');

    // --- BOT'S PRE-DEFINED QUESTIONS AND LOGIC ---
    const questions = [
        "Hello! I'm here to help you. What is your primary goal today? (e.g., 'Learn about pricing', 'Troubleshoot an issue')",
        "Thank you. Could you please provide more details about your request?",
        "Is there anything else I can assist you with?"
    ];

    let currentQuestionIndex = 0;
    let userResponses = {};

    function displayMessage(text, sender) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', sender);
        messageElement.textContent = text;
        chatWindow.appendChild(messageElement);
        // Scroll to the latest message
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    function askNextQuestion() {
        if (currentQuestionIndex < questions.length) {
            displayMessage(questions[currentQuestionIndex], 'bot');
        } else {
            // End of pre-defined questions, provide a final message
            provideFinalResponse();
        }
    }

    function provideFinalResponse() {
        // --- AI BOT'S RESPONSE LOGIC ---
        // This is where you would process the collected 'userResponses'
        // and have the AI generate a more detailed explanation.
        // For now, it's a simple acknowledgment.
        let summary = `Thank you for providing the information. Based on your goal to "${userResponses[0]}" and the details you provided, here is what I found...`;
        displayMessage(summary, 'bot');
        displayMessage("This is where the AI's full explanation would go.", 'bot');
    }

    function handleUserInput() {
        const text = userInput.value.trim();
        if (text) {
            displayMessage(text, 'user');

            // Store the user's answer
            userResponses[currentQuestionIndex] = text;
            currentQuestionIndex++;
            
            userInput.value = '';

            // Ask the next question after a short delay
            setTimeout(askNextQuestion, 500);
        }
    }

    sendBtn.addEventListener('click', handleUserInput);
    userInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            handleUserInput();
        }
    });

    logoutBtn.addEventListener('click', () => {
        sessionStorage.removeItem('isLoggedIn');
        window.location.href = 'index.html';
    });
    
    // Start the conversation
    askNextQuestion();
}