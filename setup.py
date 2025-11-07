#!/usr/bin/env python

__author__ = "K.Kobayashi, Kengo NAKADA"
__maintainer__ = "Kengo NAKADA"
__credits__ = ["Kengo NAKADA"]
__email__ = "kengo.nakada@gmail.com"
# __email__ = "kengo.nakada@spring8.or.jp"
# __copyright__ = "Copyright 2014-2018 Kengo NAKADA"
__license__ = "Apache2"
__status__ = "alpha"

from setuptools import setup, find_packages
import glob
import re
import os
import shutil


# --- クリーン処理 ---
for path in ["build", "dist"]:
    if os.path.exists(path):
        shutil.rmtree(path)

for name in os.listdir("."):
    if name.endswith(".egg-info"):
        shutil.rmtree(name)


# version = __version__
# from StructureAnalysisEnvironment import __version__
def read_version_from_toml() -> str:
    with open("pyproject.toml", encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("version"):
                m = re.search(r'version\s*=\s*["\']([^"\']+)["\']', line)
                if m:
                    return m.group(1)
    raise RuntimeError("version not found in pyproject.toml")


__version__ = read_version_from_toml()
__long_description__ = "RMC_DFT"
__description__ = "RMC_DFT"

# パッケージ指定
# packages = find_packages(exclude=["StructureAnalysisEnvironment.bin"])
__packages__ = find_packages()

setup(
    name="RMC_DFT",
    # packages=find_packages(),
    packages=__packages__,
    #       package_dir  = {'':'StructureAnalysisEnvironment'},
    #       include_package_data=True,
    #       package_data = { '': ['LICENSE.txt', 'README.md']},
    # package_data=package_data,
    # data_files=[(package_src_dir, files)],
    # scripts=__script__,
    version=__version__,
    description=__description__,
    long_description=__long_description__,
    author=__author__,
    #       author_email = ['kengo.nakada@gmail.com','kengo.nakada@spring8.or.jp'],
    #       author_email = 'kengo.nakada@gmail.com',
    # author_email='kengo.nakada@spring8.or.jp',
    author_email=__email__,
    license=__license__,
    install_requires=[
        "dataclasses",
        "coloredlogs",
        "colorlog",
        "pytest",
        "pytest-asyncio",
        "pyyaml",
        "toml",
        "grpcio",
        "nest_asyncio",
        "sphinx",
        "myst-parser",
        "sphinx-autobuild",
        "sphinx-rtd-theme",
        "sphinxcontrib-napoleon",
        "linkify-it-py",
    ],
    #       platforms = ['linux','OSX','Window'],
    #       classifiers = [
    #           'Programming Language :: Python :: 2.7',
    #           'Intended Audience :: Science/Research',
    #           'License :: OSI Approved :: MIT License'
    #           ]
)
