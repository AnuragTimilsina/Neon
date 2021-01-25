# <p style="text-align:center"> Neon </p>

*<p style="text-align:center"> An e-commerce platform for wholesalers and retailers. </p>*

## Installation

We use a Makefile to generate a fresh install of the project.

Please **make sure you are in a virtual environment** before running `make all`.  The installation will fail otherwise, since we never pollute system packages.

Useful commands include:

- `make all` : Build a fresh project.
- `make clean` : Removes the database, all images and compiled files.
- `make depends` : Install all dependencies
- `make database` : Build a fresh database.
- `make fixtures` : Create all fixtures.
- `make lint` : Fix and lints all source code.
