Example tasks
==============

As we are developing the **qubesos** module heavily, the module will see some update
to the syntax of the commands and available options.

For now please check the given examples below to learn more.


Our example inventory file
---------------------------

We can use the following command to create our inventory file. This will
automatically include all of the VMs in your Qubes. You'll have to re-run
it after creating new VMs, if you want ansible to be able to work with them.

.. warning:: Remember that the following command will rewrite the inventory file.


::

    ansible-3 localhost -m qubesos -a 'command=createinventory'

Once you have an inventory file, you can run ansible playbooks like this:

::

    ansible-playbook-3 -i inventory my_playbook.yaml


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


Setting different property values to a given vm
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
            properties:
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


Available properties
----------------------

The following are the different available properties and their data type.

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
- 'features': dict[str,str]


If you want to make changes to any existing vm, then first move it to *shutdown*
state and then use properties along with the *present* state to change any
value.

We can even add/update/remove ``features`` from a VM using properties.

::

    ---
    - hosts: local
    connection: local

    tasks:
        - name: Make sure the VM is present with right features
        qubesos:
            guest: xchat2
            state: present
            properties:
              memory: 1200
              maxmem: 2400
              netvm: 'sys-whonix'
              default_dispvm: 'fedora-28-dvm'
              label: "yellow"
              features:
                life: "better"
                can_fix_world_problem: False
                news: "good"


To delete a feature (if that exists), mark the value as **"None"**. To make it
an empty string, that is the False value, use **""** as value. Example is given
below.

::

    features:
      life: "None"
      news: ""


Adding tags to a vm
-------------------

We can also add tags to a VM using the tags values. It has to be a list of strings.

::

    ---
    - hosts: local
    connection: local

    tasks:
        - name: Make sure right tags are assigned
        qubesos:
            guest: xchat2
            state: present
            tags:
              - "Linux"
              - "IRC"
              - "Chat"

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

removetags
+++++++++++

Use this command with a list of tags to remove them from a given VM.

::

    ---
    - hosts: local
    connection: local

    tasks:
        - name: Make sure right tags are removed
        qubesos:
            guest: xchat2
            command: removetags
            tags:
              - "Linux"
              - "IRC"
              - "Chat"

Find all vms with a particular state
--------------------------------------

The following example will find all the vms with running state.

::

    ansible-3 localhost -i inventory -m qubesos -a 'state=running command=list_vms'


In the same way you can find vms with *shutdown* or *paused* state.


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


Execute a command in every running vm
---------------------------------------

First remember to create our inventory file using ``createinventory`` command.
Then you can use the following playbook. We are just running ``hostname`` command
in every running vm.

::

    ---
    - hosts: localhost
    connection: local
    tasks:
        - name: Find running hosts
        qubesos:
            command: list_vms
            state: running
        register: rhosts

    - hosts: "{{ hostvars['localhost']['rhosts']['list_vms'] }}"
    connection: qubes
    tasks:
        - name: get hostname
        command: hostname


Execute a command in every running vm except sys vms
-----------------------------------------------------

::

    ---
    - hosts: localhost
    connection: local
    tasks:
        - name: Find running hosts
        qubesos:
            command: list_vms
            state: running
        register: rhosts

        - name: Find non system vms
        set_fact:
            myvms: "{% for name in rhosts.list_vms %}{% if not name.startswith('sys-') %}{{ name }},{% endif %}{% endfor %}"


    - hosts: "{{ hostvars['localhost']['myvms'] }}"
    connection: qubes
    tasks:
        - name: Get hostname
        command: hostname

Shutdown all vms except the system vms
----------------------------------------

We are not shutting down any VM which starts with **sys-** in this example.

::

    ---
    - hosts: localhost
    connection: local
    tasks:
        - name: Find running hosts
        qubesos:
            command: list_vms
            state: running
        register: rhosts

        - debug: var=rhosts

        - name: Shutdown each vm
        qubesos:
            command: destroy
            guest: "{{ item }}"
        with_items: "{{ rhosts.list_vms }}"
        when: item.startswith("sys-") != True


You can use the above ``shutdown_all.yaml`` playbook using the following command.

::

    ansible-playbook -i inventory -b shutdown_all.yaml
