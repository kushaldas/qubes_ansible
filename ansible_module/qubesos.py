#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Copyright: (c) 2018
# Kushal Das <mail@kushaldas.in>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: qubesos
short_description: Manages virtual machines supported by QubesOS
description:
     - Manages virtual machines supported by I(libvirt).
version_added: "2.8"
options:
  name:
    description:
      - name of the guest VM being managed. Note that VM must be previously
        defined with xml.
      - This option is required unless I(command) is C(list_vms).
  state:
    description:
      - Note that there may be some lag for state requests like C(shutdown)
        since these refer only to VM states. After starting a guest, it may not
        be immediately accessible.
    choices: [ destroyed, paused, running, shutdown ]
  command:
    description:
      - In addition to state management, various non-idempotent commands are available.
    choices: [ create, define, destroy,  info, list_vms, pause, shutdown, start, status, stop, unpause ]
  autostart:
    description:
      - start VM at host startup.
    type: bool
    version_added: "2.3"
  uri:
    description:
      - libvirt connection uri.
    default: qemu:///system
  xml:
    description:
      - XML document used with the define command.
      - Must be raw XML content using C(lookup). XML cannot be reference to a file.
requirements:
    - python >= 2.6
    - libvirt-python
author:
    - Ansible Core Team
    - Michael DeHaan
    - Seth Vidal
'''

EXAMPLES = '''
# a playbook task line:
- virt:
    name: alpha
    state: running

# /usr/bin/ansible invocations
# ansible host -m virt -a "name=alpha command=status"
# ansible host -m virt -a "name=alpha command=get_xml"
# ansible host -m virt -a "name=alpha command=create uri=lxc:///"

---
# a playbook example of defining and launching an LXC guest
tasks:
  - name: define vm
    virt:
        name: foo
        command: define
        xml: "{{ lookup('template', 'container-template.xml.j2') }}"
        uri: 'lxc:///'
  - name: start vm
    virt:
        name: foo
        state: running
        uri: 'lxc:///'
'''

RETURN = '''
# for list_vms command
list_vms:
    description: The list of vms defined on the remote system
    type: dictionary
    returned: success
    sample: [
        "build.example.org",
        "dev.example.org"
    ]
# for status command
status:
    description: The status of the VM, among running, crashed, paused and shutdown
    type: string
    sample: "success"
    returned: success
