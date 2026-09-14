import csv
import random
import sys
from datetime import date, timedelta


def gerar_pedidos(quantidade, arquivo="pedidos.csv"):

    data_inicial = date(2026, 1, 1)

    with open(arquivo, "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)

        # Cabeçalho
        escritor.writerow([
            "pedido_id",
            "cliente_id",
            "produto_id",
            "quantidade",
            "valor",
            "data_pedido"
        ])

        for i in range(quantidade):
            pedido_id = 1001 + i

            # Clientes válidos entre 501 e 1500
            cliente_id = random.randint(501, 1500)

            # 80% dos produtos válidos, 20% inválidos (fora da faixa 9001–10000)
            if random.random() < 0.8:
                produto_id = random.randint(9001, 10000)
            else:
                produto_id = random.randint(10001, 11000)  # anomalia

            # Quantidade: 90% positiva, 10% negativa (anomalia)
            if random.random() < 0.9:
                quantidade_produto = random.randint(1, 10)
            else:
                quantidade_produto = random.randint(-10, -1)  # anomalia

            # Preço unitário fictício
            preco_unitario = round(random.uniform(10.0, 5000.0), 2)

            # Valor total (mesmo que seja negativo, para simular anomalia)
            valor = round(quantidade_produto * preco_unitario, 2)

            # Data aleatória em 2026
            data_pedido = data_inicial + timedelta(days=random.randint(0, 364))

            escritor.writerow([
                pedido_id,
                cliente_id,
                produto_id,
                quantidade_produto,
                valor,
                data_pedido.isoformat()
            ])

    print("======================================")
    print("      GERADOR DE PEDIDOS (CSV)")
    print("======================================")
    print(f"Registros gerados: {quantidade}")
    print(f"Arquivo: {arquivo}")
    print(f"ID inicial: 1001")
    print(f"ID final: {1000 + quantidade}")
    print("======================================")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python gerar_pedidos.py <quantidade>")
        print()
        print("Exemplos:")
        print("  python gerar_pedidos.py 100")
        print("  python gerar_pedidos.py 1000")
        print("  python gerar_pedidos.py 100000 pedidos.csv")
        sys.exit(1)

    quantidade = int(sys.argv[1])
    arquivo = "pedidos.csv"

    if len(sys.argv) >= 3:
        arquivo = sys.argv[2]

    gerar_pedidos(quantidade, arquivo)
