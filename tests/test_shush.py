import contextlib
import os
import pathlib
import pytest
import subprocess
import shush
import tempfile


@contextlib.contextmanager
def named_temp_file():
    """
    Return (file, path) for a temporary file that is deleted only when the
    context exits, not when the file is closed.
    """
    file, path = tempfile.mkstemp()
    file = os.fdopen(file, 'wb')
    try:
        yield file, pathlib.Path(path)
    finally:
        file.close()
        os.remove(path)

sh = shush.Shell()

def test_success():
    sh.true > sh

def test_failure():
    with pytest.raises(subprocess.CalledProcessError):
        sh.false > sh

def test_output():
    proc = sh.echo('hello') > sh.here
    assert(proc.stdout == b'hello\n')

def test_pipe():
    proc = sh.echo('hello') | sh.cat > sh.here
    assert(proc.stdout == b'hello\n')

def test_tail():
    proc = sh.echo('hello\ngoodbye') | sh.tail('-1') > sh.here
    assert(proc.stdout == b'goodbye\n')

def test_arg_if_then():
    proc = sh.echo('hello', False and 'goodbye') > sh.here
    assert(proc.stdout == b'hello\n')

def test_arg_none():
    proc = sh.echo(None, 'hello') > sh.here
    assert(proc.stdout == b'hello\n')

def test_arg_if_else():
    proc = sh.echo('goodbye' if False else 'hello') > sh.here
    assert(proc.stdout == b'hello\n')

def test_arg_list():
    proc = sh.echo('a', ['b', 'c'], 'd') > sh.here
    assert(proc.stdout == b'a b c d\n')

def test_arg_tuple():
    proc = sh.echo('a', ('b', 'c'), 'd') > sh.here
    assert(proc.stdout == b'a b c d\n')

def test_kwarg_bool():
    proc = sh.python(version=True) > sh.here
    assert(proc.stdout.startswith(b'Python 3.'))

def test_kwarg_short():
    proc = sh.python(c='import sys; sys.stdout.write("hello")') > sh.here
    assert(proc.stdout == b'hello')

def test_kwarg_long():
    proc = sh.env.env({'foo': 'bar'}) | sh.grep(regexp='foo') > sh.here
    assert(proc.stdout == b'foo=bar\n')

def test_stdin_str():
    proc = (sh.cat < 'hello') > sh.here
    assert(proc.stdout == b'hello')

def test_stdin_bytes():
    proc = (sh.cat < b'hello') > sh.here
    assert(proc.stdout == b'hello')

def test_stdin_file():
    with named_temp_file() as (file, path):
        file.write(b'hello')
        file.close()
        file = open(path, 'rb')
        proc = (sh.cat < file) > sh.here
        assert(proc.stdout == b'hello')
        assert(file.closed)

def test_stdin_path():
    with named_temp_file() as (file, path):
        file.write(b'hello')
        file.close()
        proc = (sh.cat < path) > sh.here
        assert(proc.stdout == b'hello')

def test_shell_env():
    sh_ = sh(env={'foo': 'bar'})
    proc = sh_.env | sh_.grep('foo') > sh_.here
    assert(proc.stdout == b'foo=bar\n')

def test_command_env():
    proc = sh.env.env({'foo': 'bar'}) | sh.grep('foo') > sh.here
    assert(proc.stdout == b'foo=bar\n')

def test_command_cwd():
    cwd = pathlib.Path('.').resolve().parent
    proc = sh.pwd.cwd(cwd) > sh.here
    assert(proc.stdout == f'{cwd}\n'.encode())

def test_command_cwd_chain():
    cwd = pathlib.Path('.').resolve().parent
    proc = sh.pwd.cwd('/does/not/exist').cwd(cwd) > sh.here
    assert(proc.stdout == f'{cwd}\n'.encode())

def test_stdout_file():
    with named_temp_file() as (file, path):
        sh.echo('hello') > file
        # Input files should be closed.
        # Output files do not need to be.
        assert(not file.closed)
        assert(path.read_bytes() == b'hello\n')

def test_stdout_path():
    with named_temp_file() as (file, path):
        file.close()
        sh.echo('hello') > path
        assert(path.read_bytes() == b'hello\n')

def test_stdout_str():
    with named_temp_file() as (file, path):
        file.close()
        sh.echo('hello') > str(path)
        assert(path.read_bytes() == b'hello\n')

def test_stdout_bytes():
    with named_temp_file() as (file, path):
        file.close()
        sh.echo('hello') > bytes(path)
        assert(path.read_bytes() == b'hello\n')

def test_stdout_nowhere():
    proc = sh.echo('hello') > sh.nowhere
    assert(proc.stdout is None)

def test_join():
    proc = sh.python(c='import sys; sys.stderr.write("hello")').join() > sh.here
    assert(proc.stdout == b'hello')

def test_command_path():
    proc = sh['/bin/echo']('hello') > sh.here
    assert(proc.stdout == b'hello\n')
