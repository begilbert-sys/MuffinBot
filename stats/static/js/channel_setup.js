// toggles stylization for when checkboxes are checked/unchecked 
var checkboxes = document.querySelectorAll('.checkbox');
checkboxes.forEach(function (checkbox) {
    checkbox.addEventListener("change", (event) => {
        var src = event.currentTarget;
        var label = src.previousElementSibling;
        var cell = src.parentElement.parentElement;
        label.classList.toggle("unselectedText");
        cell.classList.toggle("selectedCell");
    })
})

