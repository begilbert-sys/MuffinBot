function fitText() {
    var container = $('.servercard');
    var text = $('.text');
    var fontSize = 16;
  
    text.css('font-size', fontSize + 'px');
    console.log(text.width());
    console.log(text.height());
    while (text.height() > 50 && text.width() > 130) {
      fontSize--;
      text.css('font-size', fontSize + 'px');
    }
  }
  
  $(document).ready(function() {
    fitText();
    $(window).on('resize', fitText);
  });