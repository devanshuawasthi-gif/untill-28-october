(() => {
  const year = document.getElementById("year");
  if (year) year.textContent = new Date().getFullYear();

  const toggle = document.getElementById("menuToggle");
  const nav = document.getElementById("mainNav");
  if (toggle && nav) {
    toggle.addEventListener("click", () => {
      const isOpen = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(isOpen));
      toggle.setAttribute("aria-label", isOpen ? "Close navigation" : "Open navigation");
    });
    nav.querySelectorAll("a").forEach(link => link.addEventListener("click", () => {
      nav.classList.remove("open");
      toggle.setAttribute("aria-expanded", "false");
    }));
  }

  const motionToggle = document.getElementById("motionToggle");
  const savedMotion = localStorage.getItem("until28-motion");
  if (savedMotion === "off") document.body.classList.add("motion-off");
  const updateMotionLabel = () => {
    const off = document.body.classList.contains("motion-off");
    if (motionToggle) {
      motionToggle.textContent = off ? "Motion: off" : "Motion: on";
      motionToggle.setAttribute("aria-pressed", String(off));
    }
  };
  updateMotionLabel();
  if (motionToggle) motionToggle.addEventListener("click", () => {
    document.body.classList.toggle("motion-off");
    localStorage.setItem("until28-motion", document.body.classList.contains("motion-off") ? "off" : "on");
    updateMotionLabel();
  });

  const items = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    items.forEach(item => observer.observe(item));
  } else {
    items.forEach(item => item.classList.add("visible"));
  }

  // A light, decorative star field; it pauses when reduced motion is requested.
  const canvas = document.getElementById("stars");
  if (canvas && canvas.getContext) {
    const ctx = canvas.getContext("2d");
    let width = 0, height = 0, stars = [], frame = 0;
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    function resize() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = window.innerWidth; height = window.innerHeight;
      canvas.width = width * dpr; canvas.height = height * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      stars = Array.from({length: Math.min(90, Math.floor(width / 14))}, () => ({
        x: Math.random() * width, y: Math.random() * height,
        r: Math.random() * 1.2 + .25, a: Math.random() * .45 + .12,
        phase: Math.random() * 6
      }));
      draw();
    }
    function draw() {
      ctx.clearRect(0, 0, width, height);
      stars.forEach(s => {
        const pulse = reduceMotion || document.body.classList.contains("motion-off")
          ? 1 : .65 + Math.sin(frame * .018 + s.phase) * .35;
        ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(232, 204, 235, ${s.a * pulse})`; ctx.fill();
      });
      if (!reduceMotion && !document.body.classList.contains("motion-off")) frame++;
      if (!reduceMotion && !document.body.classList.contains("motion-off")) requestAnimationFrame(draw);
    }
    window.addEventListener("resize", resize);
    resize();
    if (!reduceMotion) {
      const motionObserver = new MutationObserver(() => {
        if (!document.body.classList.contains("motion-off")) draw();
      });
      motionObserver.observe(document.body, {attributes: true, attributeFilter: ["class"]});
    }
  }
})();
