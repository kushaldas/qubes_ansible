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

Install the Ansible project
-----------------------------

::

    sudo qubes-dom0-update ansible-python3


Copy over the ansible_module directory to the dom0
---------------------------------------------------

We are assuming that you will copy it over ``/usr/share/ansible_module/``
directory and the source directory is checked out in
``/home/user/qubes_ansible`` directory in a vm named *development*.

Use the following commands to copy it over in **dom0**.

::

    sudo su -
    mkdir -p /usr/share/ansible_module/conns
    qvm-run --pass-io development /home/user/qubes_ansible/ansible_module/qubesos.py > /usr/share/ansible_module/qubesos.py
    qvm-run --pass-io development /home/user/qubes_ansible/ansible_module/conns/qubes.py > /usr/share/ansible_module/conns/qubes.py


Setup the configuration file
------------------------------

We will add the following two lines to ``/etc/ansible/ansible.cfg`` file.

::

    library = /usr/share/ansible_module/
    connection_plugins = /usr/share/ansible_module/conns/ 


The above configuration file will help Ansible to find the module and the
connection plugin.


Copy over the qubes.Ansible qrexec service to the templates
------------------------------------------------------------

In future we hope this service will come by default in the templates. For now,
we can just copy over the service to the right location to all of the
templateVMs.

From the *development* vm, inside of our project directory, give this command.

::

    qvm-copy qubes-rpc/qubes.Ansible

And, after coping the file, start the template, and copy it to the right place.

::

    sudo mv ~/QubesIncoming/development/qubes.Ansible /etc/qubes-rpc/
    chmod +x /etc/qubes-rpc/qubes.Ansible


Also install the ``bin/qvm-ansible`` command if you want to manage things from
an admin domU VM.

**qubes-core-admin-client** is the packge which has all the required Python
modules and also the commands. This is by default installed in the **dom0**.


TODO (open qubestion on how to install it)
===========================================

Should we just make sure if any vm is in running state, then that file should be
inside in the right place? or copy it over there?

