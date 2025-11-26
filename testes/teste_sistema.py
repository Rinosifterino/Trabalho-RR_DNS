import requests
import time

# Este endereço só funciona DENTRO do Docker, graças ao seu container DNS
url = "http://www.dns___.com.br/"

print(f"--- Iniciando teste de carga para: {url} ---")
print("Tentando provar o balanceamento de carga (Round Robin)...")
print("-" * 50)

for i in range(1, 11):
    try:
        # Faz a requisição para o DNS
        response = requests.get(url, timeout=2)
        
        if response.status_code == 200:
            data = response.json()
            # O backend retorna {"server": "Servidor_XX"}
            servidor = data.get('server', 'Desconhecido')
            print(f"Requisição {i:02d}: Atendida por -> {servidor}")
        else:
            print(f"Requisição {i:02d}: Erro {response.status_code}")
            
    except Exception as e:
        print(f"Requisição {i:02d}: Falha ao conectar - {e}")
    
    # Espera um pouquinho entre as requisições
    time.sleep(1)

print("-" * 50)
print("Teste finalizado.")