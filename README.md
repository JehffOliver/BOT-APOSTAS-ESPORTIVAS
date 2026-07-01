# BOT-APOSTAS-ESPORTIVAS

Scanner de odds + alerta para estudar apostas esportivas com controle de risco.

> Objetivo: buscar odds via API, calcular uma chance estimada pelo consenso do mercado e destacar possiveis apostas de valor. Este projeto NAO faz apostas automaticamente.

## O que o bot faz nesta versao

- Busca jogos e odds pela The Odds API
- Mostra jogos disponiveis na interface web
- Calcula probabilidade implicita de cada odd
- Calcula uma chance estimada pelo consenso das casas, removendo margem de cada mercado
- Calcula edge e valor esperado
- Destaca alertas quando uma entrada passa nos filtros
- Mostra creditos restantes/uso da API quando a API retorna esses headers

## O que o bot nao faz

- Nao realiza aposta automaticamente
- Nao burla API, CAPTCHA, geolocalizacao, login ou termos de uso
- Nao garante lucro
- Nao usa martingale ou recuperacao agressiva

## Configurar chave da API

Crie uma conta/chave em:

```text
https://the-odds-api.com/
```

Depois crie um arquivo chamado `.env` na raiz do projeto. Voce pode copiar o exemplo:

```cmd
copy .env.example .env
```

Edite o `.env` e preencha:

```env
THE_ODDS_API_KEY=sua_chave_aqui
ODDS_SPORT=soccer_brazil_campeonato
ODDS_REGIONS=eu
ODDS_MARKETS=h2h
```

## Como executar no Windows

Abra o PowerShell ou CMD na pasta do projeto e rode:

```cmd
scripts\install.cmd
scripts\start.cmd
```

Acesse no navegador:

```text
http://127.0.0.1:8000
```

## Scripts disponiveis

```cmd
scripts\install.cmd  # cria/atualiza o .venv e instala dependencias
scripts\start.cmd    # inicia a aplicacao web
scripts\status.cmd   # verifica se esta online ou offline
scripts\stop.cmd     # para a aplicacao pela porta 8000
scripts\restart.cmd  # para e inicia novamente
```

## Como a chance estimada funciona

Para cada casa e mercado, o sistema transforma odds em probabilidades implicitas:

```text
probabilidade implicita = 1 / odd
```

Como as casas incluem margem, a soma das probabilidades geralmente passa de 100%. O sistema normaliza as probabilidades dentro de cada casa/mercado para tentar remover essa margem. Depois calcula uma media entre as casas disponiveis.

Essa media vira a coluna `Chance estimada`. Ela nao e previsao garantida; e uma leitura do consenso do mercado.

## Conceito principal

Exemplo:

- Odd: 2.10
- Probabilidade implicita: 1 / 2.10 = 47.62%
- Chance estimada pelo consenso: 52.00%
- Edge: 52.00% - 47.62% = 4.38 pontos percentuais

Se a chance estimada estiver correta, pode existir valor. Se a estimativa estiver errada, a aposta pode ser ruim mesmo parecendo boa.

## Filtros importantes

No `.env`:

```env
MIN_EDGE=0.03
MIN_EV=0.01
```

- `MIN_EDGE=0.03`: so alerta quando a chance estimada for pelo menos 3 pontos percentuais maior que a probabilidade implicita da odd.
- `MIN_EV=0.01`: so alerta quando o valor esperado for positivo acima do filtro.

## Estrutura

```text
src/
  main.py       Execucao simples em terminal antiga
  scanner.py    Calculos simples antigos
  odds_api.py   Integracao com The Odds API e analise de mercado
  web.py        Interface web via API

scripts/
  install.cmd
  start.cmd
  stop.cmd
  restart.cmd
  status.cmd
```

## Aviso

Apostas envolvem risco financeiro. Este projeto e apenas uma ferramenta de estudo/alerta e pode indicar oportunidades falsas se as probabilidades estimadas forem ruins. Aposte manualmente, com valor baixo, e nunca use martingale.
