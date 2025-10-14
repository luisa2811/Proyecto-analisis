import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import textwrap
import seaborn as sns

def clean_braces(s):
    if s is None:
        return ""
    s = str(s).strip()
    s = re.sub(r'^\{+', '', s)
    s = re.sub(r'\}+$', '', s)
    s = s.strip('"')
    s = s.rstrip(',')
    return s.strip()

def normalize_author_name(a):
    a = clean_braces(a)
    a = re.sub(r'\s+', ' ', a).strip()
    if ',' in a:
        parts = [p.strip() for p in a.split(',') if p.strip()]
        if len(parts) >= 2:
            firstname = " ".join(parts[1:])
            lastname = parts[0]
            return (firstname + " " + lastname).strip()
    return a

def split_authors_field(s):
    if not s or not isinstance(s, str):
        return []
    s = s.strip()
    # Preferir ' and ' (formato BibTeX)
    if " and " in s:
        parts = [p.strip() for p in s.split(" and ") if p.strip()]
    else:
        parts = re.split(r'\s*(?:;|/|&|\n)\s*', s)
        parts = [p for p in parts if p.strip()]
    return [normalize_author_name(p) for p in parts]


class ProcesarBib:
    def __init__(self, ruta_bib="Data/unificados.bib", carpeta_resultados="Resultados"):
        self.ruta_bib = ruta_bib
        self.carpeta_resultados = carpeta_resultados
        os.makedirs(self.carpeta_resultados, exist_ok=True)
        self.df = None

    def _extract_year(self, raw):
        if raw is None:
            return None
        m = re.search(r'(\d{4})', str(raw))
        return int(m.group(1)) if m else None


    def ordenar_articulos(self):
    
        with open(self.ruta_bib, "r", encoding="utf-8", errors="ignore") as f:
            contenido = f.read()

        # ====== 1. LIMPIEZA DE FORMATO (global) ======
        contenido = re.sub(r"\}\}\}+", "},", contenido)
        contenido = re.sub(r"\}\}+", "},", contenido)
        contenido = re.sub(r",\s*\}", "}", contenido)

        # Separar cada entrada @
        entradas = re.split(r"@(?=\w+{)", contenido)
        registros = []

        # ====== 2. PROCESAR CADA ENTRADA ======
        for entrada in entradas:
            if not entrada.strip():
                continue

            campos = {
                "title": None,
                "author": None,
                "year": None,
                "journal": None,
                "tipo": None,
                "publisher": None,
                "abstract": None,
                "url": None
            }

            # Extraer campos con regex
            for key in campos.keys():
                patron = rf"{key}\s*=\s*{{(.*?)}}"
                m = re.search(patron, entrada, re.DOTALL | re.IGNORECASE)
                if m:
                    valor = m.group(1).replace("\n", " ").strip()
                    valor = clean_braces(valor)  # limpieza local básica
                    campos[key] = valor

            # Normalizar autores si existen
            if campos["author"]:
                lista_autores = split_authors_field(campos["author"])
                campos["author"] = "; ".join(lista_autores)

            # Extraer año con función robusta
            campos["year"] = self._extract_year(campos["year"])

            registros.append(campos)

        # ====== 3. ORDENAR ======
        registros.sort(
            key=lambda x: (
                x["year"] if isinstance(x["year"], int) else 9999,
                x["title"].lower() if x["title"] else ""
            )
        )

        # ====== 4. CONVERTIR A DATAFRAME ======
        df = pd.DataFrame(registros)

        # Ordenar nuevamente en el DataFrame (por seguridad)
        df = df.sort_values(
            by=["year", "title"], 
            ascending=[True, True], 
            na_position="last"
        ).reset_index(drop=True)

        # Guardar CSV
        out_csv = os.path.join(self.carpeta_resultados, "ArticulosOrdenados.csv")
        df.to_csv(out_csv, index=False, encoding="utf-8-sig")

        self.df = df
        print(f"✅ CSV ordenado guardado en: {out_csv}")



    def graficar_autores(self, guardar_png=True, usar_seaborn=True):

        if self.df is None:
            raise RuntimeError("Primero ejecuta ordenar_articulos()")

        # --- Expandir autores ---
        def split_authors_cell(s):
            if pd.isna(s):
                return []
            s = s.strip()
            if s == '':
                return []
            # Separar por ;, /, &, and, y
            parts = re.split(r'\s*(?:;|/|&|\band\b|\by\b)\s*', s, flags=re.IGNORECASE)
            out = []
            for p in parts:
                p = p.strip()
                if not p:
                    continue
                if p.count(',') >= 2:
                    subs = [x.strip() for x in p.split(',') if x.strip()]
                    out.extend(subs)
                else:
                    out.append(p)
            return out

        authors_series = self.df['author'].fillna('').apply(split_authors_cell).explode().astype(str).str.strip()

        # --- LIMPIEZA ---
        authors_series = authors_series[authors_series != ""]
        pattern = r'^(nan|View all|\[...\]|\.\.\.|PhD|\+\s*\d+)$'
        authors_series = authors_series[~authors_series.str.match(pattern, case=False)]
        authors_series = authors_series.str.replace(r'\s+', ' ', regex=True)

        # --- Conteo ---
        author_counts = authors_series.value_counts()
        top_15_authors = author_counts.head(15).sort_values(ascending=True)

        # --- DataFrame para graficar ---
        top_authors_df = top_15_authors.reset_index()
        top_authors_df.columns = ['Autor', 'Frecuencia']
        top_authors_df['Autor'] = top_authors_df['Autor'].apply(
            lambda x: "\n".join(textwrap.wrap(x, width=30))
        )

        # --- Gráfico ---
        plt.figure(figsize=(12, 8))
        if usar_seaborn:
            sns.set_style("whitegrid")
            bar_plot = sns.barplot(data=top_authors_df, x='Frecuencia', y='Autor', palette='viridis')
        else:
            plt.barh(top_authors_df['Autor'], top_authors_df['Frecuencia'])

        for index, value in enumerate(top_authors_df['Frecuencia']):
            plt.text(value + 0.5, index, str(value), va='center', ha='left')

        plt.xlim(0, top_authors_df['Frecuencia'].max() * 1.15)
        plt.title('Top 15 Autores con Más Apariciones', fontsize=16)
        plt.xlabel('Número de Apariciones', fontsize=12)
        plt.ylabel('Autor', fontsize=12)
        plt.tight_layout()

        if guardar_png:
            png_path = os.path.join(self.carpeta_resultados, "autores_top15.png")
            plt.savefig(png_path, dpi=150)
            plt.close()
            print(f"✅ Gráfica guardada en: {png_path}")
        else:
            plt.show()

        # --- Guardar tabla CSV ---
        csv_path = os.path.join(self.carpeta_resultados, "Top15Autores.csv")
        top_authors_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"✅ CSV top15 guardado en: {csv_path}")

if __name__ == "__main__":
    procesador = ProcesarBib()
    procesador.ordenar_articulos()
    procesador.graficar_autores(guardar_png=True, usar_seaborn=True)
    