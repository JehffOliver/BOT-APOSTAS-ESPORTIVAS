from decimal import Decimal
import csv

from src.scanner import analyze_row


def main() -> None:
    with open('data/sample_odds.csv', newline='', encoding='utf-8') as file:
        rows = list(csv.DictReader(file))

    for row in rows:
        result = analyze_row(row, Decimal('0.03'), Decimal('0.01'))
        print(result)


if __name__ == '__main__':
    main()
