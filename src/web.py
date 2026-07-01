from decimal import Decimal
from html import escape

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

from src.odds_api import OddsApiSettings, get_live_analysis, load_odds_settings

app = FastAPI(title='Scanner de Odds')


def pct(value: Decimal) -> str:
    return f'{(value * Decimal("100")):.2f}%'


def money(value: Decimal) -> str:
    return f'{value:.4f}'


def selected(current: str, value: str) -> str:
    return 'selected' if current == value else ''


@app.get('/health')
def health() -> dict:
    return {'status': 'online'}


@app.get('/api/odds')
def api_odds(
    sport: str | None = Query(default=None),
    regions: str | None = Query(default=None),
    markets: str | None = Query(default=None),
) -> dict:
    settings = load_odds_settings()
    if sport:
        settings = OddsApiSettings(**{**settings.__dict__, 'sport': sport})
    if regions:
        settings = OddsApiSettings(**{**settings.__dict__, 'regions': regions})
    if markets:
        settings = OddsApiSettings(**{**settings.__dict__, 'markets': markets})

    rows, quota = get_live_analysis(settings)
    return {
        'settings': {
            'sport': settings.sport,
            'regions': settings.regions,
            'markets': settings.markets,
            'min_edge': str(settings.min_edge),
            'min_ev': str(settings.min_ev),
        },
        'quota': quota,
        'count': len(rows),
        'alerts': len([row for row in rows if row['approved']]),
        'rows': rows[:200],
    }


