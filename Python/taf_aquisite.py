import requests
import json
import pandas as pd


class TafData:

    def __init__(self, api_key, station):
        self.api_key = api_key
        self.station = station

    # ======================================================
    # BUSCAR TAF POR INTERVALO (CORRETO)
    # ======================================================
    def get_taf_range(self, start_dt, end_dt):

        url = (
            "https://api-redemet.decea.mil.br/mensagens/taf/"
            f"{self.station}"
            f"?api_key={self.api_key}"
            f"&data_ini={start_dt}"
            f"&data_fim={end_dt}"
        )

        response = requests.get(url)

        if response.status_code != 200:
            print("Erro API:", response.status_code)
            return pd.DataFrame()

        data = json.loads(response.text)

        if data["data"]["total"] == 0:
            print("Nenhum TAF encontrado")
            return pd.DataFrame()

        rows = []

        for item in data["data"]["data"]:
            rows.append({
                "estacao": item["id_localidade"],
                "validade_ini": item["validade_inicial"],
                "validade_fim": item["validade_final"],
                "taf": item["mens"],
                "recebimento": item.get("recebimento", None)
            })

        return pd.DataFrame(rows)


# ======================================================
# EXECUÇÃO
# ======================================================
if __name__ == "__main__":

    api_key = "ABTz2jQKZ2a6hbenG00IhXO48CvuHkM7KygTXtd7"
    station = "SBSC"

    taf = TafData(api_key, station)

    # intervalo REAL da API
    start = "2025090100"
    end   = "2025090923"

    df = taf.get_taf_range(start, end)
    df.to_csv("taf_historico.csv", index=False)

    print(df)