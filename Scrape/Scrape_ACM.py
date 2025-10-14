# Scrape_ACM.py
from playwright.sync_api import sync_playwright
import os
import re
import time
import random
from datetime import datetime

def scrape_acm(
    query="security systems",
    output_path=os.path.join("Data", "resultados_ACM.bib"),
    user_data_dir="session_acm",
    start_year=2018,
    end_year=datetime.now().year,
    results_per_page=50,
    max_pages_per_year=20,   # 20 páginas * 50 = 1000 por año máximo
    headless=False
):
    """
    Scraper para ACM via portal de la biblioteca (persistente).
    - Recomendado: Ejecutar una vez, resolver manualmente los CAPTCHAs / Cloudflare
      cuando aparezcan en la ventana abierta. Después la sesión se mantiene.
    - Dividimos la búsqueda por año para conseguir más resultados (evita límite por búsqueda).
    """

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    os.makedirs(user_data_dir, exist_ok=True)
    total_written = 0

    # pequeño helper "humano"
    def human_pause(min_s=0.6, max_s=1.6):
        time.sleep(random.uniform(min_s, max_s))

    with sync_playwright() as p:
        # Lanzamos contexto persistente (mantiene cookies / sesión)
        browser_context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ],
            viewport={"width": 1280, "height": 800}
        )

        # Creamos una página nueva
        page = browser_context.new_page()

        # Small stealth tweaks before any page script runs
        page.add_init_script(
            """() => {
                Object.defineProperty(navigator, 'webdriver', {get: () => false});
                Object.defineProperty(navigator, 'languages', {get: () => ['es-ES','es']});
                Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
                const original = window.navigator.permissions && window.navigator.permissions.query;
                if (original) {
                  window.navigator.permissions.query = (p) => (p && p.name === 'notifications') ? Promise.resolve({state: Notification.permission}) : original(p);
                }
            }"""
        )

        # Cabeceras extra para parecer navegador real
        page.set_extra_http_headers({"Accept-Language": "es-ES,es;q=0.9,en;q=0.8"})

        # Función para detectar mensajes de Cloudflare / verificación humana
        def wait_if_human_check():
            # Intenta detectar textos comunes o elementos de verificación
            try:
                # Ajusta el selector/texto si tu portal muestra otro mensaje
                if page.locator("text=Verificar que usted es un ser humano").is_visible(timeout=3000):
                    print("⚠️ Cloudflare / verificación humana detectada. Resuélvela en el navegador.")
                    input("Cuando termines de resolver la verificación, presiona ENTER aquí para continuar...")
                    return True
            except Exception:
                pass

            # También detectar iframes de recaptcha
            try:
                if page.locator("iframe[title*='captcha'], iframe[src*='recaptcha']").is_visible(timeout=3000):
                    print("⚠️ Iframe de CAPTCHA detectado. Resuélvelo manualmente en la ventana del navegador.")
                    input("Presiona ENTER cuando hayas resuelto el CAPTCHA...")
                    return True
            except Exception:
                pass

            return False

        try:
            # Abrir la página inicial de la biblioteca para empezar (si nunca iniciaste sesión, hazlo)
            print("Abriendo portal de la biblioteca...")
            page.goto("https://library.uniquindio.edu.co/databases", timeout=90000)
            page.wait_for_load_state("domcontentloaded", timeout=60000)
            human_pause(1.0, 2.0)

            # Recordatorio: si necesitas iniciar sesión / resolver verificación por primera vez,
            # hazlo ahora en la ventana que se abrió.
            print("Si no has iniciado sesión o hay verificación, resuélvela en la ventana del navegador.")
            wait_if_human_check()

            # Hacer clic en Facultad Ingeniería (selector que usas)
            fac_selector = "div[data-content-listing-item='fac-ingenier-a']"
            try:
                page.click(fac_selector, timeout=10000)
                page.wait_for_load_state("domcontentloaded", timeout=60000)
                human_pause(0.8, 1.6)
            except Exception:
                print(f"⚠️ No se pudo clicar en '{fac_selector}', continúa igualmente (puede que ya estés en la página).")

            # Abrir ACM: buscamos el link correspondiente y lo clickeamos
            acm_locator = "//a[contains(@href, 'dl.acm.org')]//span[contains(text(), 'ACM Digital Library')]"
            try:
                elements = page.locator(acm_locator)
                count = elements.count()
                clicked = False
                for i in range(count):
                    try:
                        if elements.nth(i).is_visible():
                            elements.nth(i).click()
                            page.wait_for_load_state("domcontentloaded", timeout=60000)
                            human_pause(1.0, 2.0)
                            print(f"Se hizo clic en el elemento ACM (index {i}).")
                            clicked = True
                            break
                    except Exception:
                        continue
                if not clicked:
                    print("⚠️ No se encontró o no se pudo clicar el enlace ACM. Revisa el selector en la página.")
            except Exception as e:
                print("⚠️ Error buscando enlace ACM:", e)

            # --- Abrimos el archivo de salida y comenzamos a iterar por años y páginas ---
            written_ids = 0
            with open(output_path, "w", encoding="utf-8") as out_file:
                for year in range(start_year, end_year + 1):
                    # Construimos la query por año (esto ayuda a obtener más resultados en total)
                    q_for_url = "+".join(query.split())
                    # Incluimos el año como parte de la búsqueda (acm suele indexar años en texto)
                    q_with_year = f"{q_for_url}+{year}"

                    print(f"\n=== Buscando '{query}' año {year} ===")
                    # Abrir búsqueda inicial para el año
                    search_url = f"https://dl.acm.org/action/doSearch?AllField={q_with_year}&pageSize={results_per_page}&startPage=1"
                    page.goto(search_url, timeout=90000)
                    page.wait_for_load_state("domcontentloaded", timeout=60000)
                    human_pause(1.0, 2.0)

                    wait_if_human_check()

                    # Intentar cambiar pageSize si existe control en la UI (segundo intento)
                    try:
                        size_btn = page.locator("a[href*='pageSize={0}']".format(results_per_page))
                        if size_btn.count() > 0:
                            try:
                                size_btn.first.click()
                                human_pause(0.8, 1.5)
                            except Exception:
                                pass
                    except Exception:
                        pass

                    # Iterar páginas para ese año
                    for page_idx in range(1, max_pages_per_year + 1):
                        print(f"[{year}] Procesando página {page_idx}...")
                        # Si Cloudflare aparece: pedir intervención manual
                        wait_if_human_check()

                        # Esperar por resultados; si no aparecen, intentar reload o URL directa
                        try:
                            page.wait_for_selector(".search__item", timeout=30000)
                        except Exception:
                            print("  ⚠️ No se encontró '.search__item' (timeout). Intentando recargar y luego URL directa...")
                            try:
                                page.reload(timeout=60000)
                                page.wait_for_selector(".search__item", timeout=30000)
                            except Exception:
                                # intentar URL directa con startPage = page_idx
                                direct = f"https://dl.acm.org/action/doSearch?AllField={q_with_year}&pageSize={results_per_page}&startPage={page_idx}"
                                print("  -> Cargando URL directa:", direct)
                                page.goto(direct, timeout=90000)
                                try:
                                    page.wait_for_selector(".search__item", timeout=30000)
                                except Exception:
                                    print("  ⚠️ Sigue sin aparecer resultados. Es probable que Cloudflare esté bloqueando.")
                                    wait_if_human_check()

                        results = page.query_selector_all(".search__item")
                        if not results:
                            print(f"  ⚠️ No se encontraron resultados en la página {page_idx}. Posible fin de resultados o bloqueo.")
                            break

                        for i, res in enumerate(results):
                            try:
                                title_el = res.query_selector(".hlFld-Title a")
                                title = title_el.inner_text().strip() if title_el else "Unknown"
                                href = title_el.get_attribute("href") if title_el else ""
                                authors_el = res.query_selector(".rlist--inline")
                                authors = authors_el.inner_text().strip() if authors_el else "Unknown"
                                year_el = res.query_selector(".bookPubDate")
                                year_text = "Unknown"
                                if year_el:
                                    m = re.search(r'\b\d{4}\b', year_el.inner_text())
                                    year_text = m.group(0) if m else "Unknown"
                                journal_el = res.query_selector(".issue-item__detail")
                                journal = journal_el.inner_text().strip() if journal_el else "Unknown"
                                abstract_el = res.query_selector(".issue-item__abstract")
                                abstract = abstract_el.inner_text().strip() if abstract_el else "Unknown"
                                full_url = ("https://dl.acm.org" + href) if href and not href.startswith("http") else href

                                # Escribir en BibTeX
                                out_file.write(f"@article{{ref{year}_{page_idx}_{i},\n")
                                out_file.write(f"  title = {{{title}}},\n")
                                out_file.write(f"  author = {{{authors}}},\n")
                                out_file.write(f"  year = {{{year_text}}},\n")
                                out_file.write(f"  journal = {{{journal}}},\n")
                                out_file.write(f"  abstract = {{{abstract}}},\n")
                                out_file.write(f"  url = {{{full_url}}}\n")
                                out_file.write("}\n\n")
                                written_ids += 1
                            except Exception as e:
                                print("  ⚠️ Error extrayendo un resultado:", e)
                                continue

                        # Intentar pasar a la siguiente página por botón; si no, usar URL directa.
                        try:
                            next_btn = page.query_selector(".pagination__btn--next")
                            if next_btn and next_btn.is_visible():
                                next_btn.click()
                                human_pause(2.5, 4.0)
                                page.wait_for_load_state("domcontentloaded", timeout=60000)
                                continue
                            else:
                                # construir URL para la próxima página (startPage = page_idx + 1)
                                next_direct = f"https://dl.acm.org/action/doSearch?AllField={q_with_year}&pageSize={results_per_page}&startPage={page_idx+1}"
                                print("  -> No se detectó botón 'Next'; navegando a:", next_direct)
                                page.goto(next_direct, timeout=90000)
                                human_pause(1.0, 2.0)
                                continue
                        except Exception as e:
                            print("  ⚠️ Error durante paginación:", e)
                            # reintentos simples
                            retr = 0
                            success = False
                            while retr < 3:
                                try:
                                    page.reload()
                                    page.wait_for_selector(".search__item", timeout=30000)
                                    success = True
                                    break
                                except Exception:
                                    retr += 1
                                    time.sleep(2)
                            if not success:
                                print("  ✖ No fue posible avanzar tras intentos. Rompiendo bucle de páginas.")
                                break

                    # fin bucle páginas para ese año
                    # pausa entre años para no sobrecargar
                    human_pause(1.0, 2.0)

            total_written = written_ids
            print(f"\n✅ Escritura completada. Registros escritos: {total_written}")
            print(f"Archivo guardado en: {output_path}")

        except Exception as exc:
            print("ERROR GENERAL:", exc)

        finally:
            try:
                browser_context.close()
            except Exception:
                pass

if __name__ == "__main__":
    # Puedes ajustar parámetros aquí si lo deseas
    scrape_acm(
        query="security systems",
        output_path=os.path.join("Data", "resultados_ACM.bib"),
        user_data_dir="session_acm",
        start_year=2018,
        end_year=2024,
        results_per_page=50,
        max_pages_per_year=20,
        headless=False
    )
