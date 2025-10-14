from Analisis.Ordenamientos import benchmark_algorithms
from Analisis.ProcesarBib import ProcesarBib
import os

if __name__ == "__main__":
    if os.path.exists("Data/unificados.bib"):
        pb = ProcesarBib()
        pb.ordenar_articulos()   # genera ArticulosOrdenados.csv ordenado por año + título
        pb.graficar_autores()    # genera autores_top15.png y Top15Autores.csv
    else:
        print("⚠️ No se encontró Data/unificados.bib. Ejecuta primero la unificación.")

    benchmark_algorithms(5000)
