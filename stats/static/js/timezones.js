function getCurrentTimezoneString(timezone) {
    var nowUTC = new Date;
    var nowTimezone = new Date(nowUTC.toLocaleString('en-US', {timeZone: timezone})); // converts date into specified timezone

    var hour = nowTimezone.getHours();
    var hourString = String(hour);
    if (hour === 0) {
        hourString = '12';
    }

    var minute = nowTimezone.getMinutes();
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

function formatResult(option) {
    if (!option.id) {
        return option.text;
    }
    var timezoneTime = getCurrentTimezoneString(option.id);
    var formattedOption = $('<span style="display: flex; justify-content: space-between;">' +
    '<span style="flex: 1;">' + option.text + '</span>' +
    '<span>' + timezoneTime + '</span>' +
    '</span>');
    return formattedOption;
}

function formatSelection(option) {
    var timezoneTime = getCurrentTimezoneString(option.id);
    return option.text + " (" + timezoneTime + ")";
}

// select2 setup
$(document).ready(function() {
    $('#id_timezone').select2({
        dropdownCssClass: 'dropdown',
        selectionCssClass: 'searchbox',
        width: "494px",
        templateResult: formatResult,
        templateSelection: formatSelection
    });
});