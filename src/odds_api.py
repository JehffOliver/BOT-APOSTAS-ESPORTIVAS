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


def decimal_env(name: str, default: str) -> Decimal:
    value = os.getenv(name, default).strip().replace(',', '.')
    try:
        return Decimal(value)
    except InvalidOperation:
        return Decimal(default)


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


def analyse_events(events: list[dict[str, Any]], settings: OddsApiSettings) -> list[dict[str, Any]]:
    opportunities: list[dict[str, Any]] = []

    for event in events:
        event_name = f"{event.get('home_team', '')} x {event.get('away_team', '')}".strip(' x')
        outcome_probability_samples: dict[str, list[Decimal]] = defaultdict(list)
        offers: list[dict[str, Any]] = []

        for bookmaker in event.get('bookmakers', []):
            bookmaker_title = bookmaker.get('title', bookmaker.get('key', ''))
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

                for outcome_name, price in parsed_outcomes:
                    raw_prob = implied_probability(price)
                    no_vig_prob = raw_prob / raw_sum
                    outcome_probability_samples[outcome_name].append(no_vig_prob)
                    offers.append({
                        'event': event_name,
                        'commence_time': event.get('commence_time', ''),
                        'home_team': event.get('home_team', ''),
                        'away_team': event.get('away_team', ''),
                        'market': market_key,
                        'selection': outcome_name,
                        'bookmaker': bookmaker_title,
                        'odds': price,
                        'bookmaker_probability': raw_prob,
                    })

        consensus_probabilities: dict[str, Decimal] = {}
        for outcome_name, samples in outcome_probability_samples.items():
            if not samples:
                continue
            consensus_probabilities[outcome_name] = sum(samples, Decimal('0')) / Decimal(len(samples))

        for offer in offers:
            estimated_probability = consensus_probabilities.get(offer['selection'])
            if estimated_probability is None:
                continue
            odds = offer['odds']
            edge = estimated_probability - offer['bookmaker_probability']
            ev = expected_value(odds, estimated_probability)
            approved = edge >= settings.min_edge and ev >= settings.min_ev
            opportunities.append({
                **offer,
                'estimated_probability': estimated_probability,
                'edge': edge,
                'expected_value': ev,
                'approved': approved,
                'bookmakers_count': len(outcome_probability_samples.get(offer['selection'], [])),
            })

    opportunities.sort(key=lambda item: (item['approved'], item['expected_value'], item['edge']), reverse=True)
    return opportunities


def get_live_analysis(settings: OddsApiSettings) -> tuple[list[dict[str, Any]], dict[str, str]]:
    events, headers = fetch_odds(settings)
    return analyse_events(events, settings), headers
