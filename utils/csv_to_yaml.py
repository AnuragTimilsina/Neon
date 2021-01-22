#! /usr/bin/env python3
import csv
import argparse
import yaml
import argparse
import sys


def parse_product(row):
    csv_headers = ("product_class", "category", "upc", "title", "description",
                   "partner_name", "partner_sku", "price", "num_in_stock")
    _ = dict(zip(csv_headers, row))

    tests = {
        "product": {
            "upc": _["upc"],
            "title": _["title"],
            "description": _["description"],
            "product_class": {
                "name": _["product_class"],
            },
            "categories": [
                {"name": _["category"]},
            ],
        },
        "partner": {
            "name": _["partner_name"],
        },
        "partner_sku": _["partner_sku"],
        "price": _["price"],
        "num_in_stock": int(_["num_in_stock"]),

    }
    return tests


def parse_csv(path):
    document = {}
    document["stock"] = []
    try:
        with open(path, 'rt') as f:
            for row in csv.reader(f, escapechar='\\'):
                document["stock"].append(parse_product(row))
        return document
    except Exception as e:
        sys.stderr.write(f"err: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Converts csv fixture files from django oscar to yaml.")

    parser.add_argument(
        "path", help="Path to the csv files to convert to yaml.")

    parsed_args = parser.parse_args()
    document = parse_csv(parsed_args.path)
    if document:
        print(yaml.dump(document, sort_keys=False))
    else:
        sys.exit(-1)


if __name__ == '__main__':
    main()
