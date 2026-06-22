API Reference
=============

Note on Scraping Modules
------------------------
The scraping and cleaning modules live in ``module_2/webScraper/`` and
are invoked by the Flask app via subprocess when ``POST /pull-data``
is triggered.

Flask App (app.py)
------------------
.. automodule:: app
   :members:
   :undoc-members:

ETL — Load Data (load_data.py)
-------------------------------
.. automodule:: load_data
   :members:
   :undoc-members:

Queries (query_data.py)
------------------------
.. automodule:: query_data
   :members:
   :undoc-members:

Configuration (configuration.py)
----------------------------------
.. automodule:: configuration
   :members:
   :undoc-members:

Scraper (scrapeData.py)
------------------------
.. automodule:: webScraper.scrapeData
   :members:
   :undoc-members:

Data Cleaning (cleanData.py)
-----------------------------
.. automodule:: webScraper.cleanData
   :members:
   :undoc-members: