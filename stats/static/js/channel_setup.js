
var checkboxes = document.querySelectorAll('.checkbox');
checkboxes.forEach(function (checkbox) {
    checkbox.addEventListener("change", (event) => {
        var src = event.currentTarget;
        var label = src.previousElementSibling;
        var cell = src.parentElement.parentElement;
        label.classList.toggle("selectedText");
        cell.classList.toggle("selectedCell");
    })
})

