from collections.abc import Sequence
import os
import pathlib
import subprocess

def option(name):
    return f'-{name}' if len(name) == 1 else f"--{name.replace('_', '-')}"

class Arguments:
    def __init__(self, args=(), kwargs={}):
        self.args = args
        self.kwargs = kwargs
    def __call__(self, *args, **kwargs):
        return Arguments(self.args + args, {**self.kwargs, **kwargs})

class Shell:
    here = subprocess.PIPE
    nowhere = subprocess.DEVNULL
    def __init__(self, popen=Arguments()):
        self.popen = popen
    def __call__(self, *args, **kwargs):
        return Shell(self.popen(*args, **kwargs))
    def __getattr__(self, program):
        return Command(program, self.popen)
    def __getitem__(self, program):
        return Command(program, self.popen)

class Command:
    def __init__(self, program, popen, argv=Arguments()):
        self.program = program
        self.popen = popen
        self.argv = argv
    def __call__(self, *args, **kwargs):
        return Command(self.program, self.popen, self.argv(*args, **kwargs))
    def __getattr__(self, kwarg):
        return Proxy(self, kwarg)
    def join(self):
        assert('stderr' not in self.popen.kwargs)
        return Command(self.program, self.popen(stderr=subprocess.STDOUT), self.argv)
    def flatten(self):
        command = [self.program]
        for k, v in self.argv.kwargs.items():
            if v is True:
                command.append(option(k))
            else:
                command.extend([option(k), str(v)])
        for v in self.argv.args:
            if v is False or v is None:
                continue
            if isinstance(v, (str, bytes)):
                command.append(v)
            elif isinstance(v, Sequence):
                # TODO: Recurse?
                command.extend(map(str, v))
            else:
                command.append(str(v))
        return command
    def start(self, *args, **kwargs):
        popen = self.popen(*args, **kwargs)
        return subprocess.Popen(self.flatten(), *popen.args, **popen.kwargs)
    def check(self, *args, **kwargs):
        popen = self.popen(*args, **kwargs)
        return subprocess.run(self.flatten(), check=True, *popen.args, **popen.kwargs)
    def __repr__(self):
        return f'{self.program}'
    def __or__(self, tail):
        return Pipeline([self]) | tail
    def __gt__(self, stdout):
        return Pipeline([self]) > stdout
    def __lt__(self, stdin):
        return Pipeline([self]) < stdin

class Proxy:
    def __init__(self, command, kwarg):
        self.command = command
        self.kwarg = kwarg
    def __call__(self, value):
        c = self.command
        return Command(c.program, c.popen(**{self.kwarg: value}), c.argv)

class Pipeline:
    def __init__(self, commands, stdin=None):
        self.commands = commands
        self.stdin = stdin
    def __repr__(self):
        r = ' | '.join(map(repr, self.commands))
        return r
    def __gt__(self, stdout):
        if stdout is None:
            stdout = subprocess.DEVNULL
        elif isinstance(stdout, Shell):
            stdout = None
        elif isinstance(stdout, str):
            stdout = open(stdout, 'wb')
        return self.check(stdout=stdout)
    def __lt__(self, stdin):
        assert(self.stdin is None)
        return Pipeline(self.commands, stdin=stdin)
    def __or__(self, tail):
        return Pipeline(self.commands + pipe(tail).commands, stdin=self.stdin)
    def check(self, stdout=None):
        # if command first, give it our stdin
        # if command first and stdin is bytes, close stdin
        # if command not first, give it stdin from previous command
        # if command last, give it our stdout, checkit, and return it
        # if command not last, give it subprocess.PIPE for stdout
        stdin = self.stdin
        if isinstance(stdin, str):
            stdin = stdin.encode()
        if isinstance(stdin, bytes):
            r, w = os.pipe()
            w = open(w, 'wb', buffering=0)
            w.write(stdin)
            w.close()
            stdin = open(r, 'rb', buffering=0)
        if isinstance(stdin, pathlib.Path):
            stdin = stdin.open('rb')

        stdout_ = subprocess.PIPE

        n = len(self.commands)
        first = 0
        last = n - 1
        for i in range(n):
            if i == last:
                method = 'check'
                stdout_ = stdout
                if isinstance(stdout_, (str, bytes, pathlib.Path)):
                    stdout_ = open(stdout_, 'wb')
            else:
                method = 'start'
            proc = getattr(self.commands[i], method)(stdin=stdin, stdout=stdout_)
            if stdin is not None:
                stdin.close()
            stdin = proc.stdout

        return proc

def pipe(x):
    return x if isinstance(x, Pipeline) else Pipeline([x])
