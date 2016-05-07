.. _badges:

.. image:: https://travis-ci.org/avanov/solo.svg?branch=develop
    :target: https://travis-ci.org/avanov/solo

.. image:: https://coveralls.io/repos/github/avanov/solo/badge.svg?branch=develop
    :target: https://coveralls.io/github/avanov/solo?branch=develop

.. image:: https://requires.io/github/avanov/solo/requirements.svg?branch=develop
    :target: https://requires.io/github/avanov/solo/requirements/?branch=develop
    :alt: Requirements Status

.. image:: https://readthedocs.org/projects/solo/badge/?version=develop
    :target: http://solo.readthedocs.org/en/develop/
    :alt: Documentation Status

.. image:: http://img.shields.io/pypi/v/solo.svg
    :target: https://pypi.python.org/pypi/solo
    :alt: Latest PyPI Release

.. image:: http://img.shields.io/pypi/dm/solo.svg
    :target: https://pypi.python.org/pypi/solo
    :alt: Monthly PyPI downloads


**Development status: Early Alpha**


Host prerequisites
------------------

* Vagrant >= 1.8
* Python 2.7.x (required for Ansible CLI);
* Ansible >= 2.0

Bootstrapping development environment
-------------------------------------

Run

.. code::

   $ git clone https://github.com/avanov/solo.git <local_project_root>
   $ cd <local_project_root>
   $ vagrant up


Running a development server
----------------------------

After a new VM is provisioned, run

.. code::

   $ vagrant ssh
   vagrant@vagrant-ubuntu-*:~$ cd /vagrant
   vagrant@vagrant-ubuntu-*:/vagrant$ pyenv activate solo
   (solo) vagrant@vagrant-ubuntu-*:/vagrant$ solo run ./config.yml


You can terminate the server by sending it a SIGINT (Ctrl-C from an interactive session).


Test framework
--------------

Run existing test suite with

.. code::

   (solo) vagrant@vagrant-ubuntu-*:/vagrant$ py.test
