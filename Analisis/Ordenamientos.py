import time
import random
import matplotlib
import matplotlib.pyplot as plt

# Forzar backend interactivo en VSCode
matplotlib.use("TkAgg")


class Ordenamientos:

    # 1. TimSort
    @staticmethod
    def timsort(arr):
        return sorted(arr)

    # 2. Comb Sort
    @staticmethod
    def comb_sort(arr):
        n = len(arr)
        gap = n
        shrink = 1.3
        sorted_ = False
        while not sorted_:
            gap = int(gap / shrink)
            if gap <= 1:
                gap = 1
                sorted_ = True
            i = 0
            while i + gap < n:
                if arr[i] > arr[i + gap]:
                    arr[i], arr[i + gap] = arr[i + gap], arr[i]
                    sorted_ = False
                i += 1
        return arr

    # 3. Selection Sort
    @staticmethod
    def selection_sort(arr):
        n = len(arr)
        for i in range(n):
            min_idx = i
            for j in range(i + 1, n):
                if arr[j] < arr[min_idx]:
                    min_idx = j
            arr[i], arr[min_idx] = arr[min_idx], arr[i]
        return arr

    # 4. Tree Sort
    class Node:
        def __init__(self, key):
            self.left = None
            self.right = None
            self.val = key

    @staticmethod
    def insert(root, key):
        if root is None:
            return Ordenamientos.Node(key)
        if key < root.val:
            root.left = Ordenamientos.insert(root.left, key)
        else:
            root.right = Ordenamientos.insert(root.right, key)
        return root

    @staticmethod
    def inorder(root, res):
        if root:
            Ordenamientos.inorder(root.left, res)
            res.append(root.val)
            Ordenamientos.inorder(root.right, res)

    @staticmethod
    def tree_sort(arr):
        if not arr:
            return []
        root = Ordenamientos.Node(arr[0])
        for i in arr[1:]:
            Ordenamientos.insert(root, i)
        res = []
        Ordenamientos.inorder(root, res)
        return res

    # 5. Pigeonhole Sort
    @staticmethod
    def pigeonhole_sort(arr):
        min_val = min(arr)
        max_val = max(arr)
        size = max_val - min_val + 1
        holes = [0] * size
        for x in arr:
            holes[x - min_val] += 1
        i = 0
        for count in range(size):
            while holes[count] > 0:
                arr[i] = count + min_val
                i += 1
                holes[count] -= 1
        return arr

    # 6. Bucket Sort
    @staticmethod
    def bucket_sort(arr):
        if len(arr) == 0:
            return arr
        bucket = []
        slot_num = 10
        for i in range(slot_num):
            bucket.append([])
        for j in arr:
            index_b = int(slot_num * j / (max(arr) + 1))
            bucket[index_b].append(j)
        for i in range(slot_num):
            bucket[i] = sorted(bucket[i])
        k = 0
        for i in range(slot_num):
            for j in range(len(bucket[i])):
                arr[k] = bucket[i][j]
                k += 1
        return arr

    # 7. QuickSort
    @staticmethod
    def quick_sort(arr):
        if len(arr) <= 1:
            return arr
        pivot = arr[len(arr) // 2]
        left = [x for x in arr if x < pivot]
        middle = [x for x in arr if x == pivot]
        right = [x for x in arr if x > pivot]
        return Ordenamientos.quick_sort(left) + middle + Ordenamientos.quick_sort(right)

    # 8. HeapSort
    @staticmethod
    def heapify(arr, n, i):
        largest = i
        l = 2 * i + 1
        r = 2 * i + 2
        if l < n and arr[i] < arr[l]:
            largest = l
        if r < n and arr[largest] < arr[r]:
            largest = r
        if largest != i:
            arr[i], arr[largest] = arr[largest], arr[i]
            Ordenamientos.heapify(arr, n, largest)

    @staticmethod
    def heap_sort(arr):
        n = len(arr)
        for i in range(n // 2 - 1, -1, -1):
            Ordenamientos.heapify(arr, n, i)
        for i in range(n - 1, 0, -1):
            arr[0], arr[i] = arr[i], arr[0]
            Ordenamientos.heapify(arr, i, 0)
        return arr

    # 9. Bitonic Sort
    @staticmethod
    def comp_and_swap(arr, i, j, dire):
        if (dire == 1 and arr[i] > arr[j]) or (dire == 0 and arr[i] < arr[j]):
            arr[i], arr[j] = arr[j], arr[i]

    @staticmethod
    def bitonic_merge(arr, low, cnt, dire):
        if cnt > 1:
            k = cnt // 2
            for i in range(low, low + k):
                Ordenamientos.comp_and_swap(arr, i, i + k, dire)
            Ordenamientos.bitonic_merge(arr, low, k, dire)
            Ordenamientos.bitonic_merge(arr, low + k, k, dire)

    @staticmethod
    def bitonic_sort(arr, low=0, cnt=None, dire=1):
        if cnt is None:
            cnt = len(arr)
        if cnt > 1:
            k = cnt // 2
            Ordenamientos.bitonic_sort(arr, low, k, 1)
            Ordenamientos.bitonic_sort(arr, low + k, k, 0)
            Ordenamientos.bitonic_merge(arr, low, cnt, dire)
        return arr

    # 10. Gnome Sort
    @staticmethod
    def gnome_sort(arr):
        n = len(arr)
        index = 0
        while index < n:
            if index == 0 or arr[index] >= arr[index - 1]:
                index += 1
            else:
                arr[index], arr[index - 1] = arr[index - 1], arr[index]
                index -= 1
        return arr

    # 11. Binary Insertion Sort
    @staticmethod
    def binary_insertion_sort(arr):
        def binary_search(subarr, val, start, end):
            if start == end:
                if subarr[start] > val:
                    return start
                else:
                    return start + 1
            if start > end:
                return start
            mid = (start + end) // 2
            if subarr[mid] < val:
                return binary_search(subarr, val, mid + 1, end)
            elif subarr[mid] > val:
                return binary_search(subarr, val, start, mid - 1)
            else:
                return mid

        for i in range(1, len(arr)):
            val = arr[i]
            j = binary_search(arr, val, 0, i - 1)
            arr = arr[:j] + [val] + arr[j:i] + arr[i + 1:]
        return arr

    # 12. Radix Sort
    @staticmethod
    def counting_sort(arr, exp1):
        n = len(arr)
        output = [0] * n
        count = [0] * 10
        for i in range(n):
            index = arr[i] // exp1
            count[index % 10] += 1
        for i in range(1, 10):
            count[i] += count[i - 1]
        i = n - 1
        while i >= 0:
            index = arr[i] // exp1
            output[count[index % 10] - 1] = arr[i]
            count[index % 10] -= 1
            i -= 1
        for i in range(len(arr)):
            arr[i] = output[i]

    @staticmethod
    def radix_sort(arr):
        max1 = max(arr)
        exp = 1
        while max1 // exp > 0:
            Ordenamientos.counting_sort(arr, exp)
            exp *= 10
        return arr


def benchmark_algorithms(n=5000):
    data = [random.randint(0, 10000) for _ in range(n)]

    algoritmos = {
        "TimSort": Ordenamientos.timsort,
        "Comb Sort": Ordenamientos.comb_sort,
        "Selection Sort": Ordenamientos.selection_sort,
        "Tree Sort": Ordenamientos.tree_sort,
        "Pigeonhole Sort": Ordenamientos.pigeonhole_sort,
        "BucketSort": Ordenamientos.bucket_sort,
        "QuickSort": Ordenamientos.quick_sort,
        "HeapSort": Ordenamientos.heap_sort,
        "Bitonic Sort": Ordenamientos.bitonic_sort,
        "Gnome Sort": Ordenamientos.gnome_sort,
        "Binary Insertion Sort": Ordenamientos.binary_insertion_sort,
        "RadixSort": Ordenamientos.radix_sort
    }

    resultados = []
    for nombre, algoritmo in algoritmos.items():
        arr = data.copy()
        inicio = time.time()
        algoritmo(arr)
        fin = time.time()
        resultados.append((nombre, n, round(fin - inicio, 6)))

    # Ordenar resultados ascendente por tiempo
    resultados.sort(key=lambda x: x[2])

    # Imprimir tabla alineada
    print("\n--- Resultados Benchmark ---")
    print(f"{'Método':<25}{'Tamaño':<15}{'Tiempo'}")
    for r in resultados:
        print(f"{r[0]:<25}{r[1]:<15}{r[2]}s")

    # Graficar
    nombres = [r[0] for r in resultados]
    tiempos = [r[2] for r in resultados]

    plt.barh(nombres, tiempos, color="skyblue")
    plt.xlabel("Tiempo (segundos)")
    plt.title("Comparación de Algoritmos de Ordenamiento (Ascendente)")
    plt.tight_layout()

    # Guardar imagen
    plt.savefig("ResultadosOrdenamientos.png")

    # Mostrar ventana y bloquear hasta cerrarla
    plt.show(block=True)
