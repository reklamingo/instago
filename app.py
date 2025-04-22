
from flask import Flask, request, render_template_string
from playwright.sync_api import sync_playwright
import random
import string
import os

app = Flask(__name__)
cekilis_sonuclari = {}

def generate_code(length=6):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def get_commenters(post_url):
    commenters = set()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            context = browser.new_context()
            page = context.new_page()
            page.goto(post_url, timeout=90000)
            page.wait_for_timeout(5000)

            if "login" in page.url:
                return ["HATA: Instagram giriş sayfasına yönlendirildi (koruma engeli)."]

            page.wait_for_selector("ul", timeout=15000)
            for _ in range(8):
                page.mouse.wheel(0, 2500)
                page.wait_for_timeout(1000)
                try:
                    a_tags = page.query_selector_all("ul li div div div span a")
                    for a in a_tags:
                        try:
                            text = a.inner_text()
                            if text.startswith("@"):
                                commenters.add(text.strip())
                        except:
                            continue
                except:
                    continue
            browser.close()
    except Exception as e:
        return [f"HATA: {str(e)}"]
    return list(commenters)

def get_likers(post_url):
    likers = set()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            context = browser.new_context()
            page = context.new_page()
            page.goto(post_url, timeout=90000)
            page.wait_for_timeout(5000)

            if "login" in page.url:
                return ["HATA: Instagram giriş sayfasına yönlendirildi (koruma engeli)."]

            # Beğeni popup'ını aç
            try:
                page.click("text=n beğenme", timeout=5000)
            except:
                try:
                    page.click("svg[aria-label='Beğeniler'] ~ span", timeout=5000)
                except:
                    return ["HATA: Beğeni popup açılamadı."]

            page.wait_for_timeout(3000)

            for _ in range(10):
                page.mouse.wheel(0, 2500)
                page.wait_for_timeout(1000)
                try:
                    usernames = page.query_selector_all("div[role='dialog'] a")
                    for u in usernames:
                        try:
                            text = u.inner_text()
                            if text.startswith("@"):
                                likers.add(text.strip())
                        except:
                            continue
                except:
                    continue
            browser.close()
    except Exception as e:
        return [f"HATA: {str(e)}"]
    return list(likers)

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
            kullanicilar = get_likers(link)

        if not kullanicilar:
            return "<p><strong>Hata:</strong> Kullanıcı bulunamadı.</p><a href='/'>Geri dön</a>"

        if any("HATA" in k for k in kullanicilar):
            return f"<p><strong>Hata oluştu:</strong><br>{kullanicilar[0]}</p><a href='/'>Geri dön</a>"

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