'''

import time
import traceback

try:
    import qubesadmin
    from qubesadmin.exc import QubesVMNotStartedError
except ImportError:
    HAS_QUBES = False
else:
    HAS_QUBES = True

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


VIRT_FAILED = 1
VIRT_SUCCESS = 0
VIRT_UNAVAILABLE = 2

ALL_COMMANDS = []
VM_COMMANDS = ['create', 'destroy', 'pause', 'shutdown', 'status', 'start', 'stop', 'unpause']
HOST_COMMANDS = ['info', 'list_vms', 'get_states']
ALL_COMMANDS.extend(VM_COMMANDS)
ALL_COMMANDS.extend(HOST_COMMANDS)

VIRT_STATE_NAME_MAP = {
    0: 'running',
    1: 'paused',
    4: 'shutdown',
    5: 'shutdown',
    6: 'crashed',
}


class VMNotFound(Exception):
    pass


class QubesVirt(object):

    def __init__(self, module):
        self.module = module
        self.app = qubesadmin.Qubes()

    def get_vm(self, vmname):
        return self.app.domains[vmname]

    def __get_state(self, domain):
        vm = self.app.domains[domain]
        if vm.is_paused():
            return "paused"
        if vm.is_running():
            return "running"
        if vm.is_halted():
            return "halted"

    def get_states(self):
        state = []
        for vm in self.app.domains:
            state.append("%s %s" % (vm.name, self.__get_state(vm.name)))
        return state

    def info(self):
        info = dict()
        for vm in self.app.domains:
            # libvirt returns maxMem, memory, and cpuTime as long()'s, which
            # xmlrpclib tries to convert to regular int's during serialization.
            # This throws exceptions, so convert them to strings here and
            # assume the other end of the xmlrpc connection can figure things
            # out or doesn't care.
            info[vm] = dict(
                state=self.__get_state(vm),
                networked=vm.is_networked()
            )

        return info


    # def autostart(self, vmid, as_flag):
    #     self.conn = self.__get_conn()
    #     # Change autostart flag only if needed
    #     if self.conn.get_autostart(vmid) != as_flag:
    #         self.conn.set_autostart(vmid, as_flag)
    #         return True

    #     return False


    def shutdown(self, vmname):
        """ Make the machine with the given vmname stop running.  Whatever that takes.  """
        vm = self.get_vm(vmname)
        vm.shutdown()
        return 0

    def pause(self, vmname):
        """ Pause the machine with the given vmname.  """

        vm = self.get_vm(vmname)
        vm.pause()
        return 0

    def unpause(self, vmname):
        """ Unpause the machine with the given vmname.  """

        vm = self.get_vm(vmname)
        vm.unpause()
        return 0

    def create(self, vmname, vmtype="AppVM", label="red", template=None, netvm="default"):
        """ Start the machine via the given vmid """
        network_vm = None
        if netvm == "default":
            network_vm = self.app.default_netvm
        elif not netvm:
            network_vm = None
        else:
            network_vm = self.get_vm(netvm)

        vm = self.app.add_new_vm(vmtype, vmname, label, template=template)
        vm.netvm = network_vm
        return 0

    def start(self, vmname):
        """ Start the machine via the given id/name """

        vm = self.get_vm(vmname)
        vm.start()
        return 0

    def destroy(self, vmname):
        """ Pull the virtual power from the virtual domain, giving it virtually no time to virtually shut down.  """
        vm = self.get_vm(vmname)
        vm.force_shutdown()
        return 0

    def undefine(self, vmname):
        """ Stop a domain, and then wipe it from the face of the earth.  (delete disk/config file) """
        try:
            self.destroy(vmname)
        except QubesVMNotStartedError:
            pass
            # Because it is not running

        while True:
            if self.__get_state(vmname) == "halted":
                break
            time.sleep(1)
        del self.app.domains[vmname]
        return 0

    def status(self, vmname):
        """
        Return a state suitable for server consumption.  Aka, codes.py values, not XM output.
        """
        return self.__get_state(vmname)



def core(module):

    state = module.params.get('state', None)
    guest = module.params.get('name', None)
    command = module.params.get('command', None)
    vmtype = module.params.get('vmtype', None)
    label = module.params.get('label', None)
    template = module.params.get('template', None)
    netvm = module.params.get('netvm', "default")
    preferences = module.params.get('preferences', None)

    v = QubesVirt(module)
    res = dict()

    if preferences:
        return VIRT_SUCCESS, {"status": preferences}

    if state and command == 'list_vms':
        res = v.list_vms(state=state)
        if not isinstance(res, dict):
            res = {command: res}
        return VIRT_SUCCESS, res

    if command == "get_states":
        states = v.get_states()
        res = {"states": states}
        return VIRT_SUCCESS, res



    if command:
        if command in VM_COMMANDS:
            if not guest:
                module.fail_json(msg="%s requires 1 argument: guest" % command)
            if command == 'create':
                # if not xml:
                #     module.fail_json(msg="define requires xml argument")
                try:
                    v.get_vm(guest)
                except KeyError:
                    v.create(guest, vmtype, label, template, netvm)
                    res = {'changed': True, 'created': guest}
                return VIRT_SUCCESS, res
            res = getattr(v, command)(guest)
            if not isinstance(res, dict):
                res = {command: res}
            return VIRT_SUCCESS, res

        elif hasattr(v, command):
            res = getattr(v, command)()
            if not isinstance(res, dict):
                res = {command: res}
            return VIRT_SUCCESS, res

        else:
            module.fail_json(msg="Command %s not recognized" % command)

    if state:
        if not guest:
            module.fail_json(msg="state change requires a guest specified")

        if state == 'running':
            if v.status(guest) is 'paused':
                res['changed'] = True
                res['msg'] = v.unpause(guest)
            elif v.status(guest) is not 'running':
                res['changed'] = True
                res['msg'] = v.start(guest)
        elif state == 'shutdown':
            if v.status(guest) is not 'shutdown':
                res['changed'] = True
                res['msg'] = v.shutdown(guest)
        elif state == 'destroyed':
            if v.status(guest) is not 'shutdown':
                res['changed'] = True
                res['msg'] = v.destroy(guest)
        elif state == 'paused':
            if v.status(guest) is 'running':
                res['changed'] = True
                res['msg'] = v.pause(guest)
        elif state == 'undefine':
            if v.status(guest) is not 'shutdown':
                res['changed'] = True
                res['msg'] = v.undefine(guest)
        else:
            module.fail_json(msg="unexpected state")

        return VIRT_SUCCESS, res


    module.fail_json(msg="expected state or command parameter to be specified")


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', aliases=['guest']),
            state=dict(type='str', choices=['destroyed', 'pause', 'running', 'shutdown', 'undefine']),
            command=dict(type='str', choices=ALL_COMMANDS),
            label=dict(type='str', default='red'),
            vmtype=dict(type='str', default='AppVM'),
            template=dict(type='str', default='default'),
            netvm=dict(type='str', default='default'),
            preferences=dict(type='dict', default={}),
        ),
    )

    if not HAS_QUBES:
        module.fail_json(msg='The `qubesos` module is not importable. Check the requirements.')

    rc = VIRT_SUCCESS
    try:
        rc, result = core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    if rc != 0:  # something went wrong emit the msg
        module.fail_json(rc=rc, msg=result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
