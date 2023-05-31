const api_route = 'http://127.0.0.1:8000/jaltol/'
var botResponse

async function sendMessage() {
    var userInput = document.getElementById("user-input").value;
    var chatWindow = document.getElementById("chat-window");
    var processingMessage = document.getElementById("processing-message");

    // Display "Processing..." message
    // processingMessage.style.display = "block";
    processingMessage.textContent = "Processing...";
    // Clear the user input field
    document.getElementById("user-input").value = "";

    // Append user message to the chat window
    var userMessage = createMessageElement(userInput, "user");
    chatWindow.appendChild(userMessage);

    var data = {
        user: userInput,
    };

    // var botResponse = "This is the bot's response.";
    try {
    var response = await fetch(api_route, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
    });

    var data = await response.json();
    botResponse = data;
    } catch(error) {
    // Handle any errors
    console.error('Error:', error);
    }

    // Append bot response to the chat window
    var botMessage = createMessageElement(botResponse, "bot");
    chatWindow.appendChild(botMessage);

    // Hide "Processing..." message
    // processingMessage.style.display = "none";
    processingMessage.textContent = ".";

    // Scroll to the bottom of the chat window
    chatWindow.scrollTop = chatWindow.scrollHeight;

}

function createMessageElement(message, role) {
    var messageElement = document.createElement("div");
    messageElement.classList.add("message", role + "-message");
    messageElement.textContent = message;
    return messageElement;
}
