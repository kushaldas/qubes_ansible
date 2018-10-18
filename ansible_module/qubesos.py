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

PREFS = {'autostart': bool,
         'debug': bool,
         'include_in_backups': bool,
         'kernel': str,
         'label': str,
         'maxmem': int,
         'memory': int,
         'provides_network': bool,
         'template': str,
         'template_for_dispvms': bool,
         'vcpus': int,
         'virt_mode': str,
         'default_dispvm': str,
         'netvm': str
        }



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
            return "shutdown"

    def get_states(self):
        state = []
        for vm in self.app.domains:
            state.append("%s %s" % (vm.name, self.__get_state(vm.name)))
        return state

    def list_vms(self, state):
        res = []
        for vm in self.app.domains:
            if vm.name != "dom0" and state == self.__get_state(vm.name):
                res.append("%s" % vm.name)
        return res

    def info(self):
        info = dict()
        for vm in self.app.domains:
            if vm.name == "dom0":
                continue
            info[vm.name] = dict(
                state=self.__get_state(vm),
                provides_network=vm.provides_network,
                label=vm.label.name,
            )

        return info


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

    def preferences(self, vmname, prefs, vmtype):
        "Sets the given preferences to the VM"
        changed = False
        vm = None
        values_changed = []
        try:
            vm = self.get_vm(vmname)
        except KeyError:
            # Means first we have to create the vm
            self.create(vmname, vmtype)
            vm = self.get_vm(vmname)
        if "autostart" in prefs and vm.autostart != prefs["autostart"]:
            vm.autostart = prefs["autostart"]
            changed = True
            values_changed.append("autostart")
        if "debug" in prefs and vm.debug != prefs["debug"]:
            vm.debug = prefs["debug"]
            changed = True
            values_changed.append("debug")
        if "include_in_backups" in prefs and vm.include_in_backups != prefs["include_in_backups"]:
            vm.include_in_backups = prefs["include_in_backups"]
            changed = True
            values_changed.append("include_in_backups")
        if "kernel" in prefs and vm.kernel != prefs["kernel"]:
            vm.kernel = prefs["kernel"]
            changed = True
            values_changed.append("kernel")
        if "label" in prefs and vm.label.name != prefs["label"]:
            vm.label = prefs["label"]
            changed = True
            values_changed.append("label")
        if "maxmem" in prefs and vm.maxmem != prefs["maxmem"]:
            vm.maxmem = prefs["maxmem"]
            changed = True
            values_changed.append("maxmem")
        if "memory" in prefs and vm.memory != prefs["memory"]:
            vm.memory = prefs["memory"]
            changed = True
            values_changed.append("memory")
        if "provides_network" in prefs and vm.provides_network != prefs["provides_network"]:
            vm.provides_network = prefs["provides_network"]
            changed = True
            values_changed.append("provides_network")
        if "netvm" in prefs:
            netvm = self.app.domains[prefs["netvm"]]
            if vm.netvm != netvm:
                vm.netvm = netvm
                changed = True
                values_changed.append("netvm")
        if "default_dispvm" in prefs:
            default_dispvm = self.app.domains[prefs["default_dispvm"]]
            if vm.default_dispvm != default_dispvm:
                vm.default_dispvm = default_dispvm
                changed = True
                values_changed.append("default_dispvm")
        if "template" in prefs:
            template = self.app.domains[prefs["template"]]
            if vm.template != template:
                vm.template = template
                changed = True
                values_changed.append("template")
        if "template_for_dispvms" in prefs and vm.template_for_dispvms != prefs["template_for_dispvms"]:
            vm.template_for_dispvms = prefs["template_for_dispvms"]
            changed = True
            values_changed.append("template_for_dispvms")
        if "vcpus" in prefs and vm.vcpus != prefs["vcpus"]:
            vm.vcpus = prefs["vcpus"]
            changed = True
            values_changed.append("vcpus")
        if "virt_mode" in prefs and vm.virt_mode != prefs["virt_mode"]:
            vm.virt_mode = prefs["virt_mode"]
            changed = True
            values_changed.append("virt_mode")
        return changed, values_changed


    def undefine(self, vmname):
        """ Stop a domain, and then wipe it from the face of the earth.  (delete disk/config file) """
        try:
            self.destroy(vmname)
        except QubesVMNotStartedError:
            pass
            # Because it is not running

        while True:
            if self.__get_state(vmname) == "shutdown":
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
    vmtype = module.params.get('vmtype', 'AppVM')
    label = module.params.get('label', 'red')
    template = module.params.get('template', None)
    netvm = module.params.get('netvm', "default")
    preferences = module.params.get('preferences', {})

    v = QubesVirt(module)
    res = dict()

    # Preferences will only work with state=present
    if preferences:
        for key,val in preferences.items():
            if not key in PREFS:
                return VIRT_FAILED, {"Invalid preference": key}
            if type(val) != PREFS[key]:
                return VIRT_FAILED, {"Invalid preference value type": key}
            # Make sure that the netvm exists
            if key == "netvm" and val != "":
                try:
                    vm = v.get_vm(val)
                except KeyError:
                    return VIRT_FAILED, {"Missing netvm": val}
                # Also the vm should provide network
                if not vm.provides_network:
                    return VIRT_FAILED, {"Missing netvm capability": val}
                    template_for_dispvms

            # Make sure that the default_dispvm exists
            if key == "default_dispvm":
                try:
                    vm = v.get_vm(val)
                except KeyError:
                    return VIRT_FAILED, {"Missing default_dispvm": val}
                # Also the vm should provide network
                if not vm.template_for_dispvms:
                    return VIRT_FAILED, {"Missing dispvm capability": val}
        if state == "present" and guest and vmtype:
            changed, changed_values = v.preferences(guest, preferences, vmtype)
            return VIRT_SUCCESS, {"Preferences updated": changed_values, "changed": changed}

    if state == "present" and guest and vmtype:
        try:
            v.get_vm(guest)
            res = {"changed": False, "status": "VM is present."}
        except KeyError:
            v.create(guest, vmtype, label, template, netvm)
            res = {'changed': True, 'created': guest}
        return VIRT_SUCCESS, res

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
            state=dict(type='str', choices=['destroyed', 'pause', 'running', 'shutdown', 'undefine', 'present']),
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
