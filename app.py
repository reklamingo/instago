
from flask import Flask, request, render_template_string
from playwright.sync_api import sync_playwright
import random, string, os

app = Flask(__name__)
cekilis_sonuclari = {}

def generate_code(length=6):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def get_commenters(post_url):
    commenters = set()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
            page = context.new_page()
            page.goto(post_url, timeout=90000)
            page.wait_for_timeout(5000)
            if "login" in page.url:
                return ["HATA: Instagram giriş sayfasına yönlendirildi."]
            page.wait_for_selector("article", timeout=15000)
            for _ in range(12):
                page.mouse.wheel(0, 3000)
                page.wait_for_timeout(1000)
            page.wait_for_timeout(3000)
            links = page.query_selector_all("a")
            for link in links:
                try:
                    txt = link.inner_text()
                    if txt.startswith("@") and len(txt) < 50:
                        commenters.add(txt.strip())
                except:
                    continue
            browser.close()
    except Exception as e:
        return [f"HATA: {str(e)}"]
    return list(commenters)

@app.route("/", methods=["GET"])
def index():
    return open("index.html", "r", encoding="utf-8").read()

@app.route("/cekilis", methods=["POST"])
def cekilis():
    link = request.form["link"]
    sayi = int(request.form["sayi"])
    tip = request.form["tip"]
    kullanicilar = get_commenters(link) if tip == "yorum" else ["@like1", "@like2", "@like3"]
    if not kullanicilar:
        return "<p><strong>Hata:</strong> Kullanıcı bulunamadı.</p><a href='/'>Geri dön</a>"
    if any("HATA" in k for k in kullanicilar):
        return f"<p><strong>Hata oluştu:</strong><br>{kullanicilar[0]}</p><a href='/'>Geri dön</a>"
    kazananlar = random.sample(kullanicilar, min(sayi, len(kullanicilar)))
    kod = "cekilis_" + generate_code()
    cekilis_sonuclari[kod] = kazananlar
    html = f"<h2>Kazananlar</h2><ul>" + ''.join(f"<li>{k}</li>" for k in kazananlar) + f"</ul><p><strong>Güvenlik Kodu:</strong> {kod}</p><a href='/'>Yeni çekiliş yap</a>"
    return render_template_string(html)

@app.route("/cekilis-sonucu/<kod>")
def sonuc_kodu_ile(kod):
    kazananlar = cekilis_sonuclari.get(kod, [])
    if kazananlar:
        html = f"<h2>{kod} için kazananlar</h2><ul>" + ''.join(f"<li>{k}</li>" for k in kazananlar) + "</ul>"
    else:
        html = f"<p><strong>{kod}</strong> kodlu bir çekiliş bulunamadı.</p>"
    return render_template_string(html + "<br><a href='/'>Ana sayfaya dön</a>")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
