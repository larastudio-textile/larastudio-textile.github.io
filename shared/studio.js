/* Всё содержание уже есть в HTML: макет можно открыть двойным кликом. */
(() => {
  'use strict';
  const views = [...document.querySelectorAll('[data-view]')];
  const scene = document.getElementById('scene');
  const motionButton = document.getElementById('motion-toggle');
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const dialog = document.getElementById('photo-dialog');
  let activeView = 'studio', sceneVisible = false, userPaused = false;
  const storedScroll = new Map();

  function route() {
    const hash = location.hash.slice(1) || document.body.dataset.defaultView || 'studio';
    if (hash === 'main') { views.find(v => !v.hidden)?.querySelector('h1')?.focus(); return; }
    const target = views.find(view => view.id === hash) || views[0];
    storedScroll.set(activeView, window.scrollY);
    document.querySelectorAll('video').forEach(video => video.pause());
    if (dialog.open) dialog.close();
    views.forEach(view => { view.hidden = view !== target; });
    activeView = target.id;
    document.querySelectorAll('.site-header nav a').forEach(link => {
      const linkView = link.dataset.route || link.hash.slice(1);
      const backLink = target.querySelector('.back-link');
      const parentView = backLink?.dataset.route || backLink?.hash.slice(1);
      const isActive = linkView === activeView || (target.classList.contains('product-view') && parentView === linkView);
      if (isActive) link.setAttribute('aria-current', 'page'); else link.removeAttribute('aria-current');
    });
    const title = target.querySelector('h1');
    document.title = target.dataset.seoTitle || (activeView === 'studio' ? 'Lara Studio — текстильные объекты' : `${title.textContent.trim()} — Lara Studio`);
    document.getElementById('route-status').textContent = activeView === 'studio' ? 'Виртуальная студия' : title.textContent;
    window.scrollTo({top: storedScroll.get(activeView) || 0, behavior: 'instant'});
    if (location.hash) title?.focus({preventScroll:true});
    updateMotion();
  }
  document.body.classList.add('js');
  addEventListener('hashchange', route);
  route();

  // Смена ракурсов не меняет выбранный товар. Видео запускается только пользователем.
  document.querySelectorAll('[data-gallery]').forEach(gallery => {
    const photoButton = gallery.querySelector('.main-photo');
    photoButton.disabled = false;
    const mainImage = photoButton.querySelector('img');
    const video = gallery.querySelector('.gallery-video');
    gallery.querySelectorAll('.gallery-thumb').forEach(thumb => {
      thumb.addEventListener('click', () => {
        gallery.querySelectorAll('.gallery-thumb').forEach(item => item.setAttribute('aria-pressed', String(item === thumb)));
        video.pause();
        const isVideo = !!thumb.dataset.video;
        photoButton.hidden = isVideo; video.hidden = !isVideo;
        if (isVideo) {
          if (video.getAttribute('src') !== thumb.dataset.video) video.src = thumb.dataset.video;
        } else {
          mainImage.src = thumb.dataset.src;
          mainImage.alt = thumb.getAttribute('aria-label');
        }
      });
    });
    photoButton.addEventListener('click', () => {
      dialog.querySelector('img').src = mainImage.src;
      dialog.querySelector('img').alt = mainImage.alt;
      dialog.querySelector('p').textContent = mainImage.alt;
      dialog.showModal();
    });
  });
  dialog.querySelector('.dialog-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => {
    const r=dialog.getBoundingClientRect();
    if (event.target === dialog && (event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)) dialog.close();
  });

  function updateMotion() {
    if (!scene || !motionButton) return;
    const paused=userPaused||reduceMotion.matches;
    const running=!paused&&!document.hidden&&sceneVisible&&activeView==='studio';
    scene.classList.toggle('is-paused',!running);
    scene.classList.toggle('is-still',paused);
    motionButton.hidden=false;
    motionButton.setAttribute('aria-pressed',String(paused));
    motionButton.textContent=reduceMotion.matches?'Движение отключено':userPaused?'Включить движение ▷':'Остановить движение Ⅱ';
    motionButton.disabled=reduceMotion.matches;
  }
  motionButton?.addEventListener('click',()=>{userPaused=!userPaused;updateMotion();});
  reduceMotion.addEventListener('change',updateMotion);
  document.addEventListener('visibilitychange',updateMotion);
  if (scene) new IntersectionObserver(entries=>{sceneVisible=entries[0].isIntersecting;updateMotion();},{threshold:.03}).observe(scene);
})();


/* Lara Studio: Yandex Metrika shopper events (product SKUs only). */
(() => {
  "use strict";
  const counterId = 114109222;
  const product = document.querySelector(".product-view[data-sku]");
  const sku = product?.dataset.sku || "";
  function goal(name, params = {}) {
    if (typeof window.ym !== "function") return;
    window.ym(counterId, "reachGoal", name, sku ? {sku, ...params} : params);
  }

  if (product) goal("product_view");

  document.addEventListener("click", (event) => {
    if (!(event.target instanceof Element)) return;
    const element = event.target.closest("a, button");
    if (!element) return;

    if (element.matches(".order-button")) {
      goal("order_click");
    } else if (element.matches("a[href*='vk.ru/'],a[href*='vk.com/']")) {
      goal("contact_click");
    } else if (element.matches(".gallery-thumb")) {
      if (element.dataset.video) {
        goal("video_selected");
      } else {
        const gallery = element.closest("[data-gallery]");
        const index = gallery ? [...gallery.querySelectorAll(".gallery-thumb")].indexOf(element) + 1 : 0;
        goal("photo_change", {photo: index});
      }
    } else if (element.matches(".main-photo")) {
      goal("photo_zoom");
    } else if (element.matches(".zone, .mobile-categories a, .site-header nav a")) {
      goal("category_open", {section: element.dataset.route || element.getAttribute("href") || ""});
    }
  }, true);

  document.querySelectorAll("video.gallery-video").forEach((video) => {
    video.addEventListener("play", () => goal("video_play"));
  });
})();
