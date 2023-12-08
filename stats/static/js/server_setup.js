function getCurrentTimeString() {
    var now = new Date;

    var hour = now.getHours();
    var hourString = String(hour);
    if (hour === 0) {
        hourString = '12';
    }

    var minute = now.getMinutes();
    var minuteString = String(minute);
    if (minute < 10) {
        minuteString = '0' + minuteString;
    }

    if (hour <= 12) {
        return hourString + ":" + minuteString + "am";
    } else {
        return (hour - 12) + ":" + minuteString + "pm";
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