threedi-schema
==========================================


.. image:: https://img.shields.io/pypi/v/threedi-schema.svg
  :target: https://pypi.org/project/threedi-schema/

.. image:: https://github.com/nens/threedi-schema/actions/workflows/test.yml/badge.svg
	:alt: Github Actions status
	:target: https://github.com/nens/threedi-schema/actions/workflows/test.yml


The schema of 3Di schematisation files.

This project exposes:

- A ``ThreediDatabase`` object to interact with schematisation files.
- A ``ModelSchema`` object (``ThreediDatabase().schema``) for adapting
  schema versions (called "migration").
- The 3Di schema as SQLAlchemy models and python Enum classes.\*

\*This package exposes SQLAlchemy models of the
schematisation files directly. A minor release of this package may
change these models and will be backwards incompatible.
If the SQLAlchemy models are used, we strongly advise to fix the
minor version as follows: ``threedi-schema==0.214.*``. Otherwise, just
fixing the major version is sufficient.

Example
-------

The following code sample shows how you can upgrade a schematisation file::

    from threedi_schema import ThreediDatabase

    db = ThreediDatabase("<Path to your sqlite file>")
    db.schema.upgrade()


The following code sample shows how you can list Channel objects::

    from threedi_schema import models
    # NB: Ensure that you pin the minor version of threedi-schema
    # when using models (or constants).

    channels = db.get_session().query(models.Channel).all()


Command-line interface
----------------------

Migrate to the latest schema version::

    threedi_schema -s path/to/model.sqlite migrate 


Ensure presence of spatial indexes::

    threedi_schema -s path/to/model.sqlite index 


Installation
------------

Install with::

  $ pip install threedi-schema