@app.get('/', response_class=HTMLResponse)
def home(
    sport: str | None = None,
    regions: str | None = None,
    markets: str | None = None,
) -> str:
    settings = load_odds_settings()
    if sport:
        settings = OddsApiSettings(**{**settings.__dict__, 'sport': sport})
    if regions:
        settings = OddsApiSettings(**{**settings.__dict__, 'regions': regions})
    if markets:
        settings = OddsApiSettings(**{**settings.__dict__, 'markets': markets})

    error = ''
    quota = {'remaining': '', 'used': '', 'last': ''}
    results = []

    try:
        results, quota = get_live_analysis(settings)
    except Exception as exc:
        error = str(exc)

    alerts = [item for item in results if item['approved']]

    rows_html = ''
    for item in results[:200]:
        css = 'ok' if item['approved'] else 'no'
        status = 'ALERTA' if item['approved'] else 'OBSERVAR'
        chance_label = 'Chance estimada pelo mercado'
        if item['selection'] == item.get('home_team'):
            chance_label = 'Chance estimada de vitoria do mandante'
        elif item['selection'] == item.get('away_team'):
            chance_label = 'Chance estimada de vitoria do visitante'
        elif item['selection'].lower() == 'draw':
            chance_label = 'Chance estimada de empate'

        rows_html += f'''
        <tr class="{css}">
          <td><strong>{status}</strong></td>
          <td>{escape(item['event'])}<br><small>{escape(item['commence_time'])}</small></td>
          <td>{escape(item['market'])}</td>
          <td>{escape(item['selection'])}<br><small>{chance_label}</small></td>
          <td>{escape(item['bookmaker'])}</td>
          <td>{item['odds']:.2f}</td>
          <td>{pct(item['bookmaker_probability'])}</td>
          <td>{pct(item['estimated_probability'])}</td>
          <td>{pct(item['edge'])}</td>
          <td>{money(item['expected_value'])}</td>
          <td>{item['bookmakers_count']}</td>
        </tr>
        '''

    if not rows_html and not error:
        rows_html = '<tr><td colspan="11">Nenhum jogo retornado para esses filtros.</td></tr>'

    error_html = ''
    if error:
        error_html = f'''
        <div class="card error">
          <h2>Configuracao pendente ou erro na API</h2>
          <p>{escape(error)}</p>
          <p>Crie um arquivo <strong>.env</strong> na raiz do projeto com sua chave:</p>
          <pre>THE_ODDS_API_KEY=sua_chave_aqui
ODDS_SPORT=soccer_brazil_campeonato
ODDS_REGIONS=eu
ODDS_MARKETS=h2h</pre>
        </div>
        '''

    return f'''
    <!doctype html>
    <html lang="pt-br">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <meta http-equiv="refresh" content="120">
      <title>Scanner de Odds</title>
      <style>
        body {{ font-family: Arial, sans-serif; margin: 24px; background: #f6f7f9; color: #111; }}
        .card {{ background: white; border-radius: 12px; padding: 20px; margin-bottom: 16px; box-shadow: 0 2px 10px rgba(0,0,0,.06); }}
        h1 {{ margin-top: 0; }}
        table {{ width: 100%; border-collapse: collapse; background: white; }}
        th, td {{ padding: 10px; border-bottom: 1px solid #ddd; text-align: left; font-size: 14px; vertical-align: top; }}
        th {{ background: #222; color: white; position: sticky; top: 0; }}
        .ok {{ background: #e9f9ee; }}
        .no {{ background: #fff; }}
        .badge {{ display: inline-block; padding: 6px 10px; border-radius: 999px; background: #eee; margin: 3px 8px 3px 0; }}
        .warn {{ color: #8a5a00; }}
        .error {{ border-left: 6px solid #b00020; }}
        input, select, button {{ padding: 10px; margin-right: 8px; }}
        button {{ cursor: pointer; }}
        small {{ color: #555; }}
        pre {{ background: #111; color: #eee; padding: 12px; border-radius: 8px; overflow: auto; }}
      </style>
    </head>
    <body>
      <div class="card">
        <h1>Scanner de Odds via API</h1>
        <span class="badge">Status: online</span>
        <span class="badge">Entradas analisadas: {len(results)}</span>
        <span class="badge">Alertas: {len(alerts)}</span>
        <span class="badge">Creditos restantes API: {escape(quota.get('remaining', ''))}</span>
        <span class="badge">Creditos usados: {escape(quota.get('used', ''))}</span>
        <p class="warn">Ferramenta de estudo e alerta. Ela nao aposta automaticamente e nao garante lucro. A chance estimada e uma leitura de consenso das odds do mercado, nao uma previsao certa.</p>
      </div>

      <div class="card">
        <h2>Filtros</h2>
        <form method="get" action="/">
          <label>Campeonato/esporte</label>
          <select name="sport">
            <option value="soccer_brazil_campeonato" {selected(settings.sport, 'soccer_brazil_campeonato')}>Brasileirao Serie A</option>
            <option value="soccer_brazil_campeonato_b" {selected(settings.sport, 'soccer_brazil_campeonato_b')}>Brasileirao Serie B</option>
            <option value="soccer_epl" {selected(settings.sport, 'soccer_epl')}>Premier League</option>
            <option value="soccer_spain_la_liga" {selected(settings.sport, 'soccer_spain_la_liga')}>La Liga</option>
            <option value="soccer_italy_serie_a" {selected(settings.sport, 'soccer_italy_serie_a')}>Serie A Italia</option>
            <option value="soccer_germany_bundesliga" {selected(settings.sport, 'soccer_germany_bundesliga')}>Bundesliga</option>
            <option value="soccer_france_ligue_one" {selected(settings.sport, 'soccer_france_ligue_one')}>Ligue 1</option>
            <option value="upcoming" {selected(settings.sport, 'upcoming')}>Proximos eventos gerais</option>
          </select>

          <label>Regiao</label>
          <select name="regions">
            <option value="eu" {selected(settings.regions, 'eu')}>Europa</option>
            <option value="uk" {selected(settings.regions, 'uk')}>Reino Unido</option>
            <option value="us" {selected(settings.regions, 'us')}>Estados Unidos</option>
            <option value="au" {selected(settings.regions, 'au')}>Australia</option>
          </select>

          <label>Mercado</label>
          <select name="markets">
            <option value="h2h" {selected(settings.markets, 'h2h')}>Resultado final / vitoria do time</option>
            <option value="totals" {selected(settings.markets, 'totals')}>Mais/Menos gols</option>
            <option value="h2h,totals" {selected(settings.markets, 'h2h,totals')}>Resultado + Mais/Menos</option>
          </select>

          <button type="submit">Atualizar analise</button>
        </form>
      </div>

      {error_html}

      <div class="card">
        <h2>Oportunidades calculadas</h2>
        <table>
          <thead>
            <tr>
              <th>Status</th><th>Jogo</th><th>Mercado</th><th>Selecao</th><th>Casa</th>
              <th>Odd</th><th>Prob. da odd</th><th>Chance estimada</th><th>Edge</th><th>EV</th><th>Amostras</th>
            </tr>
          </thead>
          <tbody>{rows_html}</tbody>
        </table>
      </div>
    </body>
    </html>
    '''
