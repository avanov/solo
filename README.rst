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
   (solo) vagrant@vagrant-ubuntu-*:/vagrant$ runme ./config.yml


You can terminate the server by sending it a SIGINT (Ctrl-C from an interactive session).

Once the server is up and running, point your browser (host machine) to
``HTTP GET http://localhost:38000/probabilities/american/inventor/male``
to get a sample output based on a provided dataset.


Test framework
--------------

Run existing test suite with

.. code::

   (solo) vagrant@vagrant-ubuntu-*:/vagrant$ py.test
