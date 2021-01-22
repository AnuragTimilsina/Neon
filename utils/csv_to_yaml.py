#! /usr/bin/env python3

"""Converts django-oscar csv fixture files to yaml

Contains functions to convert django-oscar csv fixture files to yaml.
Additionally, contains a small CLI tool to do this from the command line.
"""

import csv
import argparse
import yaml
import argparse
import sys
from typing import Optional


def parse_product(row: str) -> dict:
    """Parse the row from the fixture csv and convert to a python dictionary.

    No error checking is performed and all values are expected to be present
    in the row.

    Args:
        row: The csv row string.
    
    Returns:
        A python dict that represents the product.
    """
    csv_headers = ("product_class", "category", "upc", "title", "description",
                   "partner_name", "partner_sku", "price", "num_in_stock")
    _ = dict(zip(csv_headers, row))

    return {
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


def parse_csv(path: str) -> Optional[dict]:
    """Parse the fixture csv file and convert to a dictionary
    
    Writes to stderr if file is not present.

    Args:
        path (str): The path to the csv file.
    
    Returns:
        A dict representing the csv if file exists, None otherwise.
    """
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
