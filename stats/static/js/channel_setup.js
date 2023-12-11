// toggles stylization for when checkboxes are checked/unchecked 
function toggleSelect (inputElement) {
    var label = inputElement.previousElementSibling;
    var cell = inputElement.parentElement.parentElement;
    label.classList.toggle("unselectedText");
    cell.classList.toggle("selectedCell");
}

var checkboxes = document.querySelectorAll('.checkbox');
checkboxes.forEach(function (checkbox) {
    if (!checkbox.checked) {
        toggleSelect(checkbox);
    }
    checkbox.addEventListener("change", (event) => {
        var src = event.currentTarget;
        toggleSelect(src);
    })
});