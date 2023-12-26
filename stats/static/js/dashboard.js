
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

function setModalScript(modalID, buttonID, XID) {
  $(buttonID).on("click", () => {
    $(modalID).show();
  });

  $(XID).on("click", () => {
    $(modalID).hide();
  });

  $(window).on("click", (event) => {
    if ($(event.target).is(modalID)) {
      $(modalID).hide();
    }
  });
}

$(document).ready(function() {
  fitText();
  $(window).on('resize', fitText);

  setModalScript("#hideModal", "#hideButton", "#hideX");
  setModalScript("#deleteModal", "#deleteButton", "#deleteX");

});
