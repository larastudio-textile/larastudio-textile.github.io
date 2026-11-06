#!/usr/bin/env python3
"""Install public Yandex Metrika counter and Lara Studio event tracking.
Idempotent: repeat execution does not duplicate tracking snippets.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ID = 114109222
TAG = """<!-- Yandex.Metrika counter -->
<script>
(function(m,e,t,r,i,k,a){m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
m[i].l=1*new Date();for(var j=0;j<document.scripts.length;j++){if(document.scripts[j].src===r){return;}}
k=e.createElement(t);a=e.getElementsByTagName(t)[0];k.async=1;k.src=r;a.parentNode.insertBefore(k,a);
})(window,document,"script","https://mc.yandex.ru/metrika/tag.js?id=114109222","ym");
ym(114109222,"init",{ssr:true,webvisor:true,clickmap:true,ecommerce:"dataLayer",accurateTrackBounce:true,trackLinks:true});
</script>
<!-- /Yandex.Metrika counter -->
"""
NOSCRIPT = '<noscript><div><img src="https://mc.yandex.ru/watch/114109222" style="position:absolute;left:-9999px" alt=""></div></noscript>'
EVENTS = r"""

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
"""

def main():
    count = 0
    for file in sorted(ROOT.glob("*.html")):
        html = file.read_text(encoding="utf-8")
        if "mc.yandex.ru/metrika/tag.js?id=114109222" in html:
            continue
        if "<head>" not in html or "<body " not in html:
            raise RuntimeError(f"Unrecognized page layout: {file.name}")
        html = html.replace("<head>", "<head>\n" + TAG, 1)
        html = html.replace("<body ", "<body ", 1)  # Preserve existing attributes.
        start = html.index("<body ")
        end = html.index(">", start)
        html = html[:end + 1] + NOSCRIPT + html[end + 1:]
        file.write_text(html, encoding="utf-8", newline="")
        count += 1

    shared = ROOT / "shared/studio.js"
    source = shared.read_text(encoding="utf-8")
    if "Lara Studio: Yandex Metrika shopper events" not in source:
        shared.write_text(source + EVENTS, encoding="utf-8", newline="")
    total = sum(
        "mc.yandex.ru/metrika/tag.js?id=114109222" in file.read_text(encoding="utf-8")
        for file in ROOT.glob("*.html")
    )
    if total != 47:
        raise RuntimeError(f"Expected Metrika on 47 HTML pages, found {total}")
    print(f"Installed on {total} pages; newly changed {count} pages")

if __name__ == "__main__":
    main()
