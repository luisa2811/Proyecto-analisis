"""
SUB-REQUISITO 2: CÁLCULO DE CAMINOS MÍNIMOS ENTRE ARTÍCULOS

Aplica algoritmos de grafos para calcular:
- Dijkstra: Caminos mínimos entre pares de artículos
- Floyd-Warshall: Matriz de distancias entre todos los artículos
- Identificación de artículos con mayor conectividad

Salidas:
- ejemplos_caminos_minimos.csv (ejemplos con Dijkstra)
- matriz_distancias.csv (resultados Floyd-Warshall)
- articulos_mayor_conectividad.csv (artículos más conectados)
"""

import os
import pandas as pd
import networkx as nx
import numpy as np
import random

class CaminosMinimos:
    def __init__(self, ruta_grafo="Resultados/grafo_citaciones.graphml", carpeta_resultados="Resultados"):
        self.ruta_grafo = ruta_grafo
        self.carpeta_resultados = carpeta_resultados
        os.makedirs(self.carpeta_resultados, exist_ok=True)
        self.grafo = None
    
    def cargar_grafo(self):
        """Carga el grafo desde el archivo GraphML"""
        print(f"📥 Cargando grafo desde: {self.ruta_grafo}")
        self.grafo = nx.read_graphml(self.ruta_grafo)
        
        # Convertir a DiGraph si es necesario
        if not isinstance(self.grafo, nx.DiGraph):
            self.grafo = nx.DiGraph(self.grafo)
        
        # Convertir atributos de peso a float
        for u, v, data in self.grafo.edges(data=True):
            if 'peso' in data:
                data['peso'] = float(data['peso'])
        
        print(f"✅ Grafo cargado: {self.grafo.number_of_nodes()} nodos, {self.grafo.number_of_edges()} aristas")
        return self.grafo
    
    def calcular_dijkstra(self, num_ejemplos=10):
        """
        Calcula caminos mínimos usando Dijkstra
        
        Algoritmo: Dijkstra
        - Encuentra el camino más corto entre dos nodos
        - Usa peso inverso (mayor similitud = menor distancia)
        """
        if self.grafo is None:
            self.cargar_grafo()
        
        print("\n" + "="*70)
        print("ALGORITMO: DIJKSTRA - CAMINOS MÍNIMOS")
        print("="*70)
        
        G = self.grafo
        
        def peso_fn(u, v, d):
            return 1.0 / d.get('peso', 0.5)
        
        print(f"\n📌 Calculando {num_ejemplos} ejemplos de caminos mínimos...\n")
        
        nodos_conectados = [n for n in G.nodes() if G.degree(n) > 0]
        
        if len(nodos_conectados) < 2:
            print("   ⚠️  No hay suficientes nodos conectados")
            return
        
        ejemplos_caminos = []
        intentos = 0
        max_intentos = num_ejemplos * 10
        
        random.seed(42)
        nodos_mezclados = nodos_conectados.copy()
        random.shuffle(nodos_mezclados)
        
        i = 0
        while len(ejemplos_caminos) < num_ejemplos and intentos < max_intentos:
            idx_origen = intentos % len(nodos_mezclados)
            idx_destino = (intentos + len(nodos_mezclados)//2) % len(nodos_mezclados)
            
            origen = nodos_mezclados[idx_origen]
            destino = nodos_mezclados[idx_destino]
            
            intentos += 1
            
            if origen == destino:
                continue
            
            try:
                # Intentar calcular camino usando grafo no dirigido para mayor conectividad
                G_undirected = G.to_undirected()
                if not nx.has_path(G_undirected, origen, destino):
                    continue
                
                camino = nx.dijkstra_path(G, origen, destino, weight=peso_fn)
                distancia = nx.dijkstra_path_length(G, origen, destino, weight=peso_fn)
                
                if any(e['id_origen'] == origen and e['id_destino'] == destino for e in ejemplos_caminos):
                    continue
                
                titulo_o = G.nodes[origen].get('titulo', f'Artículo {origen}')[:50]
                titulo_d = G.nodes[destino].get('titulo', f'Artículo {destino}')[:50]
                
                i += 1
                print(f"   Ejemplo {i}:")
                print(f"   • Origen: [{origen}] {titulo_o}...")
                print(f"   • Destino: [{destino}] {titulo_d}...")
                print(f"   • Distancia mínima: {distancia:.4f}")
                print(f"   • Número de saltos: {len(camino) - 1}")
                
                if len(camino) <= 5:
                    print(f"   • Ruta: {' → '.join([str(n) for n in camino])}")
                
                print()
                
                ejemplos_caminos.append({
                    'id_origen': origen,
                    'id_destino': destino,
                    'titulo_origen': titulo_o,
                    'titulo_destino': titulo_d,
                    'distancia_minima': round(distancia, 4),
                    'num_saltos': len(camino) - 1,
                    'ruta_completa': ' → '.join([str(n) for n in camino])
                })
                
            except nx.NetworkXNoPath:
                continue
            except Exception:
                continue
        
        if len(ejemplos_caminos) < num_ejemplos:
            print(f"   ⚠️  Solo se pudieron calcular {len(ejemplos_caminos)} caminos de {num_ejemplos} solicitados")
            print(f"      Razón: El grafo tiene muchas componentes desconectadas")
            print(f"      Sugerencia: Reducir el umbral de similitud en el Sub-requisito 1")
            print(f"                  (ej: de 0.70 a 0.60 para más conexiones)")
        
        # Guardar ejemplos
        if ejemplos_caminos:
            df_caminos = pd.DataFrame(ejemplos_caminos)
            ruta = os.path.join(self.carpeta_resultados, "ejemplos_caminos_minimos.csv")
            df_caminos.to_csv(ruta, index=False, encoding='utf-8-sig')
            print(f"   💾 {len(ejemplos_caminos)} ejemplos guardados en: {ruta}")
            
            return df_caminos
        else:
            print(f"   ❌ No se pudieron calcular caminos mínimos")
            print(f"      El grafo está muy fragmentado. Ajusta el umbral de similitud.")
        
        return None
    
    def calcular_floyd_warshall(self, muestra=100):
        """
        Calcula matriz de distancias usando Floyd-Warshall
        
        Algoritmo: Floyd-Warshall
        - Calcula distancias entre TODOS los pares de nodos
        - Más costoso computacionalmente
        """
        if self.grafo is None:
            self.cargar_grafo()
        
        print("\n" + "="*70)
        print("ALGORITMO: FLOYD-WARSHALL - MATRIZ DE DISTANCIAS")
        print("="*70)
        
        G = self.grafo
        
        def peso_fn(u, v, d):
            return 1.0 / d.get('peso', 0.5)
        
        muestra = min(muestra, G.number_of_nodes())
        print(f"\n📌 Calculando matriz para {muestra} nodos más conectados...")
        
        degrees = dict(G.degree())
        top_nodos = sorted(degrees, key=degrees.get, reverse=True)[:muestra]
        G_muestra = G.subgraph(top_nodos).copy()
        
        print("   Calculando distancias...")
        distancias = dict(nx.floyd_warshall(G_muestra, weight=peso_fn))
        
        # Crear matriz
        matriz_dist = []
        for origen in top_nodos:
            for destino in top_nodos:
                if origen != destino:
                    dist = distancias[origen].get(destino, float('inf'))
                    if dist != float('inf'):
                        matriz_dist.append({
                            'origen': origen,
                            'destino': destino,
                            'distancia': round(dist, 6)
                        })
        
        df_matriz = pd.DataFrame(matriz_dist)
        ruta_matriz = os.path.join(self.carpeta_resultados, "matriz_distancias.csv")
        df_matriz.to_csv(ruta_matriz, index=False, encoding='utf-8-sig')
        print(f"   💾 Matriz guardada en: {ruta_matriz}")
        
        # Estadísticas
        if len(df_matriz) > 0:
            print(f"\n   📊 Estadísticas:")
            print(f"      Pares analizados: {len(df_matriz)}")
            print(f"      Distancia promedio: {df_matriz['distancia'].mean():.4f}")
            print(f"      Distancia mínima: {df_matriz['distancia'].min():.4f}")
            print(f"      Distancia máxima: {df_matriz['distancia'].max():.4f}")
        
        return df_matriz
    
    def identificar_mas_conectados(self, top_n=10):
        """
        Identifica artículos con mayor conectividad
        Menor distancia promedio = Mayor conectividad
        """
        if self.grafo is None:
            self.cargar_grafo()
        
        print("\n" + "="*70)
        print("ARTÍCULOS CON MAYOR CONECTIVIDAD")
        print("="*70)
        
        G = self.grafo
        
        def peso_fn(u, v, d):
            return 1.0 / d.get('peso', 0.5)
        
        print(f"\n📌 Identificando top {top_n} artículos más conectados...")
        
        conectividad = {}
        for nodo in G.nodes():
            try:
                distancias_nodo = nx.single_source_dijkstra_path_length(G, nodo, weight=peso_fn)
                dist_valores = [d for n, d in distancias_nodo.items() if n != nodo]
                if dist_valores:
                    conectividad[nodo] = np.mean(dist_valores)
            except:
                conectividad[nodo] = float('inf')
        
        top_conectados = sorted(conectividad.items(), key=lambda x: x[1])[:top_n]
        
        print(f"\n   🏆 TOP {top_n} ARTÍCULOS MÁS CONECTADOS:")
        print("   (menor distancia promedio)\n")
        
        resultados = []
        for i, (nodo, dist_prom) in enumerate(top_conectados, 1):
            titulo = G.nodes[nodo].get('titulo', f'Artículo {nodo}')[:60]
            num_conexiones = G.degree(nodo)
            
            print(f"   {i:2d}. [{nodo}] Distancia promedio: {dist_prom:.4f}")
            print(f"       Conexiones directas: {num_conexiones}")
            print(f"       {titulo}...\n")
            
            resultados.append({
                'ranking': i,
                'id_articulo': nodo,
                'distancia_promedio': round(dist_prom, 4),
                'conexiones_directas': num_conexiones,
                'titulo': titulo
            })
        
        df_conectividad = pd.DataFrame(resultados)
        ruta = os.path.join(self.carpeta_resultados, "articulos_mayor_conectividad.csv")
        df_conectividad.to_csv(ruta, index=False, encoding='utf-8-sig')
        print(f"   💾 Resultados guardados en: {ruta}")
        
        return df_conectividad
    
    def explicar_distancia(self, origen, destino):
        """Explica detalladamente cómo se calcula una distancia"""
        if self.grafo is None:
            self.cargar_grafo()
        
        G = self.grafo
        
        def peso_fn(u, v, d):
            return 1.0 / d.get('peso', 0.5)
        
        try:
            camino = nx.dijkstra_path(G, origen, destino, weight=peso_fn)
            distancia = nx.dijkstra_path_length(G, origen, destino, weight=peso_fn)
            
            print("\n" + "="*70)
            print(f"EXPLICACIÓN: CÁLCULO DE DISTANCIA {origen} → {destino}")
            print("="*70)
            
            print(f"\n📍 Origen: [{origen}] {G.nodes[origen].get('titulo', '')[:60]}...")
            print(f"📍 Destino: [{destino}] {G.nodes[destino].get('titulo', '')[:60]}...")
            print(f"\n🔍 Camino: {' → '.join([str(n) for n in camino])}")
            print(f"   Saltos: {len(camino) - 1}\n")
            
            distancia_acumulada = 0
            
            for i in range(len(camino) - 1):
                nodo_actual = camino[i]
                nodo_siguiente = camino[i + 1]
                
                datos = G.edges[nodo_actual, nodo_siguiente]
                similitud = float(datos.get('peso', 0.5))
                dist_arista = 1.0 / similitud
                distancia_acumulada += dist_arista
                
                print(f"   Paso {i+1}: [{nodo_actual}] → [{nodo_siguiente}]")
                print(f"      Similitud: {similitud:.6f} ({similitud*100:.2f}%)")
                print(f"      Distancia: {dist_arista:.6f}")
                print(f"      Acumulado: {distancia_acumulada:.6f}\n")
            
            print("="*70)
            print(f"✅ DISTANCIA TOTAL: {distancia:.4f}")
            print("="*70)
            
        except nx.NetworkXNoPath:
            print(f"❌ No existe camino entre {origen} y {destino}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print(" SUB-REQUISITO 2: CÁLCULO DE CAMINOS MÍNIMOS")
    print("="*70)
    
    # Crear instancia
    calculador = CaminosMinimos()
    
    # Cargar grafo
    calculador.cargar_grafo()
    
    # Dijkstra: Ejemplos de caminos
    calculador.calcular_dijkstra(num_ejemplos=10)
    
    # Floyd-Warshall: Matriz de distancias
    calculador.calcular_floyd_warshall(muestra=100)
    
    # Artículos más conectados
    calculador.identificar_mas_conectados(top_n=10)
    
    # Ejemplo de explicación
    print("\n" + "="*70)
    print(" EJEMPLO: EXPLICACIÓN DE CÁLCULO DE DISTANCIA")
    print("="*70)
    
    try:
        df = pd.read_csv("Resultados/ejemplos_caminos_minimos.csv")
        if len(df) > 0:
            # Convertir a string y luego a int
            origen = str(df.iloc[0]['id_origen'])
            destino = str(df.iloc[0]['id_destino'])
            calculador.explicar_distancia(origen, destino)
        else:
            print("⚠️  No hay ejemplos disponibles (grafo muy desconectado)")
    except Exception as e:
        print(f"⚠️  No se pudo cargar ejemplo: {e}")
    
    print("\n" + "="*70)
    print(" ✅ SUB-REQUISITO 2 COMPLETADO")
    print("="*70)
    print("\n📁 Archivos generados:")
    print("   • ejemplos_caminos_minimos.csv")
    print("   • matriz_distancias.csv")
    print("   • articulos_mayor_conectividad.csv")