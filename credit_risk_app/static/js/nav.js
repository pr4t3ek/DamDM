document.addEventListener("keydown", function (e) {
  if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT" || e.target.tagName === "TEXTAREA") {
    return;
  }
  const body = document.body;
  if (e.key === "ArrowRight") {
    const href = body.dataset.nextHref;
    if (href) window.location.href = href;
  } else if (e.key === "ArrowLeft") {
    const href = body.dataset.prevHref;
    if (href) window.location.href = href;
  }
});
