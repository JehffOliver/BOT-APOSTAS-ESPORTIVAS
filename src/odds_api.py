from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import os
from typing import Any

import requests
from dotenv import load_dotenv


API_HOST = 'https://api.the-odds-api.com'


@dataclass(frozen=True)
class OddsApiSettings:
    api_key: str | None
    sport: str
    regions: str
    markets: str
    odds_format: str
    bookmakers: str | None
    min_edge: Decimal
    min_ev: Decimal
    min_bookmakers: int


def decimal_env(name: str, default: str) -> Decimal:
    value = os.getenv(name, default).strip().replace(',', '.')
    try:
        return Decimal(value)
    except InvalidOperation:
        return Decimal(default)


def int_env(name: str, default: str) -> int:
    value = os.getenv(name, default).strip()
    try:
        return int(value)
    except ValueError:
        return int(default)


def load_odds_settings() -> OddsApiSettings:
    load_dotenv()
    return OddsApiSettings(
        api_key=os.getenv('THE_ODDS_API_KEY') or None,
        sport=os.getenv('ODDS_SPORT', 'soccer_brazil_campeonato'),
        regions=os.getenv('ODDS_REGIONS', 'eu'),
        markets=os.getenv('ODDS_MARKETS', 'h2h'),
        odds_format=os.getenv('ODDS_FORMAT', 'decimal'),
        bookmakers=os.getenv('ODDS_BOOKMAKERS') or None,
        min_edge=decimal_env('MIN_EDGE', '0.03'),
        min_ev=decimal_env('MIN_EV', '0.01'),
        min_bookmakers=int_env('MIN_BOOKMAKERS', '4'),
    )


def implied_probability(odds: Decimal) -> Decimal:
    if odds <= 0:
        return Decimal('0')
    return Decimal('1') / odds


def expected_value(odds: Decimal, estimated_probability: Decimal) -> Decimal:
    return (estimated_probability * (odds - Decimal('1'))) - (Decimal('1') - estimated_probability)


def fetch_odds(settings: OddsApiSettings) -> tuple[list[dict[str, Any]], dict[str, str]]:
    if not settings.api_key:
        raise RuntimeError('THE_ODDS_API_KEY nao configurada no arquivo .env')

    url = f'{API_HOST}/v4/sports/{settings.sport}/odds/'
    params: dict[str, str] = {
        'apiKey': settings.api_key,
        'regions': settings.regions,
        'markets': settings.markets,
        'oddsFormat': settings.odds_format,
        'dateFormat': 'iso',
    }
    if settings.bookmakers:
        params['bookmakers'] = settings.bookmakers

    response = requests.get(url, params=params, timeout=30)
    headers = {
        'remaining': response.headers.get('x-requests-remaining', ''),
        'used': response.headers.get('x-requests-used', ''),
        'last': response.headers.get('x-requests-last', ''),
    }

    if response.status_code != 200:
        raise RuntimeError(f'Erro na API {response.status_code}: {response.text[:500]}')

    return response.json(), headers


