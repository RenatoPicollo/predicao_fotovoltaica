import requests
import datetime
import os
import json

class MetarData:
    def __init__(self, api_url, station_code):
        self.api_url = api_url
        self.station_code = station_code
        self.file_path = "/home/picolloiot/Documents/metar_log/metar_data_reg.csv"

    # Método para consultar a API e obter os dados
    def get_metar_data(self):        
        response = requests.get(self.api_url)
        print(response.status_code)
        print(response.text.strip())

        if response.status_code == 200:
            data = json.loads(response.text.strip())
            
            if data["data"]["total"] > 0:  # Verifica se há dados
                metar_message = data["data"]["data"][0]["mens"]
                return metar_message  # Retorna a mensagem METAR
            else:
                return "NO DATA AVAILABLE"
            
        else:
            return "NO DATA AVAILABLE"

    # Método para validar os dados METAR
    def validate_metar_data(self, metar_data):
        if metar_data.startswith(f"METAR {self.station_code}"):
            # Extrai o timestamp, ex: "091200Z"
            timestamp = metar_data.split()[2]
            day = timestamp[:2]
            hour = timestamp[2:4]

            # Pega o dia e a hora UTC atuais
            now_utc = datetime.datetime.utcnow()
            current_day = now_utc.strftime("%d")
            current_hour = now_utc.strftime("%H")

            # Valida se o dia e a hora batem com os valores UTC atuais
            if day == current_day and hour == current_hour:
                return True
        return False

    # Método para salvar os dados no arquivo .csv
    def save_to_file(self, metar_data):
        current_time_utc = datetime.datetime.utcnow().strftime("%d/%m/%Y %H:00")

        # Verifica se o arquivo existe e se contém a linha correta para a hora atual
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as file:
                lines = file.readlines()

            # Verifica se a última linha é "NO DATA AVAILABLE" e se é da hora corrente
            if lines:
                last_line = lines[-1]
                if "NO DATA AVAILABLE" in last_line and current_time_utc in last_line:
                    lines[-1] = f"{current_time_utc},{metar_data}\n"
                else:
                    lines.append(f"{current_time_utc},{metar_data}\n")
            else:
                lines.append(f"{current_time_utc},{metar_data}\n")

            # Sobrescreve o arquivo
            with open(self.file_path, 'w') as file:
                file.writelines(lines)
        else:
            # Cria um novo arquivo e escreve a primeira linha
            with open(self.file_path, 'w') as file:
                file.write(f"{current_time_utc},{metar_data}\n")

    # Método principal que faz todas as operações
    def process_metar(self):
        metar_data = self.get_metar_data()

        if self.validate_metar_data(metar_data):
            self.save_to_file(metar_data)
            print("file saved")
        else:
            self.save_to_file("NO DATA AVAILABLE")

# Classe para gerenciar a aplicação
class MetarApp:
    def __init__(self, api_url, station_code):
        self.metar_data = MetarData(api_url, station_code)

    # Método que inicia a aplicação
    def run(self):
        self.metar_data.process_metar()

# Executa o programa
if __name__ == "__main__":
    api_key = "ABTz2jQKZ2a6hbenG00IhXO48CvuHkM7KygTXtd7"  # Substitua pela sua KEY API
    api_url = f"https://api-redemet.decea.mil.br/mensagens/metar/SBSC?api_key={api_key}"
    station_code = "SBSC"

    app = MetarApp(api_url, station_code)
    app.run()
