#! /usr/bin/env python3

"""Downloads and converts fixtures to yaml present in django-oscar

Contains functions to download and convert fixtures present in django-oscar.
The csv fixtures are converted to yaml. Additionally contains a CLI tool do the same.
"""
import argparse
import os
import shutil
import sys
import tempfile
import urllib.request

import csv_to_yaml
import yaml


def download_file(url: str, path: str) -> None:
    """Download file from url

    Downloads the file from url to path. No exception handling is done.

    Args:
        url (str): The url of the source file.
        path (str): The path of the destination file.

    Returns:
        None
    """
    with urllib.request.urlopen(url) as response, open(path, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)


def generate_dict(fixture_urls: list[str]) -> dict:
    """Generate a stock dict from the list of fixture urls.

    Generates a dict containing all stock_records from the fixtures present at fixture_urls.

    Args:
        fixture_urls (list[str]): The list of urls of django-oscar fixtures.

    Returns:
        A python dictionary containing all stock records from the fixtures.
    """
    document = {}
    document["stock"] = []
    for url in fixture_urls:
        _, path = tempfile.mkstemp(suffix=".csv")
        download_file(url, path)
        document["stock"].extend(csv_to_yaml.parse_csv(path)["stock"])
        os.remove(path)

    document["product_classes"] = []
    document["categories"] = []
    document["partners"] = []
    return document


def main():
    parser = argparse.ArgumentParser(
        description="Downloads and converts fixtures from django oscar to yaml")

    parser.add_argument(
        "path", help="Path to the store the yaml fixture file.")

    parsed_args = parser.parse_args()

    fixture_urls = [
        "https://raw.githubusercontent.com/django-oscar/django-oscar/master/sandbox/fixtures/books.computers-in-fiction.csv",
        "https://raw.githubusercontent.com/django-oscar/django-oscar/master/sandbox/fixtures/books.essential.csv",
        "https://raw.githubusercontent.com/django-oscar/django-oscar/master/sandbox/fixtures/books.hacking.csv",
    ]

    document = generate_dict(fixture_urls)
    out_path = parsed_args.path
    if os.path.dirname(out_path):
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with open(out_path, "w") as f:
        f.write(yaml.dump(document, sort_keys=False))


if __name__ == '__main__':
    main()
