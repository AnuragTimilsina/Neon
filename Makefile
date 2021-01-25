# Produces a fresh build of the site.
all: depends clean fixtures database

# Checks if we are inside a python virtual environment
check_for_venv:
	test -n "$(VIRTUAL_ENV)" # Please make sure you are inside a virtual environment.

# Builds the fixture.yaml file
fixtures: depends
	python utils/download_fixtures.py fixtures/fixtures.yaml

# Builds the database
database: depends
	python manage.py migrate
	python manage.py oscar_populate_countries --initial-only
	python manage.py load_catalogue fixtures/fixtures.yaml --clear

# Installs all dependencies
depends: check_for_venv
	pip install -r requirements.txt

# Cleans database, images, static_files and compiled python code.
clean:
	rm -f db.sqlite
	rm -rf images/*
	rm -rf media/*
	rm -rf static/*
	find . -type f -name "*.pyc" -delete

# fix and lint all code
lint: depends
	isort . --skip migrations
	autopep8 --exclude migrations --recursive --in-place .
	pylint --rcfile=.pylintrc shop/ catalogue/
