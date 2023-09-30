google.charts.load('current', {packages: ['corechart', 'line']});
google.charts.setOnLoadCallback(topWeekly);
google.charts.setOnLoadCallback(topMonthly);
google.charts.setOnLoadCallback(topYearly);
google.charts.setOnLoadCallback(topAllTime);

const rawDateData = JSON.parse(document.getElementById('dateData').textContent);
var dateData = [];
for (let i = 0; i < rawDateData.length; i++) {
  dateData.push([new Date(rawDateData[i][0]), rawDateData[i][1]]);
};

function defaultOptions () {
  return {
    legend: {
      textStyle: {color: 'white'}
    },
    hAxis: {
      title: 'Time',
      textStyle: {color: 'white'},
      titleTextStyle: {
        color: 'white'
      }
    },
    vAxis: {
      title: 'Number of Messages',
      textStyle: {color: 'white'},
      titleTextStyle: {
        color: 'white'
      }
    },
    backgroundColor: '#2C2F33', 
  }
}

function openPage(pageName,elmnt) {
  var i, tabcontent, selected;
  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }
  selected = document.getElementsByClassName("selectedTablink");
  for (i = 0; i < selected.length; i++) {
    selected[i].classList.replace("selectedTablink", "tablink");
  }
  document.getElementById(pageName).style.display = "block";
  elmnt.classList.replace("tablink", "selectedTablink");
}

function topWeekly() {
  var dataTable = new google.visualization.DataTable();
  dataTable.addColumn('date', 'Year');
  dataTable.addColumn('number', 'Msgs');

  dataTable.addRows(dateData.slice(-7));

  var ticks = [];
  for (let i = 0; i < dataTable.getNumberOfRows(); i++) {
    ticks.push(dataTable.getValue(i, 0));
  }
  
  var chart = new google.visualization.LineChart(document.getElementById('topWeekly'));
  var options = defaultOptions()
  options.hAxis.ticks = ticks;
  options.hAxis.format = 'MMM d';
  if (dataTable.getColumnRange(1).max == 0) {
    options.vAxis.ticks = [0, 1, 2];
  }
  chart.draw(dataTable, options);
}

function topMonthly() {
  var dataTable = new google.visualization.DataTable();
  dataTable.addColumn('date', 'Year');
  dataTable.addColumn('number', 'Msgs');

  dataTable.addRows(dateData.slice(-31));

  var ticks = [];
  for (var i = 0; i < dataTable.getNumberOfRows(); i++) {
    ticks.push(dataTable.getValue(i, 0));
  }
  
  var chart = new google.visualization.LineChart(document.getElementById('topMonthly'));
  google.visualization.events.addListener(chart, 'ready', function () {
    document.getElementById('topMonthly').style.display = 'none';
  });
  var options = defaultOptions();
  options.hAxis.ticks = ticks;
  options.hAxis.format = 'M-d';
  if (dataTable.getColumnRange(1).max == 0) {
    options.vAxis.ticks = [0, 1, 2];
  }
  chart.draw(dataTable, options);
}

function topYearly() {
  var dataTable = new google.visualization.DataTable();
  dataTable.addColumn('date', 'Year');
  dataTable.addColumn('number', 'Msgs');

  dataTable.addRows(dateData.slice(-365));

  var ticks = [];
  for (var i = 0; i < dataTable.getNumberOfRows(); i++) {
    var val = dataTable.getValue(i, 0);
    if (val.getDate() == 1) {
      ticks.push(dataTable.getValue(i, 0));
    }
  }
  
  var chart = new google.visualization.LineChart(document.getElementById('topYearly'));
  google.visualization.events.addListener(chart, 'ready', function () {
    document.getElementById('topYearly').style.display = 'none';
  });
  var options = defaultOptions();
  options.hAxis.ticks = ticks;
  options.hAxis.format = 'MMM';
  if (dataTable.getColumnRange(1).max == 0) {
    options.vAxis.ticks = [0, 1, 2];
  }
  chart.draw(dataTable, options);
}

function topAllTime() {
  var dataTable = new google.visualization.DataTable();
  dataTable.addColumn('date', 'Year');
  dataTable.addColumn('number', 'Msgs');

  dataTable.addRows(dateData);

  var ticks = [];
  var earliest = dataTable.getValue(0, 0);
  var latest = dataTable.getValue(dataTable.getNumberOfRows()-1, 0);
  if (earliest.getDate() == 1 && earliest.getMonth() == 0) {
    ticks.push(earliest);
  }
  for (let i = earliest.getFullYear() + 1; i <= latest.getFullYear(); i++) {
    ticks.push(new Date(i, 0, 1));
  }
  
  var chart = new google.visualization.LineChart(document.getElementById('topAllTime'));
  google.visualization.events.addListener(chart, 'ready', function () {
    document.getElementById('topAllTime').style.display = 'none';
  });
  var options = defaultOptions();
  options.hAxis.ticks = ticks;
  options.hAxis.format = 'y';
  chart.draw(dataTable, options);
}
