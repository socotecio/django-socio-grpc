import os
import sys

sys.path.insert(0, os.path.abspath(".."))
from django.conf import settings  # noqa

settings.configure()

project = "Django Socio gRPC"
copyright = "2023, Socotec.io"

extensions = [
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosectionlabel",
    "autodoc2",
    "sphinxcontrib.apidoc",
    "sphinxcontrib.spelling",
    "auto_pytabs.sphinx_ext",
    "sphinx_autodoc_typehints",
    "sphinx_rtd_theme",
    "myst_parser",
]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "django": ("https://docs.djangoproject.com/en/5.0/", None),
    "grpc": ("https://grpc.github.io/grpc/python/", None),
    "rest_framework": ("https://www.django-rest-framework.org/", None),
}

napoleon_google_docstring = True
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_attr_annotations = True

auto_pytabs_min_version = (3, 8)
auto_pytabs_max_version = (3, 11)
auto_pytabs_compat_mode = True

autosectionlabel_prefix_document = True

# suppress_warnings = [
#     "autosectionlabel.*",
# ]

html_theme = "sphinx_rtd_theme"
html_show_sourcelink = True
html_static_path = ["_static"]
html_title = "Django Socio gRPC"


html_theme_options = {
    "display_version": True,
}

autodoc2_render_plugin = "myst"
autodoc2_packages = [
    {"path": "../django_socio_grpc", "exclude_dirs": ["tests"]},
]
