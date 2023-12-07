function getCurrentTimeString() {
    var now = new Date;
    var hour = now.getHours();
    if (hour <= 12) {
        return now.getHours() + ":" + now.getMinutes() + "am";
    } else {
        return (now.getHours() - 12) + ":" + now.getMinutes() + "pm";
    }
}

function formatOption(option) {
    if (!option.id) {
        return option.text;
    }
    var currentTime = getCurrentTimeString();
    var formattedOption = $('<span style="display: flex; justify-content: space-between;">' +
    '<span style="flex: 1;">' + option.text + '</span>' +
    '<span>' + currentTime + '</span>' +
    '</span>');
    return formattedOption;
  }


// select2 setup
$(document).ready(function() {
    $('.js-example-basic-single').select2({
        dropdownCssClass: 'dropdown',
        selectionCssClass: 'searchbox',
        width: "494px",
        templateResult: formatOption
    });
});