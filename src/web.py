from decimal import Decimal, InvalidOperation
from html import escape

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

from src.odds_api import (
    OddsApiSettings,
    filter_opportunities,
    get_live_analysis,
    load_odds_settings,
)

app = FastAPI(title='Scanner de Odds')


def pct(value: Decimal) -> str:
    return f'{(value * Decimal("100")):.2f}%'


def money(value: Decimal) -> str:
    return f'{value:.4f}'


def selected(current: str, value: str) -> str:
    return 'selected' if current == value else ''


def checked(value: bool) -> str:
    return 'checked' if value else ''


def decimal_query(value: str | None) -> Decimal | None:
    if value is None or value.strip() == '':
        return None
    try:
        return Decimal(value.replace(',', '.'))
    except InvalidOperation:
        return None


def int_query(value: str | None) -> int | None:
    if value is None or value.strip() == '':
        return None
    try:
        return int(value)
    except ValueError:
        return None


@app.get('/health')
def health() -> dict:
    return {'status': 'online'}


@app.get('/api/odds')
def api_odds(
    sport: str | None = Query(default=None),
    regions: str | None = Query(default=None),
    markets: str | None = Query(default=None),
    only_alerts: bool = Query(default=False),
    min_edge: str | None = Query(default=None),
    min_ev: str | None = Query(default=None),
    min_bookmakers: str | None = Query(default=None),
    min_odds: str | None = Query(default=None),
    max_odds: str | None = Query(default=None),
    bookmaker: str | None = Query(default=None),
    search: str | None = Query(default=None),
) -> dict:
    settings = load_odds_settings()
    if sport:
        settings = OddsApiSettings(**{**settings.__dict__, 'sport': sport})
    if regions:
        settings = OddsApiSettings(**{**settings.__dict__, 'regions': regions})
    if markets:
        settings = OddsApiSettings(**{**settings.__dict__, 'markets': markets})

    rows, quota = get_live_analysis(settings)
    filtered = filter_opportunities(
        rows,
        only_alerts=only_alerts,
        min_edge=decimal_query(min_edge),
        min_ev=decimal_query(min_ev),
        min_bookmakers=int_query(min_bookmakers),
        min_odds=decimal_query(min_odds),
        max_odds=decimal_query(max_odds),
        bookmaker=bookmaker,
        selection_contains=search,
    )
    return {
        'settings': {
            'sport': settings.sport,
            'regions': settings.regions,
            'markets': settings.markets,
            'min_edge': str(settings.min_edge),
            'min_ev': str(settings.min_ev),
            'min_bookmakers': settings.min_bookmakers,
        },
        'quota': quota,
        'count': len(rows),
        'filtered_count': len(filtered),
        'alerts': len([row for row in rows if row['approved']]),
        'rows': filtered[:200],
    }


