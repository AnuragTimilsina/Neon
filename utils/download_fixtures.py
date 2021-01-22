#! /usr/bin/env python3
import sys
import os
import shutil
import yaml
import tempfile
import argparse
import urllib.request
import csv_to_yaml


def download_file(url, path):
    with urllib.request.urlopen(url) as response, open(path, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)


def generate_dict(fixture_urls):
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
