# BOT-APOSTAS-ESPORTIVAS

Scanner de odds + alerta para estudar apostas esportivas com controle de risco.

> Objetivo: encontrar possiveis apostas de valor comparando a odd da casa com uma probabilidade estimada por modelo/analise. Este projeto NAO faz apostas automaticamente.

## O que o bot faz nesta primeira versao

- Le uma lista de odds de exemplo em CSV
- Calcula probabilidade implicita da odd
- Compara com uma probabilidade estimada
- Calcula edge e valor esperado
- Mostra alertas quando uma entrada passa nos filtros
- Pode enviar alerta via Telegram se configurado

## O que o bot nao faz

- Nao realiza aposta automaticamente
- Nao burla API, CAPTCHA, geolocalizacao, login ou termos de uso
- Nao garante lucro
- Nao usa martingale ou recuperacao agressiva

## Conceito principal

Exemplo:

- Odd: 2.10
- Probabilidade implicita: 1 / 2.10 = 47.62%
- Sua probabilidade estimada: 54.00%
- Edge: 54.00% - 47.62% = 6.38 pontos percentuais

Se a sua estimativa estiver correta, pode existir valor. Se a estimativa estiver errada, a aposta pode ser ruim mesmo parecendo boa.

## Como rodar localmente

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m src.main
```

No Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m src.main
```

## Estrutura

```text
src/
  main.py              Ponto de entrada
  config.py            Configuracoes por variaveis de ambiente
  scanner.py           Calcula probabilidade implicita, edge e EV
  telegram_alert.py    Envio opcional de alertas no Telegram

data/
  sample_odds.csv      Dados de exemplo para teste
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
