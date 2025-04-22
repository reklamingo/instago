
from flask import Flask, request, render_template_string
from playwright.sync_api import sync_playwright
import random
import re
import os
import string

app = Flask(__name__)
cekilis_sonuclari = {}

def generate_code(length=6):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def get_commenters(post_url):
    commenters = set()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(post_url, timeout=60000)

        page.wait_for_selector("ul > li")
        for _ in range(5):
            page.mouse.wheel(0, 4000)
            page.wait_for_timeout(1500)
            links = page.query_selector_all("ul > li > div > div > div > span > a")
            for l in links:
                username = l.inner_text()
                if username and username.startswith("@"):
                    commenters.add(username)
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
            kullanicilar = ["@like1", "@like2", "@like3", "@like4", "@like5"]  # Beğeni scraping sonra yapılacak

        if not kullanicilar:
            return "Kullanıcı bulunamadı. Gönderi herkese açık mı veya yorum var mı kontrol edin."

        kazananlar = random.sample(kullanicilar, min(sayi, len(kullanicilar)))
        kod = "cekilis_" + generate_code()
        cekilis_sonuclari[kod] = kazananlar

        sonuc_html = f"<h2>Kazananlar</h2><ul>"
        for k in kazananlar:
            sonuc_html += f"<li>{k}</li>"
        sonuc_html += f"</ul><p><strong>Güvenlik Kodu:</strong> {kod}</p>"
        sonuc_html += "<a href='/'>Yeni çekiliş yap</a>"

        return render_template_string(sonuc_html)

    except Exception as e:
        return f"Hata oluştu: {str(e)}"

@app.route("/cekilis-sonucu/<kod>", methods=["GET"])
def sonuc_kodu_ile(kod):
    kazananlar = cekilis_sonuclari.get(kod)
    if kazananlar:
        html = f"<h2>{kod} için kazananlar</h2><ul>"
        for k in kazananlar:
            html += f"<li>{k}</li>"
        html += "</ul>"
    else:
        html = f"<p><strong>{kod}</strong> kodlu bir çekiliş bulunamadı.</p>"
    html += "<br><a href='/'>Ana sayfaya dön</a>"
    return render_template_string(html)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
