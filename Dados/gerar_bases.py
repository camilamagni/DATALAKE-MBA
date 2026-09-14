import subprocess
import sys


PROGRAMAS = [
    "base_clientes.py",
    "base_produtos.py",
    "base_pedidos.py"
]


def executar_programa(programa, quantidade):

    print()
    print("=" * 60)
    print(f"Executando: {programa}")
    print(f"Quantidade: {quantidade}")
    print("=" * 60)

    resultado = subprocess.run(
        [sys.executable, programa, str(quantidade)],
        capture_output=False
    )

    if resultado.returncode != 0:
        print()
        print(f"ERRO ao executar {programa}")
        return False

    print(f"{programa} executado com sucesso!")
    return True


def main():

    if len(sys.argv) < 2:

        print()
        print("Uso:")
        print("  python gerar_bases.py <quantidade>")
        print()
        print("Exemplo:")
        print("  python gerar_bases.py 10000")
        print()

        sys.exit(1)

    try:
        quantidade = int(sys.argv[1])
    except ValueError:
        print("ERRO: a quantidade deve ser um número inteiro.")
        sys.exit(1)

    if quantidade <= 0:
        print("ERRO: a quantidade deve ser maior que zero.")
        sys.exit(1)

    print()
    print("=" * 60)
    print("       GERADOR DE BASES - AWS ATHENA")
    print("=" * 60)
    print(f"Quantidade solicitada: {quantidade}")
    print("=" * 60)

    sucesso = True

    for programa in PROGRAMAS:

        resultado = executar_programa(
            programa,
            quantidade
        )

        if not resultado:
            sucesso = False

    print()
    print("=" * 60)

    if sucesso:
        print("TODAS AS BASES FORAM GERADAS COM SUCESSO!")
    else:
        print("ATENÇÃO: UMA OU MAIS BASES APRESENTARAM ERRO.")

    print("=" * 60)


if __name__ == "__main__":
    main()
