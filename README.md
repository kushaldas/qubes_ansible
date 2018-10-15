## Ansible connection and moudle for QubesOS

This is a written from scratch project to have a default Ansible connection
plugin to interact with [Qubes OS](https://qubes-os.org). This also an Ansible
module to create/destroy/maintain state of the VM(s). 


## How to setup?

Put the ``qubes-rpc/qubes.Ansible`` qrexec service file in to the templateVMs
at ``/etc/qubes-rpc`` directory.

If you are using running Ansible from **dom0**, then no other configuration
is required. Remember that right now you can create/destroy VMs only from
**dom0**.


If you want to use Ansible from any other AppVM(s) and maintain the state of
the Operating System inside of the other VM(s). You will also need to place
``bin/qvm-ansible`` file under the ``/usr/bin/`` directory of the same VM of
the Ansible controller.

Put the ``ansbile_module`` directory to a known place, in our example,
we will put it in ``/usr/share/ansible_module``.

## Installing Ansible and setup of the our module/connection

Install Ansible which everway you like. In **dom0** it would be like,

```
sudo qubes-dom0-update ansible-python3
```



Update your ``/etc/ansible.cfg`` to have the following two lines.

```
library = /usr/share/ansible_module/
connection_plugins = /usr/share/ansible_module/conns/ 
```

### How to write playbooks/roles tasks etc?


Just keep in mind that the creation/detroying of the vms will require a
**local** connection and will use the *qubesos* module.

To work on the remote VM, use **qubes** connection and use standard playbooks.


## Under development

This project is still very young, and the **qubesos** module will go under
heavy development, and also the syntax/keywords will may change.



### License GPLv3+
