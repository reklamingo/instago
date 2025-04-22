
from flask import Flask, request, render_template_string
from playwright.sync_api import sync_playwright
import random
import re

app = Flask(__name__)

def get_commenters(post_url):
    commenters = set()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(post_url, timeout=60000)

        page.wait_for_selector("ul > li")
        last_height = 0
        scroll_tries = 0

        while scroll_tries < 10:
            page.mouse.wheel(0, 5000)
            page.wait_for_timeout(2000)
            new_comments = page.query_selector_all("ul > li > div > div > div > span > a")
            for c in new_comments:
                username = c.inner_text()
                if username.startswith("@"):
                    commenters.add(username)
            scroll_tries += 1

        browser.close()
    return list(commenters)

@app.route("/", methods=["GET"])
def index():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.route("/cekilis", methods=["POST"])
def cekilis():
    link = request.form["link"]
    sayi = int(request.form["sayi"])
    tip = request.form["tip"]

    try:
        if tip == "yorum":
            kullanicilar = get_commenters(link)
        else:
            kullanicilar = ["@like1", "@like2", "@like3"]  # Beğeni çekme zor olduğu için örnek verildi

        if not kullanicilar:
            return "Kullanıcı bulunamadı. Gönderi herkese açık mı veya yorum var mı kontrol edin."

        kazananlar = random.sample(kullanicilar, min(sayi, len(kullanicilar)))
        sonuc_html = "<h2>Kazananlar</h2><ul>"
        for k in kazananlar:
            sonuc_html += f"<li>{k}</li>"
        sonuc_html += "</ul><a href='/'>Yeni çekiliş yap</a>"

        return render_template_string(sonuc_html)

    except Exception as e:
        return f"Hata oluştu: {str(e)}"

if __name__ == "__main__":
    import os
port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port, debug=True)

