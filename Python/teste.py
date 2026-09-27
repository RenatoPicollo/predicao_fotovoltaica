import requests

api_key = "ABTz2jQKZ2a6hbenG00IhXO48CvuHkM7KygTXtd7"
station = "SBSC"

url = f"https://api-redemet.decea.mil.br/mensagens/metar/{station}?api_key={api_key}"

print (requests.get(url).json()["data"]["data"][0]["mens"])

# teste de versionamento - versao 1.1