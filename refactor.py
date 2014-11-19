
"""
SubliemRefactor is a sublime text plugin using rope refactoring library
Author: Yi Xie
Email: dnatag at gmail.com
Date: 03-21-2014
"""


import os
import functools
import tempfile
import re
import time
from string import Template
from threading import Thread

import sublime
import sublime_plugin
_execcmd = __import__("Default.exec", globals(), locals(), ['ExecCommand'])
ExecCommand = _execcmd.ExecCommand

settings_file = "PyRefactor.sublime-settings"
debug = False

rope_script = Template("""
import rope.base.project
from rope.base import libutils

myproject = rope.base.project.Project(
    '$proj_path')
#myproject.validate('$fname')
myproject.validate()
ropy = libutils.path_to_resource(myproject, '$fname')
$response_action
myproject.close()
""")

# TODO: check the presence of rope and python version


def convert_path(path):
    return path.replace('\\', '/')


def refactor_static(func):
    def _proj_finder(curr_view):
        base_path = curr_view.file_name()
        while base_path != os.path.abspath(os.sep):
            base_path, ext_path = os.path.split(base_path)
            if os.path.isfile(os.path.join(
                              base_path, '.ropeproject', 'config.py')):
                break

        if base_path == os.path.abspath(os.sep):
            return

        return base_path

    @functools.wraps(func)
    def _decorator(*args, **kwargs):
        curr_view = args[0].view
        proj = _proj_finder(curr_view)
        if proj is None:
            return
        return rope_script.substitute(proj_path=convert_path(proj),
                                      fname=convert_path(curr_view.file_name()),
                                      response_action=func(*args, **kwargs))
    return _decorator


def get_python_intepreter():
    settings = sublime.load_settings(settings_file)
    if settings.has("python_intepreter"):
        return settings.get("python_intepreter")
    return "python"


class RefactorBaseCommand(sublime_plugin.TextCommand):

    def refactor(self, *args, **kwargs):
        """ For overwritten only. This is the function will be decorated
        with wraps for static contents.
        The main goal of this function is to generate the dynamic partial
        of refactor script """
        raise NotImplementedError('Feature not yet implemented')

    def run(self, edit):
        self.run_refactor_script()
        self._force_reload()

    def on_done(self, input_answer):
        self.run_refactor_script(input_answer)
        self._force_reload()

    def run_refactor_script(self, *args, **kwargs):
        """ generate contents using decorated self.refactor function.
        Subsequently, write the contents to a temp file and run the
        temp script file """

        output = self.refactor(*args, **kwargs)
        if output is None:
            sublime.message_dialog(
                "No .ropeproject found !  Create a new rope project first "
                "and then re-run the rope operation.")
            sublime.active_view().run_command("refactor_create_project")
            return

        if debug:
            print(output)

        if kwargs.get("save_views", True):
            self._save_views()

        with tempfile.NamedTemporaryFile(
                mode='w', dir=os.path.dirname(self.view.file_name()),
                delete=False) as temp:
            temp.write(output)
            temp.flush()
            name = self._quote(temp.name)
            if os.name == 'nt':
                name = self._double_quote(temp.name)
            sublime.active_window().run_command('perform_refactor', {
                'shell_cmd': ' '.join([get_python_intepreter(), '-u', name])
            })

    def _save_views(self):
        # save all dirty files before refactoring
        for view in sublime.active_window().views():
            if view.is_dirty():
                view.run_command('save')

    def _force_reload(self):
        active_window = sublime.active_window()
        # Remember current self.view
        current_view = active_window.active_view()

        for view in active_window.views():
            active_window.focus_view(view)

        # Back to current self.view
        active_window.focus_view(current_view)

    def _quote(self, content):
        return '\'' + content + '\''

    def _double_quote(self, content):
        return '\"' + content + '\"'


