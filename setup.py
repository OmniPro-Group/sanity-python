import codecs
import os
import re

from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))


def read(file_paths, default=""):
    # intentionally *not* adding an encoding option to open
    try:
        with codecs.open(os.path.join(here, *file_paths), "r") as fh:
            return fh.read()
    except Exception:
        return default


def find_version(file_paths):
    version_file = read(file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


with open("README.md") as fp:
    long_description = fp.read()

setup(
    name="sanity",
    version=find_version(["sanity", "__init__.py"]),
    description="Python Client wrapper for Sanity.io HTTP API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="OmniPro",
    author_email="",
    url="https://github.com/OmniPro-Group/sanity-python",
    download_url="https://github.com/OmniPro-Group/sanity-python",
    keywords=["sanity", "sanity-http-api"],
    packages=find_packages(),
    install_requires=["requests"],
    license_files=('LICENSE',),
    classifiers=[
        "Development Status :: 4 - Alpha",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python",
    ],
)
