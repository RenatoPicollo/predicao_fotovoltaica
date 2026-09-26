import csv
import re
from datetime import datetime

# ==========================================================
# CONFIGURAÇÃO DO PERÍODO DE PROCESSAMENTO
# ==========================================================

DATA_INICIO = datetime(2024, 10, 10, 0, 0)
DATA_FIM    = datetime(2025, 8, 31, 23, 00)

METAR_FILE = "metar_data_reg.csv"
PROD_FILE = "data_reg.csv"

OUTPUT_FILE = "pred_solar.csv"
INCOMPLETE_FILE = "incomplet_data.csv"

# ==========================================================
# PARÂMETROS DAS NUVENS
# ==========================================================

CLOUD_COVER = {
    "FEW": 1.5,
    "SCT": 3.5,
    "BKN": 6.0,
    "OVC": 8.0
}


def altitude_factor(height_ft):
    if height_ft < 2000:
        return 1.0
    elif height_ft <= 6000:
        return 0.6
    else:
        return 0.3


# ==========================================================
# PROCESSAMENTO METAR
# ==========================================================

def parse_metar(metar_text):

    cloud_regex = r'(FEW|SCT|BKN|OVC)(\d{3})'

    cloud_values = []

    for group, altitude in re.findall(cloud_regex, metar_text):

        altitude_ft = int(altitude) * 100

        value = CLOUD_COVER[group]
        factor = altitude_factor(altitude_ft)

        cloud_values.append(value * factor)

    if cloud_values:
        cloud_max = max(cloud_values)
        cloud_sum = sum(cloud_values)
        cloud_layers = len(cloud_values)
    else:
        cloud_max = 0
        cloud_sum = 0
        cloud_layers = 0

    # ------------------------------------------------------
    # Chuva
    # Detecta:
    # RA, -RA, +RA, SHRA, TSRA
    # Não detecta:
    # RERA, DZ, BR, etc.
    # ------------------------------------------------------

    chuva = 0

    rain_patterns = [
        r'\bRA\b',
        r'\+RA\b',
        r'\-RA\b',
        r'\bSHRA\b',
        r'\bTSRA\b'
    ]

    for pattern in rain_patterns:
        if re.search(pattern, metar_text):
            chuva = 1
            break

    # ------------------------------------------------------
    # Visibilidade
    # ------------------------------------------------------

    vis = None

    # Caso especial: CAVOK
    if "CAVOK" in metar_text:
        vis = 10000
    else:
        vis_match = re.search(r'\b(\d{4})\b', metar_text)

        if vis_match:
            vis = int(vis_match.group(1))

    # ------------------------------------------------------
    # Temperatura
    # Exemplo:
    # 22/20
    # M05/M07
    # ------------------------------------------------------

    temp = None

    temp_match = re.search(r'(M?\d{2})/(M?\d{2})', metar_text)

    if temp_match:

        temp_str = temp_match.group(1)

        if temp_str.startswith('M'):
            temp = -int(temp_str[1:])
        else:
            temp = int(temp_str)

    else:
        # ======================================================
        # CASO: temperatura ausente (///// ou inexistente)
        # ======================================================
        temp = None

    return {
        "cloud_max": round(cloud_max, 2),
        "cloud_sum": round(cloud_sum, 2),
        "cloud_layers": cloud_layers,
        "chuva": chuva,
        "vis": vis,
        "temp": temp
    }


# ==========================================================
# LEITURA DOS METAR
# ==========================================================

metar_data = {}
incomplete_data = []

with open(METAR_FILE, 'r', encoding='utf-8') as f:

    reader = csv.reader(f)

    for row in reader:

        try:

            if len(row) < 2:
                continue

            date_str = row[0].strip()
            metar_text = row[1].strip()

# ======================================================
# FILTRO DE METAR INVÁLIDO
# ======================================================

            invalid_metar = [
                "NO DATA AVAILABLE",
                "N/A",
                "NA",
                "NULL",
                "",
                "-"
            ]

            if metar_text.upper() in invalid_metar:
                continue

# proteção extra (casos tipo "NO DATA AVAILABLE ..." com texto extra)
            if "NO DATA AVAILABLE" in metar_text.upper():
                continue

            dt = datetime.strptime(date_str, "%d/%m/%Y %H:%M")

            if not (DATA_INICIO <= dt <= DATA_FIM):
                continue

            parsed = parse_metar(metar_text)

            key = (
                dt.year,
                dt.month,
                dt.day,
                dt.hour
            )

            metar_data[key] = parsed

        except Exception as e:
            print(f"Erro METAR: {row}")
            continue


# ==========================================================
# LEITURA PRODUÇÃO
# ==========================================================

prod_data = {}

with open(PROD_FILE, 'r', encoding='utf-8') as f:

    reader = csv.reader(f)

    for row in reader:

        try:

            if len(row) < 2:
                continue

            dt = datetime.strptime(
                row[0].strip(),
                "%Y-%m-%d %H:%M:%S"
            )

            if not (DATA_INICIO <= dt <= DATA_FIM):
                continue

            prod = float(row[1])

            key = (
                dt.year,
                dt.month,
                dt.day,
                dt.hour
            )

            prod_data[key] = prod

        except Exception:
            print(f"Erro PROD: {row}")
            continue


# ==========================================================
# CRUZAMENTO DOS DADOS
# ==========================================================

all_keys = set(metar_data.keys()) | set(prod_data.keys())

output_rows = []

for key in sorted(all_keys):

    ano, mes, dia, hora = key

    metar_exists = key in metar_data
    prod_exists = key in prod_data

    if metar_exists and prod_exists:

        metar = metar_data[key]

        output_rows.append([
            ano,
            mes,
            dia,
            hora,
            metar["cloud_max"],
            metar["cloud_sum"],
            metar["cloud_layers"],
            metar["chuva"],
            metar["vis"],
            metar["temp"],
            prod_data[key]
        ])

    else:

        incomplete_data.append([
            ano,
            mes,
            dia,
            hora,
            "prod" if metar_exists else "metar"
        ])


# ==========================================================
# SALVA pred_solar.csv
# ==========================================================

with open(
    OUTPUT_FILE,
    'w',
    newline='',
    encoding='utf-8'
) as f:

    writer = csv.writer(f)

    writer.writerow([
        "ano",
        "mes",
        "dia",
        "hora",
        "cloud_max",
        "cloud_sum",
        "cloud_layers",
        "chuva",
        "vis",
        "temp",
        "prod"
    ])

    writer.writerows(output_rows)


# ==========================================================
# SALVA incomplet_data.csv
# ==========================================================

with open(
    INCOMPLETE_FILE,
    'w',
    newline='',
    encoding='utf-8'
) as f:

    writer = csv.writer(f)

    writer.writerow([
        "ano",
        "mes",
        "dia",
        "hora",
        "type"
    ])

    writer.writerows(incomplete_data)


print()
print("===================================")
print(f"Dados válidos: {len(output_rows)}")
print(f"Dados incompletos: {len(incomplete_data)}")
print(f"Arquivo criado: {OUTPUT_FILE}")
print(f"Arquivo criado: {INCOMPLETE_FILE}")
print("===================================")
