import pathlib

from setuptools import find_packages, setup

long_description = "\n\n".join([open("README.rst").read(), open("CHANGES.rst").read()])


def get_version():
    # Edited from https://packaging.python.org/guides/single-sourcing-package-version/
    init_path = pathlib.Path(__file__).parent / "threedi_schema/__init__.py"
    for line in init_path.open("r").readlines():
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


install_requires = [
    "GeoAlchemy2>=0.9,!=0.11.*",
    "SQLAlchemy>=1.4",
    "alembic>=1.8,<2",
]

tests_require = ["pytest", "pytest-cov"]
cli_require = ["click"]


setup(
    name="threedi-schema",
    version=get_version(),
    description="The schema of 3Di schematization files",
    long_description=long_description,
    # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
    classifiers=["Programming Language :: Python", "Framework :: Django"],
    keywords=[],
    author="Nelen & Schuurmans",
    author_email="info@nelen-schuurmans.nl",
    url="https://github.com/nens/threedi-schema",
    license="MIT",
    packages=find_packages(include="threedi_schema*"),
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    python_requires=">=3.7",
    tests_require=tests_require,
    extras_require={"test": tests_require, "cli": cli_require},
    entry_points={
        "console_scripts": [
            "threedi_schema = threedi_schema.scripts:main"
        ]
    },
)
