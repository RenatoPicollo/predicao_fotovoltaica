import pandas as pd
import re

class TafToMetar:

    def __init__(self, arquivo_taf):
        self.df = pd.read_csv(arquivo_taf)

    # ==================================================
    # Extrair elementos básicos do TAF
    # ==================================================

    def parse_taf(self, taf):

        vento = ""
        visibilidade = "9999"
        nuvens = ""
        fenomeno = ""

        tx = None
        tn = None

        tokens = taf.split()

        for token in tokens:

            if re.match(r"^\d{5}(G\d{2,3})?KT$", token):
                vento = token

            elif re.match(r"^\d{4}$", token):
                visibilidade = token

            elif token.startswith(("FEW", "SCT", "BKN", "OVC")):
                nuvens = token

            elif token in [
                "BR",
                "RA",
                "-RA",
                "+RA",
                "TSRA",
                "DZ",
                "FG",
                "HZ"
            ]:
                fenomeno = token

            elif token == "CAVOK":
                visibilidade = "9999"
                nuvens = "NSC"

            # TX23/0111Z
            elif token.startswith("TX"):

                m = re.search(r"TX(\d+)", token)

                if m:
                    tx = int(m.group(1))

            # TN17/0109Z
            elif token.startswith("TN"):

                m = re.search(r"TN(\d+)", token)

                if m:
                    tn = int(m.group(1))

        # temperatura média
        if tx is not None and tn is not None:

            temperatura = round((tx + tn) / 2)

        elif tx is not None:

            temperatura = tx

        elif tn is not None:

            temperatura = tn

        else:

            temperatura = 20

        # aproximação do ponto de orvalho
        ponto_orvalho = temperatura - 2

        return {
            "vento": vento,
            "visibilidade": visibilidade,
            "nuvens": nuvens,
            "fenomeno": fenomeno,
            "temperatura": temperatura,
            "ponto_orvalho": ponto_orvalho
        }

    # ==================================================
    # Aplicar TEMPO / BECMG / PROB
    # ==================================================

    def aplicar_modificadores(self, taf, hora):

        visibilidade = None
        fenomeno = None
        nuvens = None

        tokens = taf.split()

        for i, token in enumerate(tokens):

            # PROB30 0106/0110
            if token.startswith(("PROB30", "PROB40")):

                if i + 1 < len(tokens):

                    periodo = tokens[i + 1]

                    if "/" in periodo:

                        ini = int(periodo[:4][2:])
                        fim = int(periodo[5:][2:])

                        if ini <= hora <= fim:

                            for j in range(i + 2, min(i + 10, len(tokens))):

                                tk = tokens[j]

                                if re.match(r"^\d{4}$", tk):
                                    visibilidade = tk

                                elif tk.startswith(("FEW", "SCT", "BKN", "OVC")):
                                    nuvens = tk

                                elif tk in [
                                    "BR",
                                    "RA",
                                    "-RA",
                                    "+RA",
                                    "TSRA",
                                    "DZ",
                                    "FG"
                                ]:
                                    fenomeno = tk

            # TEMPO 0118/0121
            elif token == "TEMPO":

                if i + 1 < len(tokens):

                    periodo = tokens[i + 1]

                    if "/" in periodo:

                        ini = int(periodo[:4][2:])
                        fim = int(periodo[5:][2:])

                        if ini <= hora <= fim:

                            for j in range(i + 2, min(i + 10, len(tokens))):

                                tk = tokens[j]

                                if re.match(r"^\d{4}$", tk):
                                    visibilidade = tk

                                elif tk.startswith(("FEW", "SCT", "BKN", "OVC")):
                                    nuvens = tk

                                elif tk in [
                                    "BR",
                                    "RA",
                                    "-RA",
                                    "+RA",
                                    "TSRA",
                                    "DZ",
                                    "FG"
                                ]:
                                    fenomeno = tk

        return visibilidade, nuvens, fenomeno

    # ==================================================
    # Gera METAR sintético
    # ==================================================

    def montar_metar(self, timestamp, dados):

        dia = timestamp.strftime("%d")
        hora = timestamp.strftime("%H")

        metar = (
            f"METAR SBSC "
            f"{dia}{hora}00Z "
            f"{dados['vento']} "
            f"{dados['visibilidade']} "
            f"{dados['nuvens']} "
            f"{dados['fenomeno']} "
            f"{dados['temperatura']}/{dados['ponto_orvalho']} "
            f"Q1013"
        )

        metar = " ".join(metar.split())

        return metar

    # ==================================================
    # Converter um TAF em horas
    # ==================================================

    def converter_taf(self, row):

        taf = row["taf"]

        inicio = pd.to_datetime(row["validade_ini"])
        fim = pd.to_datetime(row["validade_fim"])

        base = self.parse_taf(taf)

        registros = []

        horas = pd.date_range(
            start=inicio,
            end=fim - pd.Timedelta(hours=1),
            freq="h"
        )

        for instante in horas:

            hora = instante.hour

            vis, nuv, fen = self.aplicar_modificadores(
                taf,
                hora
            )

            dados = base.copy()

            if vis:
                dados["visibilidade"] = vis

            if nuv:
                dados["nuvens"] = nuv

            if fen:
                dados["fenomeno"] = fen

            metar = self.montar_metar(
                instante,
                dados
            )

            registros.append({
                "datahora":
                    instante.strftime("%d/%m/%Y %H:%M"),
                "metar":
                    metar
            })

        return registros

    # ==================================================
    # Executar conversão
    # ==================================================

    def run(self):

        todos = []

        for _, row in self.df.iterrows():

            registros = self.converter_taf(row)

            todos.extend(registros)

        resultado = pd.DataFrame(todos)

        resultado["datahora"] = pd.to_datetime(
            resultado["datahora"],
            format="%d/%m/%Y %H:%M"
        )

        resultado = (
            resultado
            .sort_values("datahora")
            .drop_duplicates(
                subset="datahora",
                keep="last"
            )
            .sort_values("datahora")
        )
        resultado["datahora"] = resultado["datahora"].dt.strftime("%d/%m/%Y %H:%M")

        return resultado


# ======================================================
# EXECUÇÃO
# ======================================================

arquivo_taf = "taf_historico.csv"

converter = TafToMetar(
    arquivo_taf
)

metar_like = converter.run()

print(metar_like.head(20))

# ======================================================
# EXPORTAR CSV
# ======================================================

metar_like.to_csv(
    "taf_as_metar.csv",
    index=False,
    encoding="utf-8-sig"
)

print(
    f"\nArquivo gerado com {len(metar_like)} registros."
)