"""
Scrapers de noticias para los 18 ministerios colombianos.
Cada scraper retorna noticias del día actual con estructura:
  [{"titulo": str, "url": str, "ministerio": str, "fecha": str}]
"""

import re
import urllib3
from datetime import date, datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Dict

import requests
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

TODAY = date.today()

_MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}

# ─────────────────────────────────────────────────────────────────────────────
# Utilidades comunes
# ─────────────────────────────────────────────────────────────────────────────

def _get(url: str, verify=True, timeout=15) -> Optional[requests.Response]:
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, verify=verify,
                         allow_redirects=True)
        r.raise_for_status()
        return r
    except Exception as e:
        print(f"  [!] {url[:70]} → {e}")
        return None


def _soup(url: str, verify=True) -> Optional[BeautifulSoup]:
    r = _get(url, verify=verify)
    # Usar r.content (bytes) para que BeautifulSoup detecte el charset del HTML
    # en lugar de confiar en el header HTTP (a veces incorrecto).
    return BeautifulSoup(r.content, "html.parser") if r else None


def _parse_date(s: str) -> Optional[date]:
    """Convierte cadenas de fecha en múltiples formatos a un objeto date."""
    if not s:
        return None
    s = s.strip().rstrip(".")

    # YYYY-MM-DD (ISO o dentro de datetime string)
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass

    # iso8601-YYYYMMDDTHHMMSS  (clase CSS)
    m = re.search(r"iso8601-(\d{4})(\d{2})(\d{2})", s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass

    # dd/mm/yyyy
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            pass

    # dd de MONTH de yyyy  o  dd de MONTH yyyy
    m = re.search(r"(\d{1,2})\s+de\s+(\w+?)(?:\s+de)?\s+(\d{4})", s, re.I)
    if m:
        month = _MESES.get(m.group(2).lower())
        if month:
            try:
                return date(int(m.group(3)), month, int(m.group(1)))
            except ValueError:
                pass

    # dd MONTH yyyy  (sin "de")
    m = re.search(r"(\d{1,2})\s+(\w+)\s+(\d{4})", s, re.I)
    if m:
        month = _MESES.get(m.group(2).lower())
        if month:
            try:
                return date(int(m.group(3)), month, int(m.group(1)))
            except ValueError:
                pass

    return None


def _fmt_datetime(s: str) -> str:
    """Devuelve dd/mm/yyyy HH:MM a. m./p. m. — formato unificado con Scrapermedios."""
    d = _parse_date(s)
    if not d:
        return ""
    base = f"{d.day:02d}/{d.month:02d}/{d.year}"

    m = re.search(r"(\d{1,2}):(\d{2})(?::(\d{2}))?(?:\s*(am|pm))?", s, re.I)
    if m:
        hh, mm = int(m.group(1)), int(m.group(2))
        if m.group(4) and m.group(4).lower() == "pm" and hh < 12:
            hh += 12
        elif m.group(4) and m.group(4).lower() == "am" and hh == 12:
            hh = 0
        h12 = hh % 12 or 12
        mer = "a. m." if hh < 12 else "p. m."
        return f"{base} {h12:02d}:{mm:02d} {mer}"
    return base


def _is_today(s: str) -> bool:
    return _parse_date(s) == TODAY


def _abs_url(href: str, base: str) -> str:
    if not href:
        return ""
    if href.startswith("http"):
        return href
    if href.startswith("//"):
        return "https:" + href
    return base.rstrip("/") + "/" + href.lstrip("/")


def _item(title: str, url: str, ministerio: str, fecha_str: str) -> dict:
    d = _parse_date(fecha_str)
    _dt_val = datetime(d.year, d.month, d.day) if d else datetime.min
    return {
        "titulo": title.strip(),
        "url": url,
        "ministerio": ministerio,
        "fecha": _fmt_datetime(fecha_str),
        "_dt": _dt_val,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 1. Ministerio de Igualdad y Equidad
# ─────────────────────────────────────────────────────────────────────────────
def scrape_minigualdad() -> List[Dict]:
    """https://www.minigualdadyequidad.gov.co/noticias  — Liferay"""
    nombre = "Ministerio de Igualdad y Equidad"
    base = "https://www.minigualdadyequidad.gov.co"
    soup = _soup(f"{base}/noticias")
    if not soup:
        return []

    results = []
    for h2 in soup.select("h2"):
        title = h2.get_text(strip=True)
        if not title or len(title) < 10:
            continue
        # Buscar el <small> con fecha en los ancestros
        container = h2.parent
        small = None
        for _ in range(6):
            if not container:
                break
            small = container.find("small")
            if small:
                break
            container = container.parent

        if not small or not _is_today(small.get_text(strip=True)):
            continue

        link = h2.find("a") or (
            container.find("a", href=lambda h: h and "/-/" in h) if container else None
        )
        href = _abs_url(link.get("href", "") if link else "", base)
        fecha = small.get_text(strip=True)
        results.append(_item(title, href, nombre, fecha))
    return results


# ─────────────────────────────────────────────────────────────────────────────
# 2. Ministerio del Interior
# ─────────────────────────────────────────────────────────────────────────────
def scrape_mininterior() -> List[Dict]:
    """https://www.mininterior.gov.co/noticias/  — WordPress REST API"""
    nombre = "Ministerio del Interior"
    r = _get(
        "https://www.mininterior.gov.co/wp-json/wp/v2/posts"
        "?per_page=20&orderby=date&order=desc"
    )
    if not r:
        return []
    results = []
    for p in r.json():
        dt = p.get("date", "")
        if _parse_date(dt) != TODAY:
            continue
        title = BeautifulSoup(p["title"]["rendered"], "html.parser").get_text()
        results.append(_item(title, p.get("link", ""), nombre, dt))
    return results


# ─────────────────────────────────────────────────────────────────────────────
# 3. Cancillería
# ─────────────────────────────────────────────────────────────────────────────
def scrape_cancilleria() -> List[Dict]:
    """https://www.cancilleria.gov.co/newsroom/news  — Drupal views"""
    nombre = "Ministerio de Relaciones Exteriores (Cancillería)"
    base = "https://www.cancilleria.gov.co"
    soup = _soup(f"{base}/newsroom/news")
    if not soup:
        return []

    results = []
    for row in soup.select(".contextual-region.views-row, .views-row"):
        time_tag = row.select_one("time[datetime]")
        if not time_tag or not _is_today(time_tag.get("datetime", "")):
            continue
        a = row.select_one("h2 a, h3 a, .views-field-title a")
        if not a:
            continue
        href = _abs_url(a.get("href", ""), base)
        fecha = time_tag.get("datetime", "")
        results.append(_item(a.get_text(strip=True), href, nombre, fecha))
    return results


# ─────────────────────────────────────────────────────────────────────────────
# 4. Ministerio de Hacienda  (protegido por bot — no disponible)
# ─────────────────────────────────────────────────────────────────────────────
def scrape_minhacienda() -> List[Dict]:
    """https://www.minhacienda.gov.co/prensa/noticias  — Bot Radware, no accesible"""
    print("  [i] Minhacienda: protegido por anti-bot (Radware), sin resultados.")
    return []


# ─────────────────────────────────────────────────────────────────────────────
# 5. Ministerio de Justicia  (SharePoint JS — no disponible)
# ─────────────────────────────────────────────────────────────────────────────
def scrape_minjusticia() -> List[Dict]:
    """https://www.minjusticia.gov.co/  — SharePoint cargado con JS"""
    print("  [i] Minjusticia: SharePoint con contenido dinámico (JS), sin resultados.")
    return []


# ─────────────────────────────────────────────────────────────────────────────
# 6. Ministerio de Defensa  (requiere JavaScript)
# ─────────────────────────────────────────────────────────────────────────────
def scrape_mindefensa() -> List[Dict]:
    """https://www.mindefensa.gov.co/prensa/noticias  — Requiere JavaScript"""
    print("  [i] Mindefensa: requiere JavaScript, sin resultados.")
    return []


# ─────────────────────────────────────────────────────────────────────────────
# 7. Ministerio de Salud  (SharePoint JS — no disponible)
# ─────────────────────────────────────────────────────────────────────────────
def scrape_minsalud() -> List[Dict]:
    """https://www.minsalud.gov.co/Comunicaciones/Paginas/noticias.aspx  — SharePoint JS"""
    print("  [i] Minsalud: SharePoint con contenido dinámico, sin resultados.")
    return []


# ─────────────────────────────────────────────────────────────────────────────
# 8. Ministerio del Trabajo  (Liferay — fecha en artículo)
# ─────────────────────────────────────────────────────────────────────────────
def _mintrabajo_fecha(url: str) -> str:
    """Obtiene 'Fecha de publicación: YYYY-MM-DD' desde la página del artículo."""
    soup = _soup(url)
    if not soup:
        return ""
    m = re.search(r"Fecha de publicaci[oó]n:\s*(\d{4}-\d{2}-\d{2})", soup.get_text())
    return m.group(1) if m else ""


def scrape_mintrabajo() -> List[Dict]:
    """https://www.mintrabajo.gov.co/web/guest/prensa/comunicados  — Liferay"""
    nombre = "Ministerio del Trabajo"
    url = "https://www.mintrabajo.gov.co/web/guest/prensa/comunicados"
    soup = _soup(url)
    if not soup:
        return []

    boxes = soup.select(".BoxNewsMintraHome")[:10]
    if not boxes:
        return []

    # Obtener fechas concurrentemente
    links_map = {}
    for box in boxes:
        a = box.select_one(".TitleNewsMintra a, .news-title a, h2 a, h3 a")
        if a:
            href = a.get("href", "")
            links_map[href] = a.get_text(strip=True)

    results = []
    with ThreadPoolExecutor(max_workers=5) as ex:
        future_to_href = {ex.submit(_mintrabajo_fecha, href): href for href in links_map}
        for future in as_completed(future_to_href):
            href = future_to_href[future]
            fecha = future.result()
            if _is_today(fecha):
                results.append(_item(links_map[href], href, nombre, fecha))
    return results


# ─────────────────────────────────────────────────────────────────────────────
# 9. Ministerio de Energía
# ─────────────────────────────────────────────────────────────────────────────
def scrape_minenergia() -> List[Dict]:
    """https://www.minenergia.gov.co/es/sala-de-prensa/  — CMS propio"""
    nombre = "Ministerio de Minas y Energía"
    base = "https://www.minenergia.gov.co"
    soup = _soup(f"{base}/es/sala-de-prensa/")
    if not soup:
        return []

    results = []
    seen = set()

    def _add(title, href, fecha_str):
        href_full = _abs_url(href, base)
        if href_full not in seen:
            seen.add(href_full)
            results.append(_item(title, href_full, nombre, fecha_str))

    # Noticia principal
    main = soup.select_one(".main-news-container")
    if main:
        subtitle = main.select_one(".main-news-subtitle")
        if subtitle and _is_today(subtitle.get_text(strip=True)):
            a = main.select_one("a.link-main-news")
            title_tag = main.select_one(".main-news-title")
            if a and title_tag:
                _add(title_tag.get_text(strip=True), a.get("href", ""),
                     subtitle.get_text(strip=True))

    # Lista de noticias
    for item in soup.select(".news-list"):
        subtitle = item.select_one(".news-list-subtitle")
        if not subtitle or not _is_today(subtitle.get_text(strip=True)):
            continue
        title_tag = item.select_one(".news-list-title")
        parent_a = item.find_parent("a") or item.select_one("a")
        href = parent_a.get("href", "") if parent_a else ""
        if title_tag:
            _add(title_tag.get_text(strip=True), href, subtitle.get_text(strip=True))
    return results


# ─────────────────────────────────────────────────────────────────────────────
# 10. Ministerio de Comercio, Industria y Turismo
# ─────────────────────────────────────────────────────────────────────────────
def scrape_mincit() -> List[Dict]:
    """https://www.mincit.gov.co/prensa/noticias  — tarjeta-govco con span de fecha y h3"""
    nombre = "Ministerio de Comercio, Industria y Turismo"
    base = "https://www.mincit.gov.co"
    soup = _soup(f"{base}/prensa/noticias")
    if not soup:
        return []

    results = []
    seen = set()
    for a in soup.select('a.tarjeta-govco[href*="noticias/"]'):
        href = a.get("href", "")
        if not href or href in seen or href == "#":
            continue
        seen.add(href)
        span_fecha = a.select_one("span")
        h3_title = a.select_one("h3")
        if not span_fecha or not h3_title:
            continue
        fecha_str = span_fecha.get_text(strip=True)   # "21 mayo 2026"
        if not _is_today(fecha_str):
            continue
        href_full = _abs_url(href, base)
        results.append(_item(h3_title.get_text(strip=True), href_full, nombre, fecha_str))
    return results


# ─────────────────────────────────────────────────────────────────────────────
# 11. Ministerio de Educación Nacional
# ─────────────────────────────────────────────────────────────────────────────
def scrape_mineducacion() -> List[Dict]:
    """https://www.mineducacion.gov.co/portal/salaprensa/  — CMS propio (recuadros)"""
    nombre = "Ministerio de Educación Nacional"
    base = "https://www.mineducacion.gov.co"
    soup = _soup(f"{base}/portal/salaprensa/")
    if not soup:
        return []

    results = []
    for rec in soup.select(".recuadro"):
        fecha_tag = rec.select_one(".fecha")
        if not fecha_tag:
            continue
        # Intentar con el atributo de clase iso8601-*
        iso_class = next((c for c in fecha_tag.get("class", []) if "iso8601" in c), None)
        fecha_str = iso_class or fecha_tag.get_text(strip=True)
        if not _is_today(fecha_str):
            continue
        a = rec.select_one(".titulo a, a[href]")
        if not a:
            continue
        href = _abs_url(a.get("href", ""), base)
        results.append(_item(a.get_text(strip=True), href, nombre, fecha_str))
    return results


# ─────────────────────────────────────────────────────────────────────────────
# 12. Ministerio de Ambiente y Desarrollo Sostenible
# ─────────────────────────────────────────────────────────────────────────────
def scrape_minambiente() -> List[Dict]:
    """https://www.minambiente.gov.co/sala-de-prensa/  — WordPress RSS"""
    nombre = "Ministerio de Ambiente y Desarrollo Sostenible"
    r = _get("https://www.minambiente.gov.co/feed/")
    if not r:
        return []

    soup = BeautifulSoup(r.text, "lxml-xml")
    results = []
    for item in soup.find_all("item"):
        pub = item.find("pubDate")
        if not pub or not _is_today(pub.get_text(strip=True)):
            continue
        title = item.find("title")
        link = item.find("link")
        if not title:
            continue
        # En lxml-xml, <link> puede ser un elemento vacío con el URL como next_sibling
        if link:
            href = (link.get_text(strip=True) or
                    str(link.next_sibling or "").strip())
        else:
            href = ""
        results.append(_item(
            title.get_text(strip=True),
            href,
            nombre,
            pub.get_text(strip=True)
        ))
    return results


# ─────────────────────────────────────────────────────────────────────────────
# 13. Ministerio de Vivienda  (Drupal — fecha en artículo)
# ─────────────────────────────────────────────────────────────────────────────
def _minvivienda_fecha(url: str) -> str:
    soup = _soup(url)
    if not soup:
        return ""
    # Drupal: tiempo en article header o field--name-created
    t = soup.select_one("time[datetime], .field--name-created time, .date-display-single")
    if t:
        return t.get("datetime", t.get_text(strip=True))
    # Fallback: primer texto con fecha en la página
    m = re.search(r"\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}", soup.get_text())
    return m.group(0) if m else ""


def scrape_minvivienda() -> List[Dict]:
    """https://minvivienda.gov.co/comunicaciones  — Drupal"""
    nombre = "Ministerio de Vivienda, Ciudad y Territorio"
    base = "https://minvivienda.gov.co"
    soup = _soup(f"{base}/comunicaciones")
    if not soup:
        return []

    links_map = {}
    for card in soup.select(".card-listing"):
        a = card.select_one('a[href*="sala-de-prensa"]')
        if a:
            href = _abs_url(a.get("href", ""), base)
            title = a.get_text(strip=True)
            if href not in links_map:
                links_map[href] = title

    results = []
    with ThreadPoolExecutor(max_workers=5) as ex:
        future_to_href = {ex.submit(_minvivienda_fecha, href): href
                         for href in list(links_map)[:10]}
        for future in as_completed(future_to_href):
            href = future_to_href[future]
            fecha = future.result()
            if _is_today(fecha):
                results.append(_item(links_map[href], href, nombre, fecha))
    return results


# ─────────────────────────────────────────────────────────────────────────────
# 14. MinTIC
# ─────────────────────────────────────────────────────────────────────────────
def scrape_mintic() -> List[Dict]:
    """https://www.mintic.gov.co/portal/inicio/Sala-de-prensa/Noticias/  — CMS propio"""
    nombre = "Ministerio de Tecnologías de la Información y las Comunicaciones"
    base = "https://www.mintic.gov.co"
    soup = _soup(f"{base}/portal/inicio/Sala-de-prensa/Noticias/")
    if not soup:
        return []

    results = []
    for rec in soup.select(".recuadro"):
        fecha_tag = rec.select_one(".fecha")
        if not fecha_tag:
            continue
        iso_class = next((c for c in fecha_tag.get("class", []) if "iso8601" in c), None)
        fecha_str = iso_class or fecha_tag.get_text(strip=True)
        if not _is_today(fecha_str):
            continue
        a = rec.select_one(".titulo a, a[href]")
        if not a:
            continue
        href = _abs_url(a.get("href", ""), base)
        results.append(_item(a.get_text(strip=True), href, nombre, fecha_str))
    return results


# ─────────────────────────────────────────────────────────────────────────────
# 15. Ministerio de Transporte  (CMS propio — fecha en artículo)
# ─────────────────────────────────────────────────────────────────────────────
def _mintransporte_fecha(url: str) -> str:
    soup = _soup(url)
    if not soup:
        return ""
    pub = soup.select_one(".pub-date-publication")
    if pub:
        m = re.search(r"\d{1,2}/\d{1,2}/\d{4}", pub.get_text())
        return m.group(0) if m else ""
    return ""


def scrape_mintransporte() -> List[Dict]:
    """https://mintransporte.gov.co/publicaciones/noticias/?tema=323  — CMS propio"""
    nombre = "Ministerio de Transporte"
    base = "https://mintransporte.gov.co"
    soup = _soup(f"{base}/publicaciones/noticias/?tema=323")
    if not soup:
        return []

    links_map = {}
    for pc in soup.select(".post-content"):
        a = pc.select_one("h2 a, h3 a")
        if a:
            href = _abs_url(a.get("href", ""), base)
            if href not in links_map:
                links_map[href] = a.get_text(strip=True)

    results = []
    with ThreadPoolExecutor(max_workers=5) as ex:
        future_to_href = {ex.submit(_mintransporte_fecha, href): href
                         for href in list(links_map)[:10]}
        for future in as_completed(future_to_href):
            href = future_to_href[future]
            fecha = future.result()
            if _is_today(fecha):
                results.append(_item(links_map[href], href, nombre, fecha))
    return results


# ─────────────────────────────────────────────────────────────────────────────
# 16. Ministerio de Cultura  (SharePoint con autenticación)
# ─────────────────────────────────────────────────────────────────────────────
def scrape_mincultura() -> List[Dict]:
    """https://www.mincultura.gov.co/noticias/Paginas/default.aspx  — SharePoint autenticado"""
    print("  [i] Mincultura: SharePoint con muro de autenticación, sin resultados.")
    return []


# ─────────────────────────────────────────────────────────────────────────────
# 17. Ministerio de Ciencias  (Drupal)
# ─────────────────────────────────────────────────────────────────────────────
def scrape_minciencias() -> List[Dict]:
    """https://minciencias.gov.co/sala_de_prensa  — Drupal"""
    nombre = "Ministerio de Ciencia, Tecnología e Innovación"
    base = "https://minciencias.gov.co"
    soup = _soup(f"{base}/sala_de_prensa")
    if not soup:
        return []

    results = []
    for ds in soup.select("span.date-display-single"):
        # El atributo content tiene el ISO datetime
        iso = ds.get("content", "")
        fecha_str = iso or ds.get_text(strip=True)
        if not _is_today(fecha_str):
            continue
        # Subir al td.col-1 / views-row que contiene el título
        row = ds
        for _ in range(6):
            row = row.parent if row else row
            if row and "views-row" in " ".join(row.get("class", [])):
                break
            if row and row.name == "td":
                break
        if not row:
            continue
        a = row.select_one(".views-field-title a, h2 a, h3 a")
        if not a:
            continue
        href = _abs_url(a.get("href", ""), base)
        results.append(_item(a.get_text(strip=True), href, nombre, fecha_str))
    return results


# ─────────────────────────────────────────────────────────────────────────────
# 18. Ministerio de Deporte
# ─────────────────────────────────────────────────────────────────────────────
def scrape_mindeporte() -> List[Dict]:
    """https://www.mindeporte.gov.co/sala-de-prensa/comunicados  — CMS propio"""
    nombre = "Ministerio del Deporte"
    base = "https://www.mindeporte.gov.co"
    soup = _soup(f"{base}/sala-de-prensa/comunicados")
    if not soup:
        return []

    results = []
    for art in soup.select("article"):
        fecha_tag = art.select_one("p.text-xs, .text-gray-400, p.mt-1")
        if not fecha_tag or not _is_today(fecha_tag.get_text(strip=True)):
            continue
        a = art.select_one("a[href]")
        if not a:
            continue
        href = _abs_url(a.get("href", ""), base)
        title_tag = art.select_one("p.font-semibold, p.text-base, p.leading-tight")
        title = title_tag.get_text(strip=True) if title_tag else a.get_text(strip=True)
        results.append(_item(title, href, nombre, fecha_tag.get_text(strip=True)))
    return results


# ─────────────────────────────────────────────────────────────────────────────
# 19. Fiscalía General de la Nación
# ─────────────────────────────────────────────────────────────────────────────
def scrape_fiscalia() -> List[Dict]:
    """https://www.fiscalia.gov.co/colombia/noticias/  — WordPress / Newspaper theme"""
    nombre = "Fiscalía General de la Nación"
    base = "https://www.fiscalia.gov.co/colombia"
    soup = _soup(f"{base}/noticias/")
    if not soup:
        return []

    results = []
    for card in soup.select(".td_module_wrap"):
        time_tag = card.select_one("time.entry-date[datetime]")
        if not time_tag or not _is_today(time_tag.get("datetime", "")):
            continue
        a = card.select_one("h3.entry-title a, h2.entry-title a")
        if not a:
            continue
        href = a.get("href", "")
        results.append(_item(a.get_text(strip=True), href, nombre,
                             time_tag.get("datetime", "")))
    return results


# ─────────────────────────────────────────────────────────────────────────────
# 20. Procuraduría General de la Nación
# ─────────────────────────────────────────────────────────────────────────────
def scrape_procuraduria() -> List[Dict]:
    """https://www.procuraduria.gov.co/Pages/Noticias.aspx — SharePoint Pages list via RenderListDataAsStream"""
    nombre = "Procuraduría General de la Nación"
    base = "https://www.procuraduria.gov.co"
    list_guid = "23026bcd-927a-4f42-b257-409a76f78bae"
    api_url = f"{base}/_api/web/lists('{list_guid}')/RenderListDataAsStream"

    view_xml = (
        "<View><Query><OrderBy>"
        "<FieldRef Name=\"FechaNoticia\" Ascending=\"FALSE\"/>"
        "</OrderBy></Query><RowLimit>30</RowLimit></View>"
    )
    try:
        r = requests.post(
            api_url,
            headers={**HEADERS,
                     "Accept": "application/json;odata=nometadata",
                     "Content-Type": "application/json;odata=nometadata"},
            json={"parameters": {"RenderOptions": 2, "ViewXml": view_xml}},
            timeout=20,
            verify=True,
        )
        r.raise_for_status()
    except Exception as e:
        print(f"  [!] Procuraduría → {e}")
        return []

    results = []
    for row in r.json().get("Row", []):
        fecha_str = row.get("FechaNoticia", "")
        if not fecha_str or not _is_today(fecha_str):
            continue
        title = row.get("Title", "").strip()
        href = row.get("EncodedAbsUrl", "")
        if not title or not href:
            continue
        results.append(_item(title, href, nombre, fecha_str))
    return results


# ─────────────────────────────────────────────────────────────────────────────
# 21. Superintendencia Nacional de Salud
# ─────────────────────────────────────────────────────────────────────────────
def scrape_supersalud() -> List[Dict]:
    """https://www.supersalud.gov.co/es-co/noticias — SharePoint Search API (ContentType:Noticia)"""
    nombre = "Superintendencia Nacional de Salud"
    api_url = (
        "https://www.supersalud.gov.co/_api/search/query"
        "?querytext='ContentType:Noticia'"
        "&selectproperties='Title,Path,Write'"
        "&sortlist='Write:descending'"
        "&rowlimit=50"
    )
    try:
        r = requests.get(
            api_url,
            headers={**HEADERS, "Accept": "application/json;odata=nometadata"},
            timeout=20,
            verify=True,
        )
        r.raise_for_status()
    except Exception as e:
        print(f"  [!] SuperSalud → {e}")
        return []

    rows = (r.json()
            .get("PrimaryQueryResult", {})
            .get("RelevantResults", {})
            .get("Table", {})
            .get("Rows", []))

    results = []
    for row in rows:
        cells = {c["Key"]: c["Value"] for c in row.get("Cells", [])}
        write = cells.get("Write", "")
        if not write or not _is_today(write):
            continue
        title = cells.get("Title", "").strip()
        href = cells.get("Path", "")
        if not title or not href:
            continue
        results.append(_item(title, href, nombre, write))
    return results


# ─────────────────────────────────────────────────────────────────────────────
# Registro de todos los scrapers
# ─────────────────────────────────────────────────────────────────────────────
SCRAPERS = [
    ("MinIgualdad",   scrape_minigualdad),
    ("MinInterior",   scrape_mininterior),
    ("Cancillería",   scrape_cancilleria),
    ("MinHacienda",   scrape_minhacienda),
    ("MinJusticia",   scrape_minjusticia),
    ("MinDefensa",    scrape_mindefensa),
    ("MinSalud",      scrape_minsalud),
    ("MinTrabajo",    scrape_mintrabajo),
    ("MinEnergía",    scrape_minenergia),
    ("MinCIT",        scrape_mincit),
    ("MinEducación",  scrape_mineducacion),
    ("MinAmbiente",   scrape_minambiente),
    ("MinVivienda",   scrape_minvivienda),
    ("MinTIC",        scrape_mintic),
    ("MinTransporte", scrape_mintransporte),
    ("MinCultura",    scrape_mincultura),
    ("MinCiencias",   scrape_minciencias),
    ("MinDeporte",    scrape_mindeporte),
    ("Fiscalía",      scrape_fiscalia),
    ("Procuraduría",  scrape_procuraduria),
    ("SuperSalud",    scrape_supersalud),
]
