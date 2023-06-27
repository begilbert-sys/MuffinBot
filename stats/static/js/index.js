// table sort
$(function() {
    $("#user_rankings").tablesorter();
});

// charts 
google.charts.load('current', {packages: ['corechart', 'line']});
google.charts.setOnLoadCallback(drawBasic);

function drawBasic() {

      var data = new google.visualization.DataTable();
      data.addColumn('date', 'Year');
      data.addColumn('number', 'Dogs');

      data.addRows([
      [new Date(2014, 0, 5), 5],
      [new Date(2014, 0, 6), 7],
      [new Date(2014, 0, 7), 1],
      [new Date(2014, 0, 8), 8],
      ]);

      var options = {
        hAxis: {
          title: 'Time'
        },
        vAxis: {
          title: 'Popularity'
        }
      };

      var chart = new google.visualization.LineChart(document.getElementById('chart_div'));

      chart.draw(data, options);
    }