class PerformRefactorCommand(ExecCommand):

    """ Required to cleanup the temp script """

    def run(self, *args, **kwargs):
        super().run(*args, **kwargs)
        self.progress_reporter = Thread(target=self.progress).start()

    def progress(self):
        while self.proc.poll():
            time.sleep(1)
            self.append_string(self.proc, ".")

    def finish(self, proc):
        if not self.quiet:
            elapsed = time.time() - proc.start_time
            exit_code = proc.exit_code()
            if exit_code == 0 or exit_code is None:
                self.append_string(proc,
                                  ("\n[Refactoring was successfully finished in %.1fs]"
                                   % (elapsed)))
            else:
                self.append_string(proc,
                                  ("\n[Refactoring was finished in %.1fs with exit code %d]\n"
                                   % (elapsed, exit_code)))
                self.append_string(proc, self.debug_text)

        # Terminate the reporter thread
        if self.progress_reporter:
            self.progress_reporter.join()

        if proc != self.proc:
            return

        errs = self.output_view.find_all_results()
        if len(errs) == 0:
            sublime.status_message("Refactoring finished without errors")
        else:
            sublime.status_message(
                ("Refactoring finished with %d errors") % len(errs))

        # cleanup the temp script file
        regexp = r"\[shell_cmd: %s -u \'(.+)\'\]" % get_python_intepreter()
        m = re.match(regexp, self.debug_text)
        if m is not None:
            os.unlink(m.group(1))


class RefactorCreateProjectCommand(RefactorBaseCommand):

    def run(self, edit):
        # if there is a sublime text project
        curr_view = self.view
        proj_folder = curr_view.window().project_file_name()
        # else creat a project at current file level
        if proj_folder is None:
            proj_folder = curr_view.file_name()
        project_path = os.path.dirname(proj_folder)

        active_window = sublime.active_window()
        active_window.show_input_panel(
            'Specifiy Rope project path:',
            project_path, self.on_done, None, None)

    def on_done(self, path):
        self.run_refactor_script(path)
        config_file = os.path.join(path, '.ropeproject', 'config.py')
        self.view.window().open_file(config_file)

    def refactor(self, *args, **kwargs):
        s = Template("""
import rope.base.project
myproject = rope.base.project.Project('$path')
myproject.close()
""")
        return s.substitute(path=convert_path(args[0]))


class RefactorUndoCommand(RefactorBaseCommand):

    @refactor_static
    def refactor(self, *args, **kwargs):
        return "myproject.history.undo()"


class RefactorRedoCommand(RefactorBaseCommand):

    @refactor_static
    def refactor(self, *args, **kwargs):
        return "myproject.history.redo()"


class RefactorSimpleCommand(RefactorBaseCommand):

    """ Extended RefactorBaseCommand class """
    funcs = {
        'ropy': '_ropy',
        'begin': '_begin',
        'begin_end': '_begin_end'
    }

    def _dynamic_content(self, module, func, new_change='',
                         change_param=('ropy', 'begin')):
        content = Template("""
from rope.refactor.$module import $func
changes = $func(myproject, $refactor_action).get_changes($change)
myproject.do(changes)
""")
        return content.substitute(
            func=func, module=module,
            refactor_action=
            ', '.join(self._call(x) for x in change_param if x is not None),
            change=new_change)

    def _call(self, func):
        if func in self.funcs:
            return getattr(self, self.funcs[func])()
        else:
            return func

    def _begin(self):
        return str(self._sel_word().a)

    def _begin_end(self):
        word = self._sel_word()
        return str(word.a) + ', ' + str(word.b)

    def _ropy(self):
        return 'ropy'

    def _sel_word(self):
        curr_sel_region = self.view.sel()[0]
        return self.view.word(curr_sel_region)


class RefactorInlineCommand(RefactorSimpleCommand):

    """ Rope inline method, variable, or parameter """
    @refactor_static
    def refactor(self, *args, **kwargs):
        return self._dynamic_content('inline', 'create_inline')


class RefactorLocalToFieldCommand(RefactorSimpleCommand):

    """ Rope local to field refactor """
    @refactor_static
    def refactor(self, *args, **kwargs):
        return self._dynamic_content('localtofield', 'LocalToField')


class RefactorUseFunctionCommand(RefactorSimpleCommand):

    """ Rope use function"""
    @refactor_static
    def refactor(self, *args, **kwargs):
        return self._dynamic_content('usefunction', 'UseFunction')


class RefactorEncapsulateFieldCommand(RefactorSimpleCommand):

    """ Rope encapsulate a field command with getter and setter """

    @refactor_static
    def refactor(self, *args, **kwargs):
        return self._dynamic_content('encapsulate_field', 'EncapsulateField')


