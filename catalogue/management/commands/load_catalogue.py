from PIL import Image
import logging
import urllib.request
import shutil
import yaml
import os
import sys
import decimal

from django.core.management.base import BaseCommand
from django.db.transaction import atomic
from django.core.files import File
from django.core.exceptions import FieldError

from oscar.core.loading import get_class, get_model
from oscar.apps.catalogue.exceptions import (
    IdenticalImageError, ImageImportError)


def clear_catalogue():
    Category = get_model('catalogue', 'Category')
    Partner = get_model('partner', 'Partner')
    Product = get_model('catalogue', 'Product')
    ProductCategory = get_model('catalogue', 'ProductCategory')
    ProductClass = get_model('catalogue', 'ProductClass')
    StockRecord = get_model('partner', 'StockRecord')
    ProductImage = get_model('catalogue', 'productimage')

    Category.objects.all().delete()
    Partner.objects.all().delete()
    Product.objects.all().delete()
    ProductCategory.objects.all().delete()
    ProductClass.objects.all().delete()
    StockRecord.objects.all().delete()
    ProductImage.objects.all().delete()


def load_product_class(item):
    ProductClass = get_model('catalogue', 'ProductClass')
    product_class, __ = ProductClass.objects.get_or_create(
        name=item["name"])
    return product_class


def load_partner(item):
    Partner = get_model('partner', 'Partner')

    partner, _ = Partner.objects.get_or_create(
        name=item["name"])
    return partner


def load_category(item):
    create_category_from_breadcrumbs = get_class(
        'catalogue.categories', 'create_from_breadcrumbs')
    category = create_category_from_breadcrumbs(item["name"])
    return category


def load_product(item):
    Product = get_model('catalogue', 'Product')
    ProductCategory = get_model('catalogue', 'ProductCategory')

    try:
        product = Product.objects.get(upc=item["upc"])
    except Product.DoesNotExist:
        product = Product()

    product.upc = item["upc"]
    product.title = item["title"]
    product.description = item["description"]
    product.product_class = load_product_class(item["product_class"])
    product.save()

    for category_dict in item["categories"]:
        category = load_category(category_dict)
        ProductCategory.objects.update_or_create(
            product=product, category=category)

    return product


def load_stock_record(item):
    StockRecord = get_model('partner', 'StockRecord')

    try:
        stock = StockRecord.objects.get(partner_sku=item["partner_sku"])
    except StockRecord.DoesNotExist:
        stock = StockRecord()

    stock.partner_sku = item["partner_sku"]
    stock.product = load_product(item["product"])
    stock.partner = load_partner(item["partner"])
    stock.price = decimal.Decimal(item["price"])
    stock.num_in_stock = item["num_in_stock"]

    stock.save()


def load_fixture(fixture):
    for product_class in fixture["product_classes"]:
        load_product_class(product_class)

    for partner in fixture["partners"]:
        load_partner(partner)

    for category in fixture["categories"]:
        load_category(category)

    for stock_record in fixture["stock"]:
        load_stock_record(stock_record)


class ImageImporter(object):

    allowed_extensions = ['.jpeg', '.jpg', '.gif', '.png']

    def __init__(self, logger, field):
        self.logger = logger
        self._field = field

    @atomic
    def handle(self, dirname):
        Product = get_model('catalogue', 'product')
        filenames = self._get_image_files(dirname)

        for filename in filenames:
            try:
                lookup_value \
                    = self._get_lookup_value_from_filename(filename)
                self._process_image(dirname, filename)
            except Product.MultipleObjectsReturned:
                self.logger.warning(
                    f"Multiple products matching {self._field}='{lookup_value}', skipping")
            except Product.DoesNotExist:
                self.logger.warning(
                    f"No item matching {self._field}='{lookup_value}'")
            except IdenticalImageError:
                self.logger.warning(
                    f"Identical image already exists for {self._field}='{lookup_value}, skipping")
            except IOError as e:
                raise ImageImportError(f'{filename} is not a valid image {e}')
            except FieldError as e:
                raise ImageImportError(e)

    def _get_image_files(self, image_dir):
        filenames = []
        for filename in os.listdir(image_dir):
            _, ext = os.path.splitext(filename)
            if os.path.isfile(os.path.join(image_dir, filename)) \
                    and ext in self.allowed_extensions:
                filenames.append(filename)
        return filenames

    def _process_image(self, dirname, filename):
        ProductImage = get_model('catalogue', 'productimage')

        file_path = os.path.join(dirname, filename)
        trial_image = Image.open(file_path)
        trial_image.verify()

        item = self._fetch_item(filename)

        new_data = open(file_path, 'rb').read()
        next_index = 0
        for existing in item.images.all():
            next_index = existing.display_order + 1
            try:
                if new_data == existing.original.read():
                    raise IdenticalImageError()
            except IOError:
                # File probably doesn't exist
                existing.delete()

        new_file = File(open(file_path, 'rb'))
        im = ProductImage(product=item, display_order=next_index)
        im.original.save(filename, new_file, save=False)
        im.save()

    def _fetch_item(self, filename):
        Product = get_model('catalogue', 'product')
        kwargs = {self._field: self._get_lookup_value_from_filename(filename)}
        return Product._default_manager.get(**kwargs)

    def _get_lookup_value_from_filename(self, filename):
        return os.path.splitext(filename)[0]


def import_catalogue(logger, fixture_file_path, field, clear):
    # Clear catalogue if instructed
    if clear:
        clear_catalogue()
        logger.info("Clearing catalogue")

    # Populate all products.
    with open(fixture_file_path, 'r') as stream:
        try:
            logger.info("Loading fixtures")
            load_fixture(yaml.safe_load(stream))
        except yaml.YAMLError as e:
            print(f"Could not parse yaml: {e}")

    # Download, extract and populate product images
    import tempfile
    _, archive_file = tempfile.mkstemp(suffix=".tar.gz")
    images_dir = tempfile.mkdtemp()
    url = "https://github.com/django-oscar/django-oscar/raw/master/sandbox/fixtures/images.tar.gz"

    logger.info("Downloading image archive")
    with urllib.request.urlopen(url) as response, open(archive_file, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)
    shutil.unpack_archive(archive_file, images_dir)

    logger.info("Importing images")
    ImageImporter(logger, field).handle(images_dir)

    # Remove temporary files
    os.remove(archive_file)
    shutil.rmtree(images_dir)

    logger.info("Catalogue import complete")


handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)

logger = logging.getLogger('shop.load_catalogue')
logger.setLevel(logging.INFO)
logger.addHandler(handler)


class Command(BaseCommand):
    help = 'For importing catalogue from fixtures and image archive.'

    def add_arguments(self, parser):
        parser.add_argument('path', help='/path/to/fixture.yaml')

        parser.add_argument(
            '--img-field',
            dest='image_field',
            default='upc',
            help='Product field to lookup from image filename')

        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear all existing entries in the catalogue before import"
        )

    def handle(self, *args, **options):
        import_catalogue(logger, options["path"], options.get(
            "image_field"), options["clear"])
