#!/usr/bin/env python3
"""
Minecraft Whitelist Otomatik Güncelleme - Pterodactyl API Versiyonu
1. Web sayfasından kullanıcı adlarını çeker
2. Pterodactyl API ile sunucu konsoluna whitelist komutları gönderir
"""

import os, re, time, logging, requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ============================================================
# AYARLAR (GitHub Secrets'tan okunur)
# ============================================================
ADMIN_URL    = os.environ.get("ADMIN_URL",    "https://vioxmc.wxnw.net/admin.php?sifre=@q@@qqq@q@q@q_*12")
PANEL_URL    = os.environ.get("PANEL_URL",    "https://panel.tickhosting.com")
API_KEY      = os.environ.get("API_KEY",      "")   # GitHub Secret'tan gelir
SERVER_ID    = os.environ.get("SERVER_ID",    "acbce3e2")

# ============================================================
FILITRE = {
    "div","span","html","head","body","form","input","table","tbody","thead",
    "class","style","script","href","meta","link","type","name","value",
    "action","method","button","admin","php","true","false","null","none",
    "login","password","username","submit","reset","get","post","http",
    "https","www","com","net","org","the","and","for","with","from","this",
    "that","are","was","not","all","can","her","his","has","had","but",
    "one","you","nav","header","footer","main","section","article","aside",
    "img","src","alt","width","height","color","font","size","text","data",
    "list","item","row","col","btn","icon","page","site","web","app","api",
    "var","let","const","function","return","window","document","onclick",
    "onload","jquery","bootstrap","charset","utf","viewport","content",
    "index","cache","reload","refresh","server","player","players","info",
    "error","success","warning","message","result","response","request",
    "vioxmc","wxnw","sifre","minecraft","survival","whitelist","viox"
}

def kullanicilari_cek() -> list[str]:
    """Web sayfasından Minecraft kullanıcı adlarını çeker."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    }
    log.info("Sayfa çekiliyor...")
    resp = requests.get(ADMIN_URL, headers=headers, timeout=20)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script","style","head","nav","footer"]):
        tag.decompose()

    metin = soup.get_text(" ")
    bulunanlar = re.findall(r'\b([A-Za-z0-9_]{3,16})\b', metin)
    temiz = sorted({
        u for u in bulunanlar
        if u.lower() not in FILITRE
        and not u.isdigit()
        and not u.isupper()
        and len(u) >= 3
    })
    log.info(f"{len(temiz)} kullanıcı bulundu: {temiz}")
    return temiz


def konsol_komutu_gonder(komut: str) -> bool:
    """Pterodactyl API ile sunucu konsoluna komut gönderir."""
    url = f"{PANEL_URL}/api/client/servers/{SERVER_ID}/command"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    resp = requests.post(url, json={"command": komut}, headers=headers, timeout=10)
    if resp.status_code == 204:
        log.info(f"  OK: {komut}")
        return True
    else:
        log.error(f"  HATA ({resp.status_code}): {komut} -> {resp.text}")
        return False


def whitelist_guncelle(kullanicilar: list[str]):
    """Pterodactyl API üzerinden whitelist komutlarını gönderir."""
    if not kullanicilar:
        log.warning("Eklenecek kullanıcı yok!")
        return

    log.info(f"Pterodactyl API ile komutlar gönderiliyor...")

    # Whitelist'i aç
    konsol_komutu_gonder("whitelist on")
    time.sleep(0.5)

    # Her kullanıcıyı ekle
    eklendi = 0
    for oyuncu in kullanicilar:
        basarili = konsol_komutu_gonder(f"whitelist add {oyuncu}")
        if basarili:
            eklendi += 1
        time.sleep(0.3)  # Sunucuya yük bindirme

    # Whitelist'i yenile
    time.sleep(0.5)
    konsol_komutu_gonder("whitelist reload")

    log.info("=" * 40)
    log.info(f"TAMAMLANDI! {eklendi}/{len(kullanicilar)} oyuncu eklendi.")
    log.info("=" * 40)


if __name__ == "__main__":
    log.info("Minecraft Whitelist Güncelleme Başladı")
    kullanicilar = kullanicilari_cek()
    whitelist_guncelle(kullanicilar)