class RefactorIntroduceParameterCommand(RefactorSimpleCommand):

    """ rope introduce parameter refactor """

    def run(self, edit):
        active_window = sublime.active_window()
        active_window.show_input_panel(
            'New parameter', '', self.on_done, None, None)

    @refactor_static
    def refactor(self, *args, **kwargs):
        return self._dynamic_content(
            'introduce_parameter', 'IntroduceParameter',
            self._quote(args[0]))


class RefactorMethodObjectCommand(RefactorSimpleCommand):

    """ Rope change function to method object """

    def run(self, edit):
        active_window = sublime.active_window()
        active_window.show_input_panel(
            'Destination class name:', '', self.on_done, None, None)

    @refactor_static
    def refactor(self, *args, **kwargs):
        return self._dynamic_content(
            'method_object', 'MethodObject',
            'classname=\'' + args[0] + '\'')


class RefactorMoveAttributeCommand(RefactorSimpleCommand):

    """ Rope move a globle function to different module """

    def run(self, edit):
        active_window = sublime.active_window()
        active_window.show_input_panel(
            'Destination attribute:', '', self.on_done, None, None)

    @refactor_static
    def refactor(self, *args, **kwargs):
        return self._dynamic_content(
            'move', 'create_move', self._quote(args[0]))


class RefactorRenameAttributeCommand(RefactorSimpleCommand):

    def run(self, edit):
        active_window = sublime.active_window()
        active_window.show_input_panel(
            'New name:', '', self.on_done, None, None)

    @refactor_static
    def refactor(self, *args, **kwargs):
        return self._dynamic_content(
            'rename', 'Rename',
            self._quote(args[0]) + ', docs=True')


class RefactorRenameModuleCommand(RefactorRenameAttributeCommand):

    @refactor_static
    def refactor(self, *args, **kwargs):
        return self._dynamic_content(
            'rename', 'Rename', self._quote(args[0]) + ', docs=True',
            change_param=['ropy'])


class RefactorModuleToPackageCommand(RefactorSimpleCommand):

    """ Rope transform module to package refactor """
    @refactor_static
    def refactor(self, *args, **kwargs):
        return self._dynamic_content(
            'topackage', 'ModuleToPackage', change_param=('ropy'))


class RefactorMoveGlobalCommand(RefactorSimpleCommand):

    """ Rope move a globle function to different module """

    def run(self, edit):
        active_window = sublime.active_window()
        active_window.show_input_panel(
            'Move destination file:', '', self.on_done, None, None)

    @refactor_static
    def refactor(self, *args, **kwargs):
        os.chdir(os.path.dirname(self.view.file_name()))
        dest_path = os.path.abspath(args[0])
        dest = "dest = libutils.path_to_resource(myproject, \'{0}\')\n".format(
            dest_path)

        return dest + self._dynamic_content('move', 'create_move', 'dest')


class RefactorExtractMethodCommand(RefactorSimpleCommand):

    """ Rope extract method from a block of codes"""

    def run(self, edit):
        active_window = sublime.active_window()
        active_window.show_input_panel(
            'Extracted method name:', '', self.on_done, None, None)

    @refactor_static
    def refactor(self, *args, **kwargs):
        return self._dynamic_content(
            'extract', 'ExtractMethod',
            self._quote(args[0]) + ', similar=True',
            change_param=('ropy', 'begin_end'))


class RefactorExtractVariableCommand(RefactorSimpleCommand):

    """ Rope extract variable from a block of codes"""

    def run(self, edit):
        active_window = sublime.active_window()
        active_window.show_input_panel(
            'Extracted variable name:', '', self.on_done, None, None)

    @refactor_static
    def refactor(self, *args, **kwargs):
        return self._dynamic_content(
            'extract', 'ExtractVariable', self._quote(args[0]),
            change_param=('ropy', 'begin_end'))


class RefactorRestructureCommand(RefactorSimpleCommand):

    """ rope restructure refactoring """

    def run(self, edit):
        active_window = sublime.active_window()
        active_window.show_input_panel(
            'Restructure script (pattern:goal:<args:>)',
            'pattern:',
            self.on_done, None, None)

    @refactor_static
    def refactor(self, *args, **kwargs):
        m = re.search(
            r'^pattern:\s*(.+?)\s*goal:\s*(.+?)\s*(?:args:\s*(.+?)\s*)?$',
            args[0])
        if m is None:
            raise ValueError('Unknown format of restructure script')

        pattern, goal, args_rest = m.groups()
        if args_rest is not None:
            args_rest = 'args={\'' +\
                '\': \''.join(s.strip() for s in args_rest.split(':')) +\
                '\'}'

        return self._dynamic_content(
            'restructure', 'Restructure', change_param=(
                self._quote(m.group(1)), self._quote(m.group(2)), args_rest))


