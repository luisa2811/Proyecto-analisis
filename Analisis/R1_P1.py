"""
SUB-REQUISITO 1: CONSTRUCCIÓN AUTOMÁTICA DEL GRAFO DE CITACIONES

Crea un grafo dirigido donde:
- Cada nodo = un artículo del CSV
- Cada arista = relación de similitud entre artículos (títulos + autores + palabras clave)
- Si similitud > umbral, se crea una arista dirigida con peso

Salidas:
- grafo_citaciones.graphml (estructura de datos)
- estructura_aristas_dirigidas.csv (lista de conexiones)
- visualizacion_grafo.png (diagrama visual)
"""

import os
import re
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class ConstruccionGrafo:
    def __init__(self, ruta_csv="Resultados/ArticulosOrdenados.csv", carpeta_resultados="Resultados"):
        self.ruta_csv = ruta_csv
        self.carpeta_resultados = carpeta_resultados
        os.makedirs(self.carpeta_resultados, exist_ok=True)
        self.df = None
        self.grafo = None
        
    def cargar_datos(self):
        """Carga el CSV de artículos ordenados"""
        self.df = pd.read_csv(self.ruta_csv, encoding='utf-8-sig')
        
        print(f"📥 Cargados {len(self.df)} artículos del CSV")
        
        # Eliminar duplicados basados en título
        df_original = len(self.df)
        self.df = self.df.drop_duplicates(subset=['title'], keep='first')
        duplicados_removidos = df_original - len(self.df)
        
        if duplicados_removidos > 0:
            print(f"⚠️  Removidos {duplicados_removidos} artículos duplicados")
        
        # Resetear índices
        self.df = self.df.reset_index(drop=True)
        
        print(f"✅ Total de artículos únicos: {len(self.df)}")
        return self.df
    
    def _crear_texto_combinado(self, row):
        """Combina título, autores y abstract para análisis de similitud"""
        partes = []
        
        if pd.notna(row.get('title')):
            partes.append(str(row['title']) * 3)  # Más peso al título
        
        if pd.notna(row.get('author')):
            partes.append(str(row['author']) * 2)  # Peso medio a autores
        
        if pd.notna(row.get('abstract')):
            partes.append(str(row['abstract']))  # Palabras clave del abstract
        
        return ' '.join(partes) if partes else ''
    
    def construir_grafo(self, umbral_similitud=0.70, max_conexiones=5):
        """
        Construye el grafo dirigido de citaciones por similitud
        
        Parámetros:
        - umbral_similitud: valor mínimo para crear conexión (0.70 = 70%)
        - max_conexiones: máximo de conexiones salientes por artículo
        """
        if self.df is None:
            self.cargar_datos()
        
        print("\n" + "="*70)
        print("SUB-REQUISITO 1: CONSTRUCCIÓN DEL GRAFO DE CITACIONES")
        print("="*70)
        
        # 1. Crear grafo dirigido
        G = nx.DiGraph()
        
        # 2. Agregar nodos
        print("\n📌 Paso 1: Agregando nodos al grafo...")
        for idx, row in self.df.iterrows():
            titulo = row.get('title', f'Artículo_{idx}')
            autor = row.get('author', 'Sin autor')
            year = row.get('year', 'N/A')
            
            G.add_node(idx, 
                      id_articulo=idx,
                      titulo=titulo,
                      autor=autor,
                      año=year,
                      journal=row.get('journal', ''),
                      abstract=row.get('abstract', ''))
        
        print(f"   ✅ Agregados {G.number_of_nodes()} nodos (artículos)")
        
        # 3. Calcular similitud
        print("\n📌 Paso 2: Calculando similitud entre artículos...")
        print(f"   Umbral de similitud: {umbral_similitud*100}%")
        print(f"   Basado en: Títulos + Autores + Palabras clave (abstract)")
        
        textos = [self._crear_texto_combinado(row) for _, row in self.df.iterrows()]
        
        vectorizer = TfidfVectorizer(max_features=500, stop_words='english', 
                                    ngram_range=(1, 2), min_df=2)
        tfidf_matrix = vectorizer.fit_transform(textos)
        similitud_matriz = cosine_similarity(tfidf_matrix)
        
        # 4. Crear aristas
        print(f"\n📌 Paso 3: Creando aristas (relaciones entre artículos)...")
        aristas_creadas = 0
        aristas_rechazadas = 0
        
        for i in range(len(self.df)):
            similitudes_i = similitud_matriz[i].copy()
            similitudes_i[i] = -1  # Excluir mismo artículo
            
            indices_similares = np.argsort(similitudes_i)[-max_conexiones:]
            
            for j in indices_similares:
                sim = similitud_matriz[i, j]
                
                # Verificación 1: No el mismo artículo
                if i == j:
                    continue
                
                # Verificación 2: Similitud en rango válido
                if sim >= 0.95 or sim < umbral_similitud:
                    aristas_rechazadas += 1
                    continue
                
                # Verificación 3: Títulos no demasiado similares
                titulo_i = str(G.nodes[i]['titulo']).strip().lower()
                titulo_j = str(G.nodes[j]['titulo']).strip().lower()
                
                palabras_i = set(titulo_i.split())
                palabras_j = set(titulo_j.split())
                
                if len(palabras_i) > 0 and len(palabras_j) > 0:
                    similitud_titulo = len(palabras_i & palabras_j) / len(palabras_i | palabras_j)
                    
                    if similitud_titulo > 0.90:
                        aristas_rechazadas += 1
                        continue
                
                # Crear arista
                G.add_edge(i, j, peso=float(sim), similitud_porcentaje=f"{sim*100:.1f}%")
                aristas_creadas += 1
        
        print(f"   ✅ Creadas {aristas_creadas} aristas válidas")
        print(f"   ⚠️  Rechazadas {aristas_rechazadas} conexiones")
        
        # Mostrar ejemplos
        print(f"\n   📝 Ejemplos de relaciones inferidas por similitud:")
        contador = 0
        
        for origen, destino, datos in G.edges(data=True):
            if contador >= 3:
                break
            
            sim = datos.get('peso', 0)
            titulo_o = G.nodes[origen]['titulo'][:40] if G.nodes[origen]['titulo'] else f'Art. {origen}'
            titulo_d = G.nodes[destino]['titulo'][:40] if G.nodes[destino]['titulo'] else f'Art. {destino}'
            autor_o = str(G.nodes[origen]['autor'])[:30] if pd.notna(G.nodes[origen]['autor']) else 'Sin autor'
            autor_d = str(G.nodes[destino]['autor'])[:30] if pd.notna(G.nodes[destino]['autor']) else 'Sin autor'
            
            print(f"\n      Ejemplo {contador + 1}:")
            print(f"      [{origen}] → [{destino}]")
            print(f"      Similitud: {sim*100:.1f}%")
            print(f"        • {titulo_o}...")
            print(f"        • {titulo_d}...")
            print(f"      Autores:")
            print(f"        • {autor_o}...")
            print(f"        • {autor_d}...")
            
            contador += 1
        
        self.grafo = G
        
        # Resumen
        print("\n📊 RESULTADO SUB-REQUISITO 1:")
        print(f"   • Grafo dirigido creado exitosamente")
        print(f"   • Nodos (artículos): {G.number_of_nodes()}")
        print(f"   • Aristas (relaciones): {G.number_of_edges()}")
        print(f"   • Densidad: {nx.density(G):.6f}")
        print(f"   • Grado promedio: {sum(dict(G.degree()).values()) / G.number_of_nodes():.2f}")
        
        return G
    
    def exportar_grafo(self, formato='graphml'):
        """Exporta el grafo a archivo"""
        if self.grafo is None:
            raise RuntimeError("Primero construye el grafo")
        
        G_export = self.grafo.copy()
        
        # Limpiar atributos
        for node in G_export.nodes():
            if pd.isna(G_export.nodes[node].get('titulo')):
                G_export.nodes[node]['titulo'] = f'Artículo {node}'
            if pd.isna(G_export.nodes[node].get('autor')):
                G_export.nodes[node]['autor'] = 'Sin autor'
        
        # Exportar estructura
        if formato == 'graphml':
            ruta = os.path.join(self.carpeta_resultados, "grafo_citaciones.graphml")
            nx.write_graphml(G_export, ruta)
        elif formato == 'gexf':
            ruta = os.path.join(self.carpeta_resultados, "grafo_citaciones.gexf")
            nx.write_gexf(G_export, ruta)
        
        print(f"\n💾 Estructura guardada en: {ruta}")
        
        # Exportar lista de aristas
        lista_aristas = []
        
        for origen, destino, datos in self.grafo.edges(data=True):
            titulo_o = self.grafo.nodes[origen]['titulo'][:50] if self.grafo.nodes[origen]['titulo'] else f'Artículo {origen}'
            titulo_d = self.grafo.nodes[destino]['titulo'][:50] if self.grafo.nodes[destino]['titulo'] else f'Artículo {destino}'
            
            lista_aristas.append({
                'id_origen': origen,
                'id_destino': destino,
                'titulo_origen': titulo_o,
                'titulo_destino': titulo_d,
                'peso': round(datos.get('peso', 0), 6),
                'similitud_porcentaje': datos.get('similitud_porcentaje', '0%'),
                'direccion': f'{origen} → {destino}'
            })
        
        df_aristas = pd.DataFrame(lista_aristas)
        ruta_aristas = os.path.join(self.carpeta_resultados, "estructura_aristas_dirigidas.csv")
        df_aristas.to_csv(ruta_aristas, index=False, encoding='utf-8-sig')
        
        print(f"💾 Lista de aristas: {ruta_aristas}")
        print(f"   Total aristas con dirección y peso: {len(lista_aristas)}")
        
        return ruta
    
    def visualizar_grafo(self, num_nodos=50, guardar=True):
        """Visualiza el grafo"""
        if self.grafo is None:
            raise RuntimeError("Primero construye el grafo")
        
        G = self.grafo
        degrees = dict(G.degree())
        top_nodos = sorted(degrees, key=degrees.get, reverse=True)[:num_nodos]
        subgrafo = G.subgraph(top_nodos).copy()
        
        plt.figure(figsize=(16, 12))
        pos = nx.spring_layout(subgrafo, k=1.5, iterations=50, seed=42)
        
        node_sizes = [degrees[n] * 30 + 100 for n in subgrafo.nodes()]
        
        node_colors = []
        for n in subgrafo.nodes():
            year = subgrafo.nodes[n].get('año', 2000)
            if pd.isna(year):
                year = 2000
            node_colors.append(year)
        
        nodes = nx.draw_networkx_nodes(subgrafo, pos, 
                                       node_size=node_sizes,
                                       node_color=node_colors,
                                       cmap=plt.cm.viridis,
                                       alpha=0.7)
        
        nx.draw_networkx_edges(subgrafo, pos, 
                              edge_color='gray',
                              alpha=0.2,
                              arrows=True,
                              arrowsize=10,
                              width=0.5,
                              connectionstyle='arc3,rad=0.1')
        
        if node_colors:
            plt.colorbar(nodes, label='Año de publicación')
        
        plt.title(f'Red de Citaciones por Similitud\n(Top {num_nodos} artículos más conectados)', 
                 fontsize=16, pad=20)
        plt.axis('off')
        plt.tight_layout()
        
        if guardar:
            ruta = os.path.join(self.carpeta_resultados, "visualizacion_grafo.png")
            plt.savefig(ruta, dpi=150, bbox_inches='tight', facecolor='white')
            print(f"\n🖼️  Visualización: {ruta}")
            plt.close()
        else:
            plt.show()


if __name__ == "__main__":
    print("\n" + "="*70)
    print(" SUB-REQUISITO 1: CONSTRUCCIÓN DEL GRAFO DE CITACIONES")
    print("="*70)
    
    # Crear instancia
    constructor = ConstruccionGrafo()
    
    # Cargar datos
    constructor.cargar_datos()
    
    # Construir grafo
    # NOTA: Ajusta estos parámetros según necesites:
    # - umbral_similitud más bajo = MÁS conexiones (0.50-0.70 recomendado)
    # - max_conexiones más alto = grafo más denso (5-10 recomendado)
    constructor.construir_grafo(umbral_similitud=0.60, max_conexiones=8)
    
    # Exportar
    constructor.exportar_grafo(formato='graphml')
    
    # Visualizar
    constructor.visualizar_grafo(num_nodos=50, guardar=True)
    
    print("\n" + "="*70)
    print(" ✅ SUB-REQUISITO 1 COMPLETADO")
    print("="*70)
    print("\n📁 Archivos generados:")
    print("   • grafo_citaciones.graphml")
    print("   • estructura_aristas_dirigidas.csv")
    print("   • visualizacion_grafo.png")