def list_sports(api_key: str) -> list[dict[str, Any]]:
    response = requests.get(f'{API_HOST}/v4/sports/', params={'apiKey': api_key}, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(f'Erro ao listar esportes {response.status_code}: {response.text[:500]}')
    return response.json()


def confidence_label(bookmakers_count: int, edge: Decimal, ev: Decimal) -> str:
    if bookmakers_count < 3:
        return 'baixa'
    if bookmakers_count >= 6 and edge >= Decimal('0.05') and ev >= Decimal('0.03'):
        return 'alta'
    if bookmakers_count >= 4 and edge >= Decimal('0.03') and ev >= Decimal('0.01'):
        return 'media'
    return 'baixa'


def analyse_events(events: list[dict[str, Any]], settings: OddsApiSettings) -> list[dict[str, Any]]:
    opportunities: list[dict[str, Any]] = []

    for event in events:
        event_name = f"{event.get('home_team', '')} x {event.get('away_team', '')}".strip(' x')
        # outcome -> list of samples. Each sample has the bookmaker and that bookmaker's no-vig probability.
        probability_samples: dict[str, list[dict[str, Any]]] = defaultdict(list)
        offers: list[dict[str, Any]] = []

        for bookmaker in event.get('bookmakers', []):
            bookmaker_title = bookmaker.get('title', bookmaker.get('key', ''))
            bookmaker_key = bookmaker.get('key', bookmaker_title)
            last_update = bookmaker.get('last_update', '')

            for market in bookmaker.get('markets', []):
                market_key = market.get('key', '')
                outcomes = market.get('outcomes', [])
                parsed_outcomes: list[tuple[str, Decimal]] = []

                for outcome in outcomes:
                    try:
                        price = Decimal(str(outcome.get('price')))
                    except InvalidOperation:
                        continue
                    if price <= 1:
                        continue
                    parsed_outcomes.append((outcome.get('name', ''), price))

                raw_sum = sum((implied_probability(price) for _, price in parsed_outcomes), Decimal('0'))
                if raw_sum <= 0:
                    continue

                margin = raw_sum - Decimal('1')

                for outcome_name, price in parsed_outcomes:
                    raw_prob = implied_probability(price)
                    no_vig_prob = raw_prob / raw_sum
                    probability_samples[outcome_name].append({
                        'bookmaker_key': bookmaker_key,
                        'bookmaker_title': bookmaker_title,
                        'probability': no_vig_prob,
                        'margin': margin,
                    })
                    offers.append({
                        'event': event_name,
                        'commence_time': event.get('commence_time', ''),
                        'home_team': event.get('home_team', ''),
                        'away_team': event.get('away_team', ''),
                        'market': market_key,
                        'selection': outcome_name,
                        'bookmaker': bookmaker_title,
                        'bookmaker_key': bookmaker_key,
                        'bookmaker_last_update': last_update,
                        'odds': price,
                        'bookmaker_probability': raw_prob,
                        'bookmaker_market_margin': margin,
                    })

        for offer in offers:
            samples = probability_samples.get(offer['selection'], [])
            samples_excluding_current = [
                sample for sample in samples
                if sample['bookmaker_key'] != offer['bookmaker_key']
            ]
            used_samples = samples_excluding_current or samples
            if not used_samples:
                continue

            estimated_probability = sum(
                (sample['probability'] for sample in used_samples),
                Decimal('0'),
            ) / Decimal(len(used_samples))

            odds = offer['odds']
            edge = estimated_probability - offer['bookmaker_probability']
            ev = expected_value(odds, estimated_probability)
            bookmakers_count = len(used_samples)
            approved = (
                edge >= settings.min_edge
                and ev >= settings.min_ev
                and bookmakers_count >= settings.min_bookmakers
            )
            confidence = confidence_label(bookmakers_count, edge, ev)

            opportunities.append({
                **offer,
                'estimated_probability': estimated_probability,
                'edge': edge,
                'expected_value': ev,
                'approved': approved,
                'bookmakers_count': bookmakers_count,
                'confidence': confidence,
                'method': 'consenso_sem_a_casa_atual' if samples_excluding_current else 'consenso_com_a_casa_atual',
            })

    opportunities.sort(key=lambda item: (item['approved'], item['expected_value'], item['edge'], item['bookmakers_count']), reverse=True)
    return opportunities


def filter_opportunities(
    opportunities: list[dict[str, Any]],
    only_alerts: bool = False,
    min_edge: Decimal | None = None,
    min_ev: Decimal | None = None,
    min_bookmakers: int | None = None,
    min_odds: Decimal | None = None,
    max_odds: Decimal | None = None,
    bookmaker: str | None = None,
    selection_contains: str | None = None,
) -> list[dict[str, Any]]:
    filtered = opportunities
    if only_alerts:
        filtered = [item for item in filtered if item['approved']]
    if min_edge is not None:
        filtered = [item for item in filtered if item['edge'] >= min_edge]
    if min_ev is not None:
        filtered = [item for item in filtered if item['expected_value'] >= min_ev]
    if min_bookmakers is not None:
        filtered = [item for item in filtered if item['bookmakers_count'] >= min_bookmakers]
    if min_odds is not None:
        filtered = [item for item in filtered if item['odds'] >= min_odds]
    if max_odds is not None:
        filtered = [item for item in filtered if item['odds'] <= max_odds]
    if bookmaker:
        needle = bookmaker.lower().strip()
        filtered = [item for item in filtered if needle in item['bookmaker'].lower()]
    if selection_contains:
        needle = selection_contains.lower().strip()
        filtered = [item for item in filtered if needle in item['selection'].lower() or needle in item['event'].lower()]
    return filtered


def get_live_analysis(settings: OddsApiSettings) -> tuple[list[dict[str, Any]], dict[str, str]]:
    events, headers = fetch_odds(settings)
    return analyse_events(events, settings), headers
