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