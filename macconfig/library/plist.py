#!/usr/bin/python
# -*- coding: utf-8 -*-

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

class PListException(Exception):
    pass

class PListExtension(object):
    def __init__(self, **kwargs):
        # Just set all given parameters
        for key, val in kwargs.items():
            setattr(self, key, val)

        # We require a value if present
        if self.state == 'present' and self.value is None:
            raise PListException("Missing value parameter")

        if self.state == 'present' and not self.value_type:
            raise PListException("Missing type parameter")

    def current_value(self):
        cmd = "Print " + self.entry
        rc, out, err = self.module.run_command([self.executable, "-c", cmd, self.out_file])

        if rc not in [0, 1]:
            raise PListException("An error occurred while checking value: " + out)

        if rc == 0:
            return out.strip()

        if rc == 1:
            # also returns 1 if file does not exist, maybe we want to do something about that? ¯\_(ツ)_/¯
            return None
    
    def add_value(self):
        cmd = "Add %s %s %s" % (self.entry, self.value_type, self.value)
        rc, out, err = self.module.run_command([self.executable, "-c", cmd, self.out_file])
        if rc != 0:
            raise PListException("An error occurred while adding value: " + out)

    def set_value(self):
        cmd = "Set %s %s" % (self.entry, self.value)
        rc, out, err = self.module.run_command([self.executable, "-c", cmd, self.out_file])
        if rc != 0:
            raise PListException("An error occurred while setting value: " + out)
    
    def clear_value(self):
        cmd = "Delete " + self.entry
        rc, out, err = self.module.run_command([self.executable, "-c", cmd, self.out_file])
        if rc != 0:
            raise PListException("An error occurred while deleting value: " + out)

    def run(self):
        val = self.current_value()

        # Handle absent state
        if self.state == "absent":
            if val is None:
                return False
            if self.module.check_mode:
                return True
            self.clear_value()
            return True
        
        # Handle present state (new entry)
        if val is None:
            if self.module.check_mode:
                return True
            self.add_value()
            return True

        # Handle present state (existing entry)
        if self.value_equals(val):
            return False
        if self.module.check_mode:
            return True
        self.set_value()
        return True

    def value_equals(self, v):
        if self.value_type == "bool":
            expected = v == "true"
            return self.value is expected
        if self.value_type == "integer":
            return self.value == int(v)
        if self.value_type == "real":
            return self.value == float(v)
        return self.value == v

def main():
    module = AnsibleModule(
        argument_spec=dict(
            file=dict(
                require=True,
                type='str'
            ),
            entry=dict(
                required=True,
                type='str',
            ),
            type=dict(
                choices=[
                    'string',
                    # 'array',
                    # 'dict',
                    'bool',
                    'real',
                    'integer',
                    # 'date',
                    # 'data'
                ],
                default='string',
            ),
            value=dict(
                required=True,
                type='raw',
            ),
            state=dict(
                default="present",
                required=False,
                choices=[
                    "absent", "present"
                ],
            ),
            plistbuddy_executable=dict(
                default='/usr/libexec/PlistBuddy',
                required=False,
                type='str',
            )
        ),
        supports_check_mode=True,
    )

    out_file = module.params['file']
    entry = module.params['entry']
    value_type = module.params['type']
    value = module.params['value']
    state = module.params['state']
    executable = module.params['plistbuddy_executable']

    if value_type == "integer":
        # YAML parser parses all numbers as floats
        value = int(value)

    try:
        plist = PListExtension(module=module, out_file=out_file, entry=entry, value_type=value_type, value=value, state=state, executable=executable)
        changed = plist.run()
        module.exit_json(changed=changed)
    except PListException as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
