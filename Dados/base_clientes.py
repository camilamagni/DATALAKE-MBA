import csv
import random
import sys

# ==========================================
# LISTAS DE NOMES, SOBRENOMES E CIDADES
# ==========================================

nomes = [
    "Andre", "Debora", "Rafael", "Felipe", "Tatiane",
    "Juliana", "Danilo", "Flavia", "Vinicius", "Beatriz",
    "Rodrigo", "Bruna", "Alexandre", "Renata", "Caio",
    "Kelly", "Marcos", "Camila", "Gabriel", "Mariana",
    "Lucas", "Patricia", "Eduardo", "Fernanda", "Ricardo",
    "Aline", "Bruno", "Larissa", "Thiago", "Amanda",
    "Carlos", "Ana", "Pedro", "Maria", "Joao",
    "Julia", "Gustavo", "Leticia", "Leonardo", "Isabela",
    "Matheus", "Carolina", "Diego", "Natalia", "Henrique",
    "Luana", "Fernando", "Bianca", "Marcelo", "Vanessa",
    "Rafael", "Priscila", "Fabio", "Cristina", "Daniel",
    "Monica", "Renan", "Sabrina", "Igor", "Elaine",
    "Alex", "Simone", "Victor", "Raquel", "Wesley",
    "Claudia", "Samuel", "Adriana", "Murilo", "Tatiana",
    "Vitor", "Carla", "Otavio", "Regina", "Arthur",
    "Manuela", "Enzo", "Helena", "Miguel", "Laura",
    "Davi", "Valentina", "Nicolas", "Alice", "Bernardo",
    "Sophia", "Theo", "Livia", "Heitor", "Melissa"
]

sobrenomes = [
    "Silva", "Santos", "Oliveira", "Souza", "Pereira",
    "Costa", "Rodrigues", "Almeida", "Nascimento", "Lima",
    "Araujo", "Fernandes", "Carvalho", "Gomes", "Martins",
    "Rocha", "Ribeiro", "Alves", "Monteiro", "Mendes",
    "Barbosa", "Freitas", "Barros", "Dias", "Castro",
    "Cardoso", "Teixeira", "Moreira", "Correia", "Moura",
    "Cavalcanti", "Pinto", "Ramos", "Macedo", "Miranda",
    "Nunes", "Machado", "Batista", "Marques", "Duarte",
    "Tavares", "Vieira", "Coelho", "Sales", "Farias",
    "Campos", "Andrade", "Borges", "Moraes", "Cunha",
    "Melo", "Guimaraes", "Bezerra", "Queiroz", "Rezende",
    "Medeiros", "Siqueira", "Vasconcelos", "Amaral", "Braga"
]

cidades = [
    ("São Paulo", "SP"), ("Rio de Janeiro", "RJ"),
    ("Belo Horizonte", "MG"), ("Curitiba", "PR"),
    ("Porto Alegre", "RS"), ("Salvador", "BA"),
    ("Recife", "PE"), ("Fortaleza", "CE"),
    ("Brasília", "DF"), ("Manaus", "AM")
]

# ==========================================
# GERADOR DE CLIENTES EM CSV
# ==========================================

def gerar_clientes(quantidade, arquivo="clientes.csv"):
    with open(arquivo, "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)

        # Cabeçalho
        escritor.writerow(["cliente_id", "nome", "cidade", "estado"])

        for i in range(quantidade):
            nome = random.choice(nomes)
            sobrenome = random.choice(sobrenomes)
            cidade, estado = random.choice(cidades)

            cliente_id = 505 + i
            nome_completo = f"{nome} {sobrenome}"

            escritor.writerow([cliente_id, nome_completo, cidade, estado])

    print("==========================================")
    print("   GERADOR DE CLIENTES (CSV)")
    print("==========================================")
    print(f"Registros gerados : {quantidade}")
    print(f"ID inicial        : 505")
    print(f"ID final          : {504 + quantidade}")
    print(f"Arquivo           : {arquivo}")
    print("==========================================")


# ==========================================
# PROGRAMA PRINCIPAL
# ==========================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python gerar_clientes.py <quantidade>")
        print()
        print("Exemplos:")
        print("  python gerar_clientes.py 1000")
        print("  python gerar_clientes.py 10000 clientes.csv")
        sys.exit(1)

    quantidade = int(sys.argv[1])
    arquivo = "clientes.csv"

    if len(sys.argv) >= 3:
        arquivo = sys.argv[2]

    gerar_clientes(quantidade, arquivo)
