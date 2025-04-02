import subprocess
import json
import matplotlib.pyplot as plt

# Executa o student.py 10 vezes
for _ in range(10):
    subprocess.run(["python3", "student.py"])

# Lê o arquivo scores.json
with open('scores.json', 'r') as file:
    scores = json.load(file)

# Extrai os valores das pontuações
values = [score[1] for score in scores]

# Gera o gráfico de linhas
plt.figure()
plt.plot(range(1, len(values) + 1), values, marker='o')
plt.xlabel('Número de Jogos')
plt.ylabel('Pontuação')
plt.ylim(bottom=0)
plt.grid(False)
plt.title('Pontuação por Jogo')
plt.show()