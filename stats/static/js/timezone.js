function militaryTime(dateTime) {
    var hour = dateTime.getHours();
    var minute = dateTime.getMinutes();
    var hourString = String(hour);
    if (hour < 10) {
        var hourString = '0' + String(hour);
    } 

    var minuteString = String(minute);
    if (minute < 10) {
        var minuteString = '0' + String(minute);
    }
    return hourString + ':' + minuteString;

}

function meridiemTime(dateTime) {
    var hour = dateTime.getHours();
    var hourString = String(hour);

    var minute = dateTime.getMinutes();
    var minuteString = String(minute);
    if (minute < 10) {
        minuteString = '0' + minuteString;
    }
    if (hour === 0) {
        return "12:" + minuteString + "am";
    }
    else if (hour === 12) {
        return "12:" + minuteString + "pm";
    }
    else if (hour < 12) {
        return hourString + ":" + minuteString + "am";
    } 
    else {
        return (hour - 12) + ":" + minuteString + "pm";
    }
}

function getCurrentTimezoneString(timezone) {
    var nowUTC = new Date;
    var nowTimezone = new Date(nowUTC.toLocaleString('en-US', {timeZone: timezone})); // converts date into specified timezone
    if ($("#time-format").is(":checked")) {
        return militaryTime(nowTimezone);
    } else {
        return meridiemTime(nowTimezone);
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
settings = {
    dropdownCssClass: 'dropdown',
    selectionCssClass: 'searchbox',
    width: "494px",
    templateResult: formatResult,
    templateSelection: formatSelection
};

$(document).ready(function() {

    $('#id_timezone').select2(settings);

    $('#time-format').on('input', () => { // reloads selector times when the time format is toggled
        $("#id_timezone").select2("destroy");
        $("#id_timezone").select2(settings);
    });


    $("#timezone-selector").css("visibility", "visible"); // prevents FOUC

});