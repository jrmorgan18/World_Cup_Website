(function () {
  'use strict';

  var article = document.querySelector('[data-longform]');
  var body = document.getElementById('longform-body');
  var progress = document.getElementById('longform-progress-bar');
  if (!article || !body || !progress) return;

  function updateProgress() {
    var start = body.getBoundingClientRect().top + window.scrollY;
    var distance = body.offsetHeight - window.innerHeight;
    var amount = distance > 0 ? (window.scrollY - start) / distance : 0;
    progress.style.transform = 'scaleX(' + Math.max(0, Math.min(1, amount)) + ')';
  }

  var links = Array.prototype.slice.call(document.querySelectorAll('.longform-toc a[href^="#"]'));
  var headings = Array.prototype.slice.call(document.querySelectorAll('.longform-body h2[id]'));

  if ('IntersectionObserver' in window && headings.length) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        links.forEach(function (link) {
          link.classList.toggle('is-active', link.getAttribute('href') === '#' + entry.target.id);
        });
      });
    }, { rootMargin: '-18% 0px -70% 0px' });
    headings.forEach(function (heading) { observer.observe(heading); });
  }

  var ticking = false;
  window.addEventListener('scroll', function () {
    if (ticking) return;
    window.requestAnimationFrame(function () {
      updateProgress();
      ticking = false;
    });
    ticking = true;
  }, { passive: true });
  window.addEventListener('resize', updateProgress);
  updateProgress();
}());
