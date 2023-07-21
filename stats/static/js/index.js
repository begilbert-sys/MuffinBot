/* 
table sort
*/

$.tablesorter.addParser({ 
  // set a unique id 
  id: 'bignumber',
  is: function(s) { 
      // return false so this parser is not auto detected 
      return false; 
  }, 
  format: function(s) {
      // format your data for normalization 
      return s.replace('$','').replace(/,/g,'');
  }, 
  // set type, either numeric or text 
  type: 'numeric' 
}); 

$(function() {
  $("#user_rankings").tablesorter({theme: 'blue'});
});


/*
display date data
*/

// util function for getting the data from views.py
function getDateData(url, number_of_days) {
  return $.ajax({
    url: url,
    type: 'GET',
    dataType: "json",
    async: false,
    headers: {'X-Requested-With': 'XMLHttpRequest'},
    success: function(data) {return data}
  }).responseJSON;
};


// chart 
google.charts.load('current', {packages: ['corechart', 'line']});
google.charts.setOnLoadCallback(drawBasic);

function drawBasic() {
  var date_data = getDateData("date_data/", 100);

  var data = new google.visualization.DataTable();
  data.addColumn('date', 'Year');
  data.addColumn('number', 'Msgs');

  var sorted_keys = Object.keys(date_data).sort();
  for (let i = 0; i < sorted_keys.length; i++) {
    var dateiso = sorted_keys[i];
    var value = date_data[dateiso];
    data.addRow([new Date(dateiso), value]);
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