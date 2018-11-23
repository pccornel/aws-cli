# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
from awscli.customizations.wizard import devcommands, factory
from awscli.customizations.wizard.loader import WizardLoader
from awscli.customizations.commands import BasicCommand


def register_wizard_commands(event_handlers):
    devcommands.register_dev_commands(event_handlers)
    loader = WizardLoader()
    commands = loader.list_commands_with_wizards()
    _register_wizards_for_commands(commands, event_handlers)


def _register_wizards_for_commands(commands, event_handlers):
    for command in commands:
        event_handlers.register('building-command-table.%s' % command,
                                _add_wizard_command)




def _add_wizard_command(session, command_object, command_table, **kwargs):
    runner = factory.create_default_wizard_runner(session)
    cmd = WizardCommand(
        session=session,
        loader=WizardLoader(),
        parent_command=command_object.name,
        runner=runner,
    )
    command_table['wizard'] = cmd


class WizardCommand(BasicCommand):
    def __init__(self, session, loader, parent_command, runner,
                 wizard_name='_main'):
        self._session = session
        self._loader = loader
        self._parent_command = parent_command
        self._runner = runner
        self._wizard_name = wizard_name

    def _build_subcommand_table(self):
        subcommand_table = super(WizardCommand, self)._build_subcommand_table()
        wizards = self._loader.list_available_wizards(self._parent_command)
        for name in wizards:
            cmd = WizardCommand(self._session, self._loader,
                                self._parent_command, self._runner,
                                wizard_name=name)
            subcommand_table[name] = cmd
        self._add_lineage(subcommand_table)
        return subcommand_table

    def _run_main(self, parsed_args, parsed_globals):
        if self._wizard_exists():
            self._run_wizard()
            return 0
        else:
            self._raise_usage_error()

    def _wizard_exists(self):
        return self._loader.wizard_exists(self._parent_command,
                                          self._wizard_name)

    def _run_wizard(self):
        loaded = self._loader.load_wizard(
            self._parent_command, self._wizard_name)
        self._runner.run(loaded)

    def _raise_usage_error(self):
        raise ValueError("usage: aws [options] <command> <subcommand> "
                            "[parameters]\naws: error: too few arguments")
