## Ansible connection and moudle for QubesOS

This is a written from scratch project to have a default Ansible connection
plugin to interact with [Qubes OS](https://qubes-os.org). There is also an
Ansible module to create/destroy/maintain state of the VM(s). 


## How to setup?

Put the ``qubes-rpc/qubes.Ansible`` qrexec service file in to the templateVMs
at ``/etc/qubes-rpc`` directory. The file must be executable (``chmod 755``).

If you are running Ansible from **dom0**, then no other configuration is 
required. Remember that right now you can create/destroy VMs only from
**dom0**.

It should also work from any VM wtih AdminAPI access. We need someone to test
that out.


If you want to use Ansible from any other AppVM(s) and maintain the state of
the Operating System inside of the other VM(s). You will also need to place
``bin/qvm-ansible`` file under the ``/usr/bin/`` directory of the same VM of
the Ansible controller.

Put the ``ansible_module`` directory in a known place; in our example,
we will put it in ``/usr/share/ansible_module``.

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

