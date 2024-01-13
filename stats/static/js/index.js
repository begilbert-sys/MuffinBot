var slideIndex = 2; // start on the first slide
var timer = null;
const wait = 7000;
loopSlides();

function incrementSlide(num) {
    slideIndex += num;
    if (slideIndex < 0) {
        slideIndex = 2;
    } else if (slideIndex > 2) {
        slideIndex = 0;
    }
}
function setSlide(num) {
    clearTimeout(timer);
    slideIndex = num;
    displaySlide()
    timer = setTimeout(loopSlides, wait);
}
function changeSlide(num) {
    clearTimeout(timer);
    incrementSlide(num);
    displaySlide()
    timer = setTimeout(loopSlides, wait);
}
function loopSlides() {
    incrementSlide(1);
    displaySlide();
    timer = setTimeout(loopSlides, wait);
}
function displaySlide() {
    var slides = document.getElementsByClassName("slide");
    var dots = document.getElementsByClassName("dot");
    for (let i = 0; i < slides.length; i++) {
        slides[i].style.display = "none";
        dots[i].classList.remove("active");
    }
    slides[slideIndex].style.display = "block";
    dots[slideIndex].classList.add("active");

}