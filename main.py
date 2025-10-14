import os
from Scrape.Scrape_ACM import scrape_acm
from Scrape.Scrape_IEE import scrape_ieee
from Scrape.Scrape_Sage import scrape_sage
from Scrape.Scrape_Springer import scrape_springer_open
from Scrape.Unificar import unify_results_from_files

def run_scraper(scraper_func, output_file):
    """Ejecuta un scraper y verifica que genere datos."""
    print(f"\n=== Iniciando scraper: {scraper_func.__name__} ===")
    scraper_func()

    # Verificar si el archivo se creó y tiene contenido
    if os.path.exists(output_file):
        size = os.path.getsize(output_file)
        if size > 0:
            print(f"✅ Archivo generado correctamente: {output_file} ({size} bytes)")
        else:
            print(f"⚠️ Archivo vacío: {output_file}")
    else:
        print(f"❌ No se creó el archivo: {output_file}")

if __name__ == "__main__":
    # Crear carpeta Data si no existe
    os.makedirs("Data", exist_ok=True)

    # Ejecutar scrapers
    run_scraper(scrape_acm, "Data/resultados_ACM.bib")
    run_scraper(scrape_ieee, "Data/resultados_ieee.bib")
    run_scraper(scrape_sage, "Data/resultados_Sage.bib")
    run_scraper(scrape_springer_open, "Data/resultados_springer_open.bib")

    # Unificar resultados
    print("\n=== Unificando resultados de todos los scrapers ===")
    unify_results_from_files(
        "Data/resultados_ACM.bib",
        "Data/resultados_ieee.bib",
        "Data/resultados_springer_open.bib",
        "Data/resultados_Sage.bib"
    )
    print("\n✅ Unificación finalizada.")
