Example tasks
==============

As we are developing the **qubesos** module heavily, the module will see some update
to the syntax of the commands and available options.

For now please check the given examples below to learn more.


Make sure a vm is present
-------------------------

This is the preferred method to create a new vm if it is not there.


::

    ---
    - hosts: local
    connection: local

    tasks:
        - name: Create our test vm
        qubesos:
            guest: supansible
            label: blue
            state: present
            template: "debian-9"

Only the *guest* name is the must have value, by default it will use the system default template and netvm.
The default label color is **red**.


Setting different preference values to a given vm
--------------------------------------------------

.. note:: This must be done when the vm is in shutdown state. Means this will also work while creating the vm.


::

    ---
    - hosts: local
    connection: local

    tasks:
        - name: Make sure the VM is present
        qubesos:
            guest: xchat2
            state: present
            preferences:
              memory: 1200
              maxmem: 2400
              netvm: 'sys-whonix'
              default_dispvm: 'fedora-28-dvm'
              label: "yellow"

        - name: Make sure the xchat7 is present
        qubesos:
            guest: xchat2
            state: present
           
        - name: Run the xchat2 VM
        qubesos:
            guest: xchat2
            state: running


.. note:: Always remember to move the state to running to get the vm up and running.


Available preferences
----------------------

The following are the different available preferences and their data type.

- 'autostart': bool
- 'debug': bool
- 'include_in_backups': bool
- 'kernel': str
- 'label': str
- 'maxmem': int
- 'memory': int
- 'provides_network': bool
- 'template': str
- 'template_for_dispvms': bool
- 'vcpus': int
- 'virt_mode': str
- 'default_dispvm': str
- 'netvm': str


If you want to make changes to any existing vm, then first move it to *shutdown*
state and then use preferences along with the *present* state to change any
value.


Different available states
---------------------------

- destroyed
- pause
- running
- shutdown
- undefine
- present

.. warning:: The **undefine** state will remove the vm and all data related to it. So, use with care.


Different available commands
-----------------------------

The following commands are currently available.

shutdown
+++++++++

It will try to shutdown the vm normally.

::

    ansible-3 localhost -i inventory -m qubesos -a 'guest=xhcat2 command=shutdown'

destroy
++++++++

The *destroy* command will forcefully shutdown the guest now.

::

    ansible-3 localhost -i inventory -m qubesos -a 'guest=xhcat2 command=destroy'


.. note:: Use the *destroyed* state to properly destroy a vm than this command.


Find all vms with a particular state
--------------------------------------

The following example will find all the vms with running state.

::

    ansible-3 localhost -i inventory -m qubesos -a 'state=running command=list_vms'


In the same way you can find vms with *shutdown* or *paused* state.


Our example inventory file
---------------------------

We will use the following inventory file for the following examples.

::

    [local]
    localhost

    [local:vars]
    ansible_connection=local

    [appvms]
    supansible
    xchat7

    [appvms:vars]
    ansible_connection=qubes

    [debian_templates]
    debian-9
    whonix-gw-14
    whonix-ws-14

    [debian_templates:vars]
    ansible_connection=qubes

    [fedora_templates]
    fedora-28

    [fedora_templates:vars]
    ansible_connection=qubes

Install a package and copy to file to the remote vm and fetch some file back
----------------------------------------------------------------------------

Here is an example playbook (install_packages.yaml) for the same.


::

    ---
    - hosts: xchat7
    tasks:
    - name: Ensure sl is at the latest version
        package: name=sl state=latest
    - name: example copying file with owner and permissions
        copy:
        src: foo.conf
        dest: /etc/foo.conf
    - name: Fetch os-relase
        fetch:
        src: /etc/os-release
        dest: /tmp/fetched


You can run the playbook using the following command.

::

    ansible-playbook -i inventory -b install_packages.yaml


You can also pass `-u different_user` or the set **ansible_user** value to run the above
playbook as a different user in the vm.
