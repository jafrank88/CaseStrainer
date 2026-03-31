Development Guide
=================

Setting up Development Environment
----------------------------------

1. Clone the repository::

      git clone https://github.com/uwlaw/casestrainer.git
      cd casestrainer

2. Create virtual environment::

      python -m venv venv
      source venv/bin/activate  # Windows: venv\Scripts\activate

3. Install dependencies::

      pip install -r requirements.txt
      pip install -r requirements-dev.txt

4. Install pre-commit hooks::

      pre-commit install

Running Tests
-------------

Run all tests::

   pytest

Run tests for specific package::

   pytest tests/clustering/
   pytest tests/extraction/
   pytest tests/verification/

Run with coverage::

   pytest --cov=src tests/

Code Quality
------------

The project uses several tools for code quality:

* **Black**: Code formatting
* **isort**: Import sorting
* **flake8**: Linting
* **mypy**: Type checking
* **bandit**: Security scanning

These are run automatically via pre-commit hooks.

Building Documentation
------------------------

Build Sphinx documentation::

   cd docs
   make html

View documentation::

   open _build/html/index.html

Adding New Modules
------------------

When adding new functionality:

1. Create module in appropriate package (clustering/extraction/verification)
2. Add type hints
3. Write docstrings (Google style)
4. Add unit tests
5. Update package __init__.py exports
6. Update documentation

Commit Messages
---------------

Follow conventional commits::

   feat: add new verification source
   fix: correct year validation logic
   docs: update API documentation
   test: add unit tests for clustering
   refactor: modularize verification

API Documentation
-----------------

See the API reference sections for detailed documentation of each module.
