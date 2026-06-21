import os
import sys
import os
import sys
sys.path.insert(0, os.path.abspath('../../src'))
sys.path.insert(0, os.path.abspath('../../src/module_2'))

project   = 'Grad Cafe Analytics'
copyright = '2025, Stefan Thomas'
author    = 'Stefan Thomas'
release   = '4.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

templates_path   = ['_templates']
exclude_patterns = ['_build']
html_theme       = 'sphinx_rtd_theme'
html_static_path = ['_static']