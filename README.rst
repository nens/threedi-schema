threedi-schema
==========================================


.. image:: https://img.shields.io/pypi/v/threedi-schema.svg
  :target: https://pypi.org/project/threedi-schema/

.. image:: https://github.com/nens/threedi-schema/actions/workflows/test.yml/badge.svg
	:alt: Github Actions status
	:target: https://github.com/nens/threedi-schema/actions/workflows/test.yml


The schema of 3Di schematization files

This package exposes the following:

- A ``ThreediDatabase`` object to interact with the schematization files.
- Methods for upgrading schema versions.
- The 3Di schema as SQLAlchemy models and python Enum classes.

Example
-------

The following code sample shows how you can upgrade a schematization file::

    from threedi_schema import ThreediDatabase

    db = ThreediDatabase("<Path to your sqlite file>")
    db.schema.upgrade()


The following code sample shows how you can list Channel objects::

    from threedi_schema import models

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
