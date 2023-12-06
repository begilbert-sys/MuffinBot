function toggleSelector() {
    var tzPopdown = document.getElementById('timezone-wrapper');
    var arrow = document.getElementById('popdown-arrow');
    if (tzPopdown.style.display === "none") {
        tzPopdown.style.display = "block";
        arrow.src = up_arrow;
        setTimes();
    } else {
        tzPopdown.style.display = "none";
        arrow.src = down_arrow;
    }
}

function getTimeStr() {
    var now = new Date;
    var hour = now.getHours();
    if (hour <= 12) {
        return now.getHours() + ":" + now.getMinutes() + "am";
    } else {
        return (now.getHours() - 12) + ":" + now.getMinutes() + "pm";
    }
}

function setTimes() {
    const pacific = document.getElementById('pacific-time');
    var now = new Date;
    pacific.children[1].textContent = now.toLocaleTimeString('en-US',{ hour: '2-digit', minute: '2-digit' });
}