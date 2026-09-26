import pandas as pd

# Arquivos CSV
csv_1 = "pred_solar_teste.csv"
csv_2 = "previsao_gradient_boosting.csv"

# Leitura dos arquivos
df1 = pd.read_csv(csv_1, sep=",", decimal=".")
df2 = pd.read_csv(csv_2, sep=";", decimal=",")

# Soma da coluna prod
soma1 = df1["prod"].sum()
soma2 = df2["prod"].sum()

# Diferenças
diferenca = soma1 - soma2

if soma1 != 0:
    diferenca_percentual = (diferenca / soma1) * 100
else:
    diferenca_percentual = 0

# Exibição
print("=" * 50)
print("COMPARAÇÃO DE ENERGIA TOTAL")
print("=" * 50)
print(f"Arquivo 1: {csv_1}")
print(f"Soma de prod: {soma1:.2f}")
print()
print(f"Arquivo 2: {csv_2}")
print(f"Soma de prod: {soma2:.2f}")
print()
print(f"Diferença absoluta: {diferenca:.2f}")
print(f"Diferença percentual: {diferenca_percentual:.2f}%")
print("=" * 50)