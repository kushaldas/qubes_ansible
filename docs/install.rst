How to install the project in dom0?
====================================

**dom0** is the special VM which has admin rights over the whole [Qubes
OS](https://qubes-os.org) system. To make use of this project, you will have to
install Ansible and this project in the **dom0**.

What about an admin domU AppVM?
--------------------------------

This should just work from an admin **domU** AppVM too. But, this feature is yet
to be tested.

There are two major parts of the project, one **qubes** connection plugin, and one
**qubesos** module.

Clone the project
------------------

In an AppVM, clone the git repo (we assume this vm's name is development).

::

    git clone https://github.com/kushaldas/qubes_ansible

Install the Ansible project
-----------------------------


On Qubes 4.2 please use the following command.

::

    sudo qubes-dom0-update ansible

Copy over the ansible_module directory to the dom0
---------------------------------------------------

We are assuming that you will copy it over ``/usr/share/ansible_module/``
directory and the source directory is checked out in
``/home/user/qubes_ansible`` directory in a vm named *development*.

Use the following commands to copy it over in **dom0**.

::

    sudo su -
    mkdir -p /usr/share/ansible_module/conns
    qvm-run --pass-io development 'cat /home/user/qubes_ansible/ansible_module/qubesos.py' > /usr/share/ansible_module/qubesos.py
    qvm-run --pass-io development 'cat /home/user/qubes_ansible/ansible_module/conns/qubes.py' > /usr/share/ansible_module/conns/qubes.py


Setup the configuration file
------------------------------

We will add the following two lines to ``/etc/ansible/ansible.cfg`` file.

::

    [defaults]
    library = /usr/share/ansible_module/
    connection_plugins = /usr/share/ansible_module/conns/


The above configuration file will help Ansible to find the module and the
connection plugin.



TODO (open question on how to install it)
===========================================

Should we just make sure if any vm is in running state, then that file should be
inside in the right place? or copy it over there?
