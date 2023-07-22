$.tablesorter.addParser({ 
    // set a unique id 
    id: 'bignumber',
    is: function(s, table, cell, $cell) { 
        // return false so this parser is not auto detected 
        return false; 
    }, 
    format: function(s, table, cell, cellIndex) {
        // format your data for normalization 
        return s.replace(/,/g,'');
    }, 
    // set type, either numeric or text 
    type: 'numeric' 
  });
  
  
  // the inner function ensures that the "rank" column remains static even after being sorted
  $(function() {
    $("#user_rankings").tablesorter().on("sortEnd", function () {
        $(this).find('tbody td:first-child').text(function (i) {
            return i + 1;
        });
    });
  });
  