.. Formify documentation master file, created by
   sphinx-quickstart on Fri Feb 14 22:06:12 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Formify -- validation library for Python
========================================

Introduction
------------

Formify is a validation library for Python written using `TDD
<http://en.wikipedia.org/wiki/Test-driven_development>`_ approach and inspired
by other similar toolkits, especially WTForms. The main goal of this library is
to be completely independent from other frameworks, so same validation model
could be used in both web and desktop applications.

Features:

* Easy data schema definition using class attributes and validators
* Schema objects act like standard Python dictionaries
* Almost all validators can be used in a standalone way (without any data
  schema), so it is easy to use just one validator without creating schema for
  it
* Separation of input data processing into two distinct steps: conversion to
  proper type and validation of value known to be of concrete type

Installing
----------

The simplest way of get things work is following:

1. Download Formify
2. Create ``3rdparty`` directory somewhere in your project
3. Create a symlink or copy ``/formify`` directory (the one with source code) to
   directory created in previous step.
4. Tell your Python interpreter to search modules in previously created
   ``3rdparty`` directory (by adding path to ``sys.path`` somewhere in your
   bootstrap file).
5. Try to import ``formify`` module.

I know this is a bit messy but will certainly work ;-) I will create
``setup.py`` script in the future.

License
-------

Formify is distributed under the `MIT license
<http://opensource.org/licenses/mit-license.php>`_.

API reference
-------------

formify.decorators
^^^^^^^^^^^^^^^^^^

.. automodule:: formify.decorators
    :members:

formify.exc
^^^^^^^^^^^

.. automodule:: formify.exc
    :members:
    :show-inheritance:

formify.schema
^^^^^^^^^^^^^^

.. automodule:: formify.schema
    :members:
    :special-members:
    :show-inheritance:

formify.validators
^^^^^^^^^^^^^^^^^^^^^^^

formify.validators.base
"""""""""""""""""""""""

.. automodule:: formify.validators.base
    :members:
    :special-members:
    :show-inheritance:

formify.validators.general
""""""""""""""""""""""""""

.. automodule:: formify.validators.general
    :members:
    :special-members:
    :show-inheritance:

formify.validators.iso
""""""""""""""""""""""

.. automodule:: formify.validators.iso
    :members:
    :special-members:
    :show-inheritance:

formify.validators.mixins
"""""""""""""""""""""""""

.. automodule:: formify.validators.mixins
    :members:
    :special-members:
    :show-inheritance:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
