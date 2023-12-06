
function fitText() {
  /* resize the name of a server to fit its card container */
  var container = $('.servercard');
  var text = $('.text');
  var fontSize = 16;
  text.css('font-size', fontSize + 'px');
  while (text.height() > 82) {
    fontSize--;
    text.css('font-size', fontSize + 'px');
  }
}
  
$(document).ready(function() {
  fitText();
  $(window).on('resize', fitText);
});