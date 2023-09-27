/*
display date data
*/
const dateData = JSON.parse(document.getElementById('dateData').textContent);

const options = {
  legend: {
    textStyle: {color: 'white'}
  },
  hAxis: {
    title: 'Time',
    format: 'MMM d',
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
};

function openPage(pageName,elmnt) {
  var i, tabcontent, tablinks;
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


// chart 
google.charts.load('current', {packages: ['corechart', 'line']});
google.charts.setOnLoadCallback(topWeekly);
google.charts.setOnLoadCallback(topMonthly);
google.charts.setOnLoadCallback(topYearly);
google.charts.setOnLoadCallback(topAllTime);


function topWeekly() {
  var dataTable = new google.visualization.DataTable();
  dataTable.addColumn('date', 'Year');
  dataTable.addColumn('number', 'Msgs');

  for (let i = dateData.length - 7; i < dateData.length; i++) {
    dataTable.addRow([new Date(dateData[i][0]), dateData[i][1]]);
  };

  var ticks = [];
  for (let i = 0; i < dataTable.getNumberOfRows(); i++) {
    ticks.push(dataTable.getValue(i, 0));
  }
  
  var chart = new google.visualization.LineChart(document.getElementById('topWeekly'));
  options.ticks = ticks;
  chart.draw(dataTable, options);
}

function topMonthly() {
  var dataTable = new google.visualization.DataTable();
  dataTable.addColumn('date', 'Year');
  dataTable.addColumn('number', 'Msgs');

  for (let i = dateData.length - 31; i < dateData.length; i++) {
    dataTable.addRow([new Date(dateData[i][0]), dateData[i][1]]);
  };

  var ticks = [];
  for (var i = 0; i < dataTable.getNumberOfRows(); i++) {
    ticks.push(dataTable.getValue(i, 0));
  }
  
  var chart = new google.visualization.LineChart(document.getElementById('topMonthly'));
  google.visualization.events.addListener(chart, 'ready', function () {
    document.getElementById('topMonthly').style.display = 'none';
  });
  options.ticks = ticks;
  chart.draw(dataTable, options);
}

function topYearly() {
  var dataTable = new google.visualization.DataTable();
  dataTable.addColumn('date', 'Year');
  dataTable.addColumn('number', 'Msgs');

  for (let i = dateData.length - 365; i < dateData.length; i++) {
    dataTable.addRow([new Date(dateData[i][0]), dateData[i][1]]);
  };

  var ticks = [];
  for (var i = 0; i < dataTable.getNumberOfRows(); i++) {
    ticks.push(dataTable.getValue(i, 0));
  }
  
  var chart = new google.visualization.LineChart(document.getElementById('topYearly'));
  google.visualization.events.addListener(chart, 'ready', function () {
    document.getElementById('topYearly').style.display = 'none';
  });
  chart.draw(dataTable, options);
}

function topAllTime() {
  var dataTable = new google.visualization.DataTable();
  dataTable.addColumn('date', 'Year');
  dataTable.addColumn('number', 'Msgs');

  for (let i = 0; i < dateData.length; i++) {
    dataTable.addRow([new Date(dateData[i][0]), dateData[i][1]]);
  };

  var ticks = [];
  for (var i = 0; i < dataTable.getNumberOfRows(); i++) {
    ticks.push(dataTable.getValue(i, 0));
  }
  
  var chart = new google.visualization.LineChart(document.getElementById('topAllTime'));
  google.visualization.events.addListener(chart, 'ready', function () {
    document.getElementById('topAllTime').style.display = 'none';
  });
  chart.draw(dataTable, options);
}

