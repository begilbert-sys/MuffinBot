/* 
table sort
*/
$(function() {
    $("#user_rankings").tablesorter();
});

/* 
charts 
*/
google.charts.load('current', {packages: ['corechart', 'line']});
google.charts.setOnLoadCallback(drawBasic);

function drawBasic() {
    const date_data = JSON.parse(document.getElementById('date_counts').textContent);

    var data = new google.visualization.DataTable();
    data.addColumn('date', 'Year');
    data.addColumn('number', 'Msgs');

    var sorted_keys = Object.keys(date_data).sort();
    for (let i = 0; i < sorted_keys.length; i++) {
        var date = sorted_keys[i];
        var value = date_data[date];
        var year = Number(date.substring(0,2)) + 2000;
        var monthIndex = Number(date.substring(2,4)) - 1;
        var day = Number(date.substring(4,6));
        data.addRow([new Date(year, monthIndex, day), value]);
    };

    var options = {
        hAxis: {
          title: 'Time'
        },
        vAxis: {
          title: 'Number of Messages'
        },
        backgroundColor: '#2C2F33'
      };

    var chart = new google.visualization.LineChart(document.getElementById('chart_div'));

    chart.draw(data, options);

}