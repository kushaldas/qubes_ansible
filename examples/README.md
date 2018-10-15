## How to try out the examples?


Update your **dom0** ``/etc/ansible/ansible.cfg`` as below.

```
library = /usr/share/ansible_module/
connection_plugins = /usr/share/ansible_module/conns/ 
```

And make sure that you have the ``ansible_module`` directory from this project
in the right place.

### The inventory file

```
[local]
localhost

[local:vars]
ansible_connection=local

[appvms]
supansible
xchat

[appvms:vars]
ansible_connection=qubes
```

### Running the playbooks from dom0

To create the vms

```
ansible-playbook-3 -i inventory create_vm.yaml
```

To delete one particular vm

```
ansible-playbook-3 -i inventory undefine_vm.yaml
```

To install packages in the *xchat* vm

```
ansible-playbook-3 -i inventory -b install_packages.yaml
```