class RefactorComplexCommand(RefactorSimpleCommand):

    _pat = re.compile(r'(def|class)\s+(\w+)\((.*?)\):')

    def _find_signiture(self, line, capture=3, sep='def '):
        current_view = sublime.active_window().active_view()
        if current_view.is_dirty():
            current_view.run_command('save')

        line = line.split(sep)[-1]
        with open(current_view.file_name(), 'rU') as f:
            for lines in f.read().split(sep):
                if line in lines:
                    strip_lines = sep + ' '.join(lines.split())
                    m = RefactorComplexCommand._pat.search(strip_lines)
                    if m is not None:
                        return m.group(capture)


class RefactorIntroduceFactoryCommand(RefactorComplexCommand):

    """ rope introduce class factory refactor """

    def run(self, edit):
        active_window = sublime.active_window()
        active_window.show_input_panel(
            'Factory name', '', self.on_done, None, None)

    @refactor_static
    def refactor(self, *args, **kwargs):
        line = ' '.join([self.view.substr(self.view.line(sel))
                         for sel in self.view.sel()])
        m = RefactorComplexCommand._pat.search(line)
        if m is not None:
            self.cls_name = m.group(2)
        else:
            self.cls_name = self._find_signiture(line, 2, 'class ')

        if self.cls_name is None:
            sublime.message_dialog('no class line detected!')
            return
        # TODO: change selection to cls_name to free user for the selection

        return self._dynamic_content(
            'introduce_factory', 'IntroduceFactory',
            self._quote(args[0]) + ', global_factory=False')


class RefactorChangeSignatureCommand(RefactorComplexCommand):

    """ Rope Change signature refactor """

    def run(self, edit):
        active_window = sublime.active_window()

        line = ' '.join([self.view.substr(self.view.line(sel))
                         for sel in self.view.sel()])
        m = RefactorComplexCommand._pat.search(line)
        if m is not None:
            self.old_signature = m.group(3)
        else:
            self.old_signature = self._find_signiture(line)

        if self.old_signature is None:
            sublime.message_dialog("No def line detected!")
            return

        active_window.show_input_panel(
            'New Signature (one change only):', ' '.join(
                self.old_signature.split('\n')),
            self.on_done, None, None)

    @refactor_static
    def refactor(self, *args, **kwargs):
        old_sign_dict = {}
        for index, item in enumerate(self.old_signature.split(',')):
            old_sign_dict[item.strip()] = index

        argument_order = []
        argument_adder = []

        for i, item in enumerate(args[0].split(',')):
            if item.strip() in old_sign_dict:
                argument_order.append(old_sign_dict[item.strip()])
            else:
                argument_adder.append((i, item.strip()))

        argument_remover = [old_sign_dict[key] for key in
                            old_sign_dict.keys() if key not in args[0]]

        changer1 = ""
        if len(argument_remover) == 1:
            # remover
            changer = "ArgumentRemover({0})".format(argument_remover[0])
            if len(argument_adder) == 1:
                changer1 = "change_signature.ArgumentAdder{0}".format(
                    argument_adder[0])
        elif len(argument_adder) == 1:
            # adder
            changer = "ArgumentAdder{0}".format(argument_adder[0])
        elif len(argument_order) == len(old_sign_dict):
            # reorder
            changer = "ArgumentReorderer({0})".format(argument_order)
        else:
            sublime.message_dialog(
                'Only single refactoring operation allowed!')
            return

        curr_sel_region = self.view.sel()[0]
        start = self.view.word(curr_sel_region).begin()
        contents = Template("""
from rope.refactor import change_signature
from rope.refactor.change_signature import *
changers=[$charger1]
changers.append(change_signature.$arg_change)
changes = ChangeSignature(myproject, ropy, $start).get_changes(changers)
myproject.do(changes)
""")
        return contents.substitute(arg_change=changer,
                                   start=start, charger1=changer1)
