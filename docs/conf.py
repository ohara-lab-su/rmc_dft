"""RMC_DFT 共通 Sphinx 設定。言語別ソースは docs/en, docs/ja。"""
from pathlib import Path
import sys

DOCS_DIR = Path(__file__).resolve().parent
ROOT_DIR = DOCS_DIR.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

project = "rmc_dft"
root_doc = "index"
source_suffix = {".md": "markdown", ".rst": "restructuredtext"}
extensions = [
    "myst_parser", "sphinx.ext.autodoc", "sphinx.ext.autosummary",
    "sphinx.ext.napoleon", "sphinx.ext.viewcode",
]
autosummary_generate = True
myst_enable_extensions = ["colon_fence", "dollarmath", "amsmath"]
html_theme = "sphinx_rtd_theme"
html_theme_options = {"collapse_navigation": False, "navigation_depth": 4}
exclude_patterns = ["_build", "**/.DS_Store"]
