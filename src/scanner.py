from decimal import Decimal


def implied_probability(odds: Decimal) -> Decimal:
    if odds <= 0:
        raise ValueError('odds must be greater than zero')
    return Decimal('1') / odds


def expected_value(odds: Decimal, estimated_probability: Decimal) -> Decimal:
    profit_if_right = odds - Decimal('1')
    probability_wrong = Decimal('1') - estimated_probability
    return (estimated_probability * profit_if_right) - probability_wrong


def analyze_row(row: dict, min_edge: Decimal, min_ev: Decimal) -> dict:
    odds = Decimal(str(row['odds']))
    estimated_probability = Decimal(str(row['estimated_probability']))
    implied = implied_probability(odds)
    edge = estimated_probability - implied
    ev = expected_value(odds, estimated_probability)
    approved = edge >= min_edge and ev >= min_ev

    return {
        **row,
        'implied_probability': implied,
        'edge': edge,
        'expected_value': ev,
        'approved': approved,
    }
