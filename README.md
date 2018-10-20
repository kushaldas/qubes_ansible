## Ansible connection and moudle for QubesOS

This is a written from scratch project to have a default Ansible connection
plugin to interact with [Qubes OS](https://qubes-os.org). There is also an
Ansible module to create/destroy/maintain state of the VM(s). 


## How to setup?

Put the ``ansible_module`` directory in a known place; in our example,
we will put it in ``/usr/share/ansible_module``.

Remember that this project will only from **dom0** or any VM wtih AdminAPI
access.



## Installing Ansible and setup of the our module/connection

Install Ansible whichever way you like. In **dom0** it would be,

```
sudo qubes-dom0-update ansible-python3
```



Update your ``/etc/ansible/ansible.cfg`` to have the following two lines.

```
library = /usr/share/ansible_module/
connection_plugins = /usr/share/ansible_module/conns/ 
```

### How to write playbooks/roles tasks etc?


Just keep in mind that creating/destroying vms will require a **local** 
connection and will use the *qubesos* module.

To work on a remote VM, use **qubes** connection and use standard playbooks.


## Examples

Check the [examples](examples/) directory in this repo.

## Under development

This project is still very young, and, the **qubesos** module is under
heavy development so the syntax/keywords may change in future.

### License GPLv3+

Please see the [LICENSE](LICENSE) file for a complete copy of License.

## Documentation

Read it [online](https://qubes-ansible.readthedocs.io/en/latest/).