@app.get('/', response_class=HTMLResponse)
def home(
    sport: str | None = None,
    regions: str | None = None,
    markets: str | None = None,
    only_alerts: bool = False,
    min_edge: str | None = None,
    min_ev: str | None = None,
    min_bookmakers: str | None = None,
    min_odds: str | None = None,
    max_odds: str | None = None,
    bookmaker: str | None = None,
    search: str | None = None,
) -> str:
    settings = load_odds_settings()
    if sport:
        settings = OddsApiSettings(**{**settings.__dict__, 'sport': sport})
    if regions:
        settings = OddsApiSettings(**{**settings.__dict__, 'regions': regions})
    if markets:
        settings = OddsApiSettings(**{**settings.__dict__, 'markets': markets})

    filter_min_edge = decimal_query(min_edge)
    filter_min_ev = decimal_query(min_ev)
    filter_min_bookmakers = int_query(min_bookmakers)
    filter_min_odds = decimal_query(min_odds)
    filter_max_odds = decimal_query(max_odds)

    error = ''
    quota = {'remaining': '', 'used': '', 'last': ''}
    all_results = []
    results = []

    try:
        all_results, quota = get_live_analysis(settings)
        results = filter_opportunities(
            all_results,
            only_alerts=only_alerts,
            min_edge=filter_min_edge,
            min_ev=filter_min_ev,
            min_bookmakers=filter_min_bookmakers,
            min_odds=filter_min_odds,
            max_odds=filter_max_odds,
            bookmaker=bookmaker,
            selection_contains=search,
        )
    except Exception as exc:
        error = str(exc)

    alerts = [item for item in all_results if item['approved']]

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

        method_label = 'Consenso das outras casas' if item['method'] == 'consenso_sem_a_casa_atual' else 'Consenso incluindo a propria casa'
        explanation = (
            f"Odd {item['odds']:.2f} implica {pct(item['bookmaker_probability'])}. "
            f"O consenso sem margem estimou {pct(item['estimated_probability'])}. "
            f"Diferenca: {pct(item['edge'])}."
        )

        rows_html += f'''
        <tr class="{css}">
          <td><strong>{status}</strong><br><small>Confianca: {escape(item['confidence'])}</small></td>
          <td>{escape(item['event'])}<br><small>{escape(item['commence_time'])}</small></td>
          <td>{escape(item['market'])}</td>
          <td>{escape(item['selection'])}<br><small>{chance_label}</small></td>
          <td>{escape(item['bookmaker'])}<br><small>Atualizado: {escape(item.get('bookmaker_last_update', ''))}</small></td>
          <td>{item['odds']:.2f}</td>
          <td>{pct(item['bookmaker_probability'])}</td>
          <td>{pct(item['estimated_probability'])}</td>
          <td>{pct(item['edge'])}</td>
          <td>{money(item['expected_value'])}</td>
          <td>{item['bookmakers_count']}</td>
          <td><small>{escape(method_label)}<br>{escape(explanation)}</small></td>
        </tr>
        '''

    if not rows_html and not error:
        rows_html = '<tr><td colspan="12">Nenhum jogo retornado para esses filtros.</td></tr>'

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

    min_edge_value = escape(min_edge or '')
    min_ev_value = escape(min_ev or '')
    min_bookmakers_value = escape(min_bookmakers or '')
    min_odds_value = escape(min_odds or '')
    max_odds_value = escape(max_odds or '')
    bookmaker_value = escape(bookmaker or '')
    search_value = escape(search or '')

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
        input, select, button {{ padding: 10px; margin: 4px 8px 8px 0; }}
        button {{ cursor: pointer; }}
        small {{ color: #555; }}
        pre {{ background: #111; color: #eee; padding: 12px; border-radius: 8px; overflow: auto; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 10px; align-items: end; }}
        .field label {{ display: block; font-weight: bold; margin-bottom: 4px; }}
        .field input, .field select {{ width: 100%; box-sizing: border-box; }}
        .help {{ background: #f0f4ff; border-left: 6px solid #4263eb; }}
      </style>
    </head>
    <body>
      <div class="card">
        <h1>Scanner de Odds via API</h1>
        <span class="badge">Status: online</span>
        <span class="badge">Entradas retornadas: {len(all_results)}</span>
        <span class="badge">Entradas filtradas: {len(results)}</span>
        <span class="badge">Alertas: {len(alerts)}</span>
        <span class="badge">Creditos restantes API: {escape(quota.get('remaining', ''))}</span>
        <span class="badge">Creditos usados: {escape(quota.get('used', ''))}</span>
        <p class="warn">Ferramenta de estudo e alerta. Ela nao aposta automaticamente e nao garante lucro. A chance estimada e uma leitura de consenso das odds do mercado, nao uma previsao certa.</p>
      </div>

      <div class="card help">
        <h2>Como o calculo funciona hoje</h2>
        <p><strong>Chance estimada</strong>: o sistema pega as odds de varias casas, transforma em probabilidades, remove a margem dentro de cada mercado e tira uma media. Ao avaliar uma casa especifica, tenta usar o consenso das outras casas para evitar comparar a casa com ela mesma.</p>
        <p><strong>Edge</strong>: diferenca entre a chance estimada e a probabilidade implicita da odd. <strong>EV</strong>: valor esperado teorico. Isso ainda nao considera escalação, lesoes, momento, tabela, xG, clima ou noticias.</p>
      </div>

      <div class="card">
        <h2>Filtros</h2>
        <form method="get" action="/">
          <div class="grid">
            <div class="field">
              <label>Campeonato/esporte</label>
              <select name="sport">
                <option value="soccer_brazil_campeonato" {selected(settings.sport, 'soccer_brazil_campeonato')}>Brasileirao Serie A</option>
                <option value="soccer_brazil_campeonato_b" {selected(settings.sport, 'soccer_brazil_campeonato_b')}>Brasileirao Serie B</option>
                <option value="soccer_epl" {selected(settings.sport, 'soccer_epl')}>Premier League</option>
                <option value="soccer_spain_la_liga" {selected(settings.sport, 'soccer_spain_la_liga')}>La Liga</option>
                <option value="soccer_italy_serie_a" {selected(settings.sport, 'soccer_italy_serie_a')}>Serie A Italia</option>
                <option value="soccer_germany_bundesliga" {selected(settings.sport, 'soccer_germany_bundesliga')}>Bundesliga</option>
                <option value="soccer_france_ligue_one" {selected(settings.sport, 'soccer_france_ligue_one')}>Ligue 1</option>
                <option value="soccer_usa_mls" {selected(settings.sport, 'soccer_usa_mls')}>MLS</option>
                <option value="upcoming" {selected(settings.sport, 'upcoming')}>Proximos eventos gerais</option>
              </select>
            </div>

            <div class="field">
              <label>Regiao</label>
              <select name="regions">
                <option value="eu" {selected(settings.regions, 'eu')}>Europa</option>
                <option value="uk" {selected(settings.regions, 'uk')}>Reino Unido</option>
                <option value="us" {selected(settings.regions, 'us')}>Estados Unidos</option>
                <option value="au" {selected(settings.regions, 'au')}>Australia</option>
                <option value="eu,uk" {selected(settings.regions, 'eu,uk')}>Europa + Reino Unido</option>
                <option value="us,eu" {selected(settings.regions, 'us,eu')}>Estados Unidos + Europa</option>
              </select>
            </div>

            <div class="field">
              <label>Mercado</label>
              <select name="markets">
                <option value="h2h" {selected(settings.markets, 'h2h')}>Resultado final / vitoria do time</option>
                <option value="totals" {selected(settings.markets, 'totals')}>Mais/Menos gols</option>
                <option value="spreads" {selected(settings.markets, 'spreads')}>Handicap / spreads</option>
                <option value="h2h,totals" {selected(settings.markets, 'h2h,totals')}>Resultado + Mais/Menos</option>
              </select>
            </div>

            <div class="field">
              <label>Buscar time/selecao</label>
              <input name="search" value="{search_value}" placeholder="ex: Flamengo">
            </div>

            <div class="field">
              <label>Filtrar casa</label>
              <input name="bookmaker" value="{bookmaker_value}" placeholder="ex: FanDuel">
            </div>

            <div class="field">
              <label>Edge minimo</label>
              <input name="min_edge" value="{min_edge_value}" placeholder="0.03">
            </div>

            <div class="field">
              <label>EV minimo</label>
              <input name="min_ev" value="{min_ev_value}" placeholder="0.01">
            </div>

            <div class="field">
              <label>Minimo de casas</label>
              <input name="min_bookmakers" value="{min_bookmakers_value}" placeholder="4">
            </div>

            <div class="field">
              <label>Odd minima</label>
              <input name="min_odds" value="{min_odds_value}" placeholder="1.50">
            </div>

            <div class="field">
              <label>Odd maxima</label>
              <input name="max_odds" value="{max_odds_value}" placeholder="3.50">
            </div>

            <div class="field">
              <label>Somente alertas</label>
              <input type="checkbox" name="only_alerts" value="true" {checked(only_alerts)}>
            </div>
          </div>
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
              <th>Odd</th><th>Prob. da odd</th><th>Chance estimada</th><th>Edge</th><th>EV</th><th>Amostras</th><th>Metodo</th>
            </tr>
          </thead>
          <tbody>{rows_html}</tbody>
        </table>
      </div>
    </body>
    </html>
    '''
