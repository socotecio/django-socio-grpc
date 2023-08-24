project = "Django Socio gRPC"
copyright = "2023, Socotec.io"

extensions = [
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.autodoc",
    "sphinxcontrib.apidoc",
    "sphinxcontrib.spelling",
    # "sphinx.ext.napoleon",
    "auto_pytabs.sphinx_ext",
    "sphinx_autodoc_typehints",
    "sphinx_rtd_theme",
    "myst_parser",
]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "django": ("https://docs.djangoproject.com/en/4.2/", None),
    "grpc": ("https://grpc.github.io/grpc/python/", None),
    "rest_framework": ("https://www.django-rest-framework.org/", None),
}

apidoc_module_dir = "../django_socio_grpc"
apidoc_excluded_paths = ["*/tests/*"]


napoleon_google_docstring = True
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_attr_annotations = True

autoclass_content = "class"
autodoc_class_signature = "separated"
autodoc_default_options = {
    "special-members": "__init__",
    "show-inheritance": True,
    "members": True,
}
autodoc_member_order = "bysource"
autodoc_typehints_format = "short"


auto_pytabs_min_version = (3, 8)
auto_pytabs_max_version = (3, 11)
auto_pytabs_compat_mode = True

autosectionlabel_prefix_document = True

# suppress_warnings = [
#     "autosectionlabel.*",
#     "ref.python",  # TODO: remove when https://github.com/sphinx-doc/sphinx/issues/4961 is fixed
# ]

html_theme = "sphinx_rtd_theme"
html_show_sourcelink = True
html_static_path = ["_static"]
html_title = "Django Socio gRPC"


html_theme_options = {
    "display_version": True,
}
