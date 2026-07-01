from decimal import Decimal
import csv
from pathlib import Path

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse

from src.scanner import analyze_row

app = FastAPI(title='Scanner de Odds')
DATA_FILE = Path('data/sample_odds.csv')
MIN_EDGE = Decimal('0.03')
MIN_EV = Decimal('0.01')


def pct(value: Decimal) -> str:
    return f'{(value * Decimal("100")):.2f}%'


def load_results() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    with DATA_FILE.open(newline='', encoding='utf-8') as file:
        rows = list(csv.DictReader(file))
    return [analyze_row(row, MIN_EDGE, MIN_EV) for row in rows]


@app.get('/health')
def health() -> dict:
    return {'status': 'online'}


@app.get('/', response_class=HTMLResponse)
def home() -> str:
    results = load_results()
    alerts = [item for item in results if item['approved']]

    rows_html = ''
    for item in results:
        css = 'ok' if item['approved'] else 'no'
        status = 'ALERTA' if item['approved'] else 'IGNORAR'
        rows_html += f'''
        <tr class="{css}">
          <td>{status}</td>
          <td>{item['event']}</td>
          <td>{item['market']}</td>
          <td>{item['selection']}</td>
          <td>{item['bookmaker']}</td>
          <td>{Decimal(str(item['odds'])):.2f}</td>
          <td>{pct(item['implied_probability'])}</td>
          <td>{pct(Decimal(str(item['estimated_probability'])))}</td>
          <td>{pct(item['edge'])}</td>
          <td>{item['expected_value']:.4f}</td>
        </tr>
        '''

    return f'''
    <!doctype html>
    <html lang="pt-br">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Scanner de Odds</title>
      <style>
        body {{ font-family: Arial, sans-serif; margin: 24px; background: #f6f7f9; color: #111; }}
        .card {{ background: white; border-radius: 12px; padding: 20px; margin-bottom: 16px; box-shadow: 0 2px 10px rgba(0,0,0,.06); }}
        h1 {{ margin-top: 0; }}
        table {{ width: 100%; border-collapse: collapse; background: white; }}
        th, td {{ padding: 10px; border-bottom: 1px solid #ddd; text-align: left; font-size: 14px; }}
        th {{ background: #222; color: white; position: sticky; top: 0; }}
        .ok {{ background: #e9f9ee; }}
        .no {{ background: #fff; }}
        .badge {{ display: inline-block; padding: 6px 10px; border-radius: 999px; background: #eee; margin-right: 8px; }}
        .warn {{ color: #8a5a00; }}
        input, button {{ padding: 10px; }}
        button {{ cursor: pointer; }}
      </style>
    </head>
    <body>
      <div class="card">
        <h1>Scanner de Odds</h1>
        <span class="badge">Status: online</span>
        <span class="badge">Entradas analisadas: {len(results)}</span>
        <span class="badge">Alertas: {len(alerts)}</span>
        <p class="warn">Ferramenta de estudo e alerta. Ela nao aposta automaticamente e nao garante lucro.</p>
      </div>

      <div class="card">
        <h2>Enviar CSV</h2>
        <p>Colunas esperadas: event, market, selection, bookmaker, odds, estimated_probability</p>
        <form action="/upload" method="post" enctype="multipart/form-data">
          <input type="file" name="file" accept=".csv" required>
          <button type="submit">Atualizar dados</button>
        </form>
      </div>

      <div class="card">
        <h2>Resultado</h2>
        <table>
          <thead>
            <tr>
              <th>Status</th><th>Evento</th><th>Mercado</th><th>Selecao</th><th>Casa</th>
              <th>Odd</th><th>Prob. implicita</th><th>Prob. estimada</th><th>Edge</th><th>EV</th>
            </tr>
          </thead>
          <tbody>{rows_html}</tbody>
        </table>
      </div>
    </body>
    </html>
    '''


@app.post('/upload')
async def upload(file: UploadFile = File(...)):
    DATA_FILE.parent.mkdir(exist_ok=True)
    content = await file.read()
    DATA_FILE.write_bytes(content)
    return RedirectResponse('/', status_code=303)
