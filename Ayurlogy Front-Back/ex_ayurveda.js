// AOS Init
// AOS.init({
//   duration: 1000,
//   once: true
// });

// // Simple Auto Slider
// function autoSlide(sliderId) {
//   const slider = document.getElementById(sliderId);
//   let index = 0;

//   setInterval(() => {
//     index++;
//     slider.style.transform = `translateX(-${index * 270}px)`;

//     if (index >= slider.children.length - 1) {
//       index = 0;
//       slider.style.transform = "translateX(0)";
//     }
//   }, 3000);
// }

// autoSlide("herbSlider");
// autoSlide("testimonialSlider");

// AOS Init
AOS.init({
  duration: 1000,
  once: true
});

// Simple Auto Slider
function autoSlide(sliderId) {
  const slider = document.getElementById(sliderId);
  let index = 0;

  setInterval(() => {
    index++;
    slider.style.transform = `translateX(-${index * 270}px)`;

    if (index >= slider.children.length - 1) {
      index = 0;
      slider.style.transform = "translateX(0)";
    }
  }, 3000);
}

autoSlide("herbSlider");
autoSlide("testimonialSlider");

