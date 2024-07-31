# WEAVE Docs

## Installation and contribution

To install mkdocs do the following:

``` bash
virtualenv -p python3 ~/.virtualenvs/mkdocs
source ~/.virtualenvs/mkdocs/bin/activate
pip install --upgrade pip
pip install mkdocs-material
```

After installation, you should see `(mkdocs)` in your command line. If you close your terminal and return later, re-run the first two commands before previewing locally:

``` bash
virtualenv -p python3 ~/.virtualenvs/mkdocs
source ~/.virtualenvs/mkdocs/bin/activate
```

## Starting the server

At the top of the repo do:

``` bash
mkdocs serve 
```

You may need to specify a port (4000 or 8000):

```bash
mkdocs serve --dev-addr 127.0.0.1:4000
```

If it complains about ASCII:

``` bash
export LC_ALL=en_US.utf-8 && export LANG=en_US.utf-8
```
