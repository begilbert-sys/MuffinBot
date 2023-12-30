// removes a message after 1 second of delay
function hideMessages() {
    document.querySelectorAll(".message").forEach((message) => {
        message.classList.add("message_gone");
    })
};

setTimeout(hideMessages, 2500);