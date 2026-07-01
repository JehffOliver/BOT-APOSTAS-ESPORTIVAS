# BOT-APOSTAS-ESPORTIVAS

Scanner de odds + alerta para estudar apostas esportivas com controle de risco.

> Objetivo: encontrar possiveis apostas de valor comparando a odd da casa com uma probabilidade estimada por modelo/analise. Este projeto NAO faz apostas automaticamente.

## O que o bot faz nesta primeira versao

- Le uma lista de odds em CSV
- Calcula probabilidade implicita da odd
- Compara com uma probabilidade estimada
- Calcula edge e valor esperado
- Mostra alertas quando uma entrada passa nos filtros
- Disponibiliza uma interface web local
- Permite enviar um novo CSV pela tela web

## O que o bot nao faz

- Nao realiza aposta automaticamente
- Nao burla API, CAPTCHA, geolocalizacao, login ou termos de uso
- Nao garante lucro
- Nao usa martingale ou recuperacao agressiva

## Como executar no Windows

Abra o PowerShell na pasta do projeto e rode:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Depois inicie a aplicacao:

```powershell
.\scripts\start.ps1
```

Acesse no navegador:

```text
http://127.0.0.1:8000
```

## Scripts disponiveis

```powershell
.\scripts\start.ps1    # inicia a aplicacao web
.\scripts\status.ps1   # verifica se esta online ou offline
.\scripts\stop.ps1     # para a aplicacao pela porta 8000
.\scripts\restart.ps1  # para e inicia novamente
```

Observacao: o script start.ps1 fica com o processo aberto na propria janela do PowerShell. Para parar, pressione Ctrl+C ou abra outro PowerShell na pasta do projeto e rode .\scripts\stop.ps1.

## Como executar pelo Python diretamente

```powershell
.venv\Scripts\activate
python -m uvicorn src.web:app --host 127.0.0.1 --port 8000
```

## Formato do CSV

O arquivo precisa ter estas colunas:

```csv
event,market,selection,bookmaker,odds,estimated_probability
Time A x Time B,Resultado Final,Time A,Casa Exemplo,2.10,0.54
```

Onde:

- odds: odd decimal da casa, exemplo 2.10
- estimated_probability: sua probabilidade estimada em decimal, exemplo 0.54 para 54%

## Conceito principal

Exemplo:

- Odd: 2.10
- Probabilidade implicita: 1 / 2.10 = 47.62%
- Sua probabilidade estimada: 54.00%
- Edge: 54.00% - 47.62% = 6.38 pontos percentuais

Se a sua estimativa estiver correta, pode existir valor. Se a estimativa estiver errada, a aposta pode ser ruim mesmo parecendo boa.

## Estrutura

```text
src/
  main.py      Execucao simples em terminal
  scanner.py   Calcula probabilidade implicita, edge e EV
  web.py       Interface web local

data/
  sample_odds.csv

scripts/
  start.ps1
  stop.ps1
  restart.ps1
  status.ps1
```

## Primeiro marco do projeto

1. Rodar com CSV de exemplo.
2. Trocar o CSV por uma fonte real de odds permitida.
3. Criar um modelo simples de probabilidade.
4. Comparar desempenho em historico.
5. So depois pensar em alerta real.

## Regra de banca sugerida para testes pequenos

- Banca inicial: R$ 10,00
- Entrada maxima: R$ 0,10 ou R$ 0,20
- Sem martingale
- Stop loss diario: R$ 2,00
- Stop win diario: R$ 2,00
- Aposta manual, sempre

## Aviso

Apostas envolvem risco financeiro. Este projeto e apenas uma ferramenta de estudo/alerta e pode indicar oportunidades falsas se as probabilidades estimadas forem ruins.
