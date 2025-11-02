"""
SUB-REQUISITO 3: IDENTIFICACIÓN DE COMPONENTES FUERTEMENTE CONEXAS

Usa algoritmos de grafos para identificar:
- Grupos de artículos fuertemente conectados (bidireccional)
- Clústeres temáticos o de autores relacionados
- Artículos aislados vs artículos en grupos

Algoritmo: Kosaraju/Tarjan (implementado en NetworkX)

Salidas:
- componentes_fuertemente_conexas.csv (resumen)
- componentes_detalle_completo.csv (todos los artículos de cada grupo)
"""

import os
import pandas as pd
import networkx as nx

class ComponentesConexas:
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
        
        print(f"✅ Grafo cargado: {self.grafo.number_of_nodes()} nodos, {self.grafo.number_of_edges()} aristas")
        return self.grafo
    
    def identificar_componentes_fuertes(self):
        """
        Identifica componentes fuertemente conexas
        
        Algoritmo: Kosaraju/Tarjan
        - Encuentra grupos donde todos los nodos están conectados bidireccionales
        - Representa clústeres temáticos cohesivos
        """
        if self.grafo is None:
            self.cargar_grafo()
        
        print("\n" + "="*70)
        print("SUB-REQUISITO 3: COMPONENTES FUERTEMENTE CONEXAS")
        print("="*70)
        
        G = self.grafo
        
        print("\n📌 Algoritmo: KOSARAJU/TARJAN")
        print("   Identificando componentes fuertemente conexas...\n")
        
        # Componentes fuertemente conexas
        componentes_fuertes = list(nx.strongly_connected_components(G))
        componentes_fuertes = sorted(componentes_fuertes, key=len, reverse=True)
        
        print(f"   ✅ Encontradas {len(componentes_fuertes)} componentes fuertemente conexas")
        
        # Mostrar principales
        print("\n   📋 COMPONENTES PRINCIPALES:\n")
        
        resultados_componentes = []
        for i, componente in enumerate(componentes_fuertes[:10], 1):
            tam = len(componente)
            nodos_list = sorted(list(componente))[:10]
            
            print(f"   Componente {i}: {tam} artículos")
            print(f"   IDs: {nodos_list}{'...' if tam > 10 else ''}")
            
            if tam <= 5:
                print(f"   Artículos:")
                for nodo in nodos_list:
                    titulo = G.nodes[nodo].get('titulo', f'Artículo {nodo}')[:50]
                    print(f"      • [{nodo}] {titulo}...")
            print()
            
            resultados_componentes.append({
                'componente_id': i,
                'num_articulos': tam,
                'nodos': str(nodos_list),
                'tipo': 'Principal' if tam > 1 else 'Aislado'
            })
        
        # Componentes débiles (para comparación)
        componentes_debiles = list(nx.weakly_connected_components(G))
        componentes_debiles = sorted(componentes_debiles, key=len, reverse=True)
        
        print(f"   ℹ️  Componentes débilmente conexas: {len(componentes_debiles)}")
        print(f"   ℹ️  Componente débil más grande: {len(componentes_debiles[0])} artículos")
        
        # Guardar resumen
        df_componentes = pd.DataFrame(resultados_componentes)
        ruta = os.path.join(self.carpeta_resultados, "componentes_fuertemente_conexas.csv")
        df_componentes.to_csv(ruta, index=False, encoding='utf-8-sig')
        print(f"\n   💾 Resumen guardado en: {ruta}")
        
        # Guardar detalle completo
        self._guardar_detalle_completo(componentes_fuertes, G)
        
        # Resumen
        articulos_en_grupos = sum(len(c) for c in componentes_fuertes if len(c) > 1)
        articulos_aislados = sum(1 for c in componentes_fuertes if len(c) == 1)
        
        print("\n📊 RESULTADO SUB-REQUISITO 3:")
        print(f"   • Componentes fuertemente conexas: {len(componentes_fuertes)}")
        print(f"   • Componente más grande: {len(componentes_fuertes[0])} artículos")
        print(f"   • Artículos en grupos temáticos: {articulos_en_grupos}")
        print(f"   • Artículos aislados: {articulos_aislados}")
        
        return componentes_fuertes
    
    def _guardar_detalle_completo(self, componentes, G):
        """Guarda detalles completos de cada componente"""
        detalles_completos = []
        
        for i, componente in enumerate(componentes[:20], 1):
            nodos_list = sorted(list(componente))
            
            for nodo in nodos_list:
                titulo = G.nodes[nodo].get('titulo', 'Sin título')
                if pd.isna(titulo):
                    titulo = f'Artículo {nodo}'
                
                autor = G.nodes[nodo].get('autor', 'Sin autor')
                if pd.isna(autor):
                    autor = 'Sin autor'
                
                detalles_completos.append({
                    'componente_id': i,
                    'tamaño_componente': len(componente),
                    'id_articulo': nodo,
                    'titulo': titulo,
                    'autor': autor,
                    'año': G.nodes[nodo].get('año', 'N/A')
                })
        
        df_detalles = pd.DataFrame(detalles_completos)
        ruta_detalles = os.path.join(self.carpeta_resultados, "componentes_detalle_completo.csv")
        df_detalles.to_csv(ruta_detalles, index=False, encoding='utf-8-sig')
        print(f"   💾 Detalles completos guardados en: {ruta_detalles}")
        print(f"      (Contiene TODOS los artículos de cada componente)")
    
    def analizar_componente(self, componente_id):
        """
        Analiza una componente específica en detalle
        Muestra todos los artículos y sus conexiones
        """
        if self.grafo is None:
            self.cargar_grafo()
        
        # Cargar componentes
        try:
            df = pd.read_csv(os.path.join(self.carpeta_resultados, "componentes_detalle_completo.csv"))
            
            componente_df = df[df['componente_id'] == componente_id]
            
            if len(componente_df) == 0:
                print(f"❌ Componente {componente_id} no encontrada")
                return
            
            print(f"\n{'='*70}")
            print(f"ANÁLISIS DETALLADO: COMPONENTE {componente_id}")
            print(f"{'='*70}")
            
            print(f"\n📊 Total de artículos: {len(componente_df)}\n")
            
            for idx, row in componente_df.iterrows():
                print(f"   [{row['id_articulo']}] {row['titulo'][:60]}...")
                print(f"      Autor: {row['autor'][:50]}")
                print(f"      Año: {row['año']}\n")
            
            # Analizar conexiones internas
            G = self.grafo
            nodos_componente = componente_df['id_articulo'].tolist()
            subgrafo = G.subgraph(nodos_componente)
            
            print(f"🔗 Conexiones internas:")
            print(f"   Aristas bidireccionales: {subgrafo.number_of_edges()}")
            print(f"   Densidad del grupo: {nx.density(subgrafo):.4f}")
            
        except FileNotFoundError:
            print("❌ Primero ejecuta identificar_componentes_fuertes()")
    
    def comparar_componentes(self, top_n=5):
        """
        Compara las principales componentes
        Muestra características de cada grupo
        """
        try:
            df = pd.read_csv(os.path.join(self.carpeta_resultados, "componentes_fuertemente_conexas.csv"))
            
            print(f"\n{'='*70}")
            print(f"COMPARACIÓN DE TOP {top_n} COMPONENTES")
            print(f"{'='*70}\n")
            
            for idx, row in df.head(top_n).iterrows():
                print(f"Componente {row['componente_id']}:")
                print(f"   • Tamaño: {row['num_articulos']} artículos")
                print(f"   • Tipo: {row['tipo']}")
                print(f"   • Primeros IDs: {row['nodos']}\n")
            
        except FileNotFoundError:
            print("❌ Primero ejecuta identificar_componentes_fuertes()")


if __name__ == "__main__":
    print("\n" + "="*70)
    print(" SUB-REQUISITO 3: COMPONENTES FUERTEMENTE CONEXAS")
    print("="*70)
    
    # Crear instancia
    analizador = ComponentesConexas()
    
    # Cargar grafo
    analizador.cargar_grafo()
    
    # Identificar componentes
    componentes = analizador.identificar_componentes_fuertes()
    
    # Comparar principales componentes
    print("\n" + "="*70)
    print(" COMPARACIÓN DE COMPONENTES")
    print("="*70)
    analizador.comparar_componentes(top_n=5)
    
    # Analizar componente más grande
    print("\n" + "="*70)
    print(" ANÁLISIS DETALLADO: COMPONENTE MÁS GRANDE")
    print("="*70)
    if len(componentes) > 0:
        analizador.analizar_componente(componente_id=1)
    
    print("\n" + "="*70)
    print(" ✅ SUB-REQUISITO 3 COMPLETADO")
    print("="*70)
    print("\n📁 Archivos generados:")
    print("   • componentes_fuertemente_conexas.csv")
    print("   • componentes_detalle_completo.csv")