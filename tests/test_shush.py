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

@pytest.fixture()
def sh():
    return shush.Shell().here

def test_success(sh):
    sh.true > sh

def test_failure(sh):
    with pytest.raises(subprocess.CalledProcessError):
        sh.false > sh

def test_output(sh):
    proc = sh> sh.echo('hello')
    assert(proc.stdout == b'hello\n')

def test_prompt(sh):
    sh> sh.true

def test_pipe(sh):
    proc = sh> sh.echo('hello') | sh.cat
    assert(proc.stdout == b'hello\n')

def test_tail(sh):
    proc = sh> sh.echo('hello\ngoodbye') | sh.tail('-1')
    assert(proc.stdout == b'goodbye\n')

def test_arg_if_then(sh):
    proc = sh> sh.echo('hello', False and 'goodbye')
    assert(proc.stdout == b'hello\n')

def test_arg_none(sh):
    proc = sh> sh.echo(None, 'hello')
    assert(proc.stdout == b'hello\n')

def test_arg_if_else(sh):
    proc = sh> sh.echo('goodbye' if False else 'hello')
    assert(proc.stdout == b'hello\n')

def test_arg_list(sh):
    proc = sh> sh.echo('a', ['b', 'c'], 'd')
    assert(proc.stdout == b'a b c d\n')

def test_arg_tuple(sh):
    proc = sh> sh.echo('a', ('b', 'c'), 'd')
    assert(proc.stdout == b'a b c d\n')

def test_kwarg_bool(sh):
    proc = sh> sh.python(version=True)
    assert(proc.stdout.startswith(b'Python 3.'))

def test_kwarg_short(sh):
    proc = sh> sh.python(c='import sys; sys.stdout.write("hello")')
    assert(proc.stdout == b'hello')

def test_kwarg_long(sh):
    proc = sh> sh.env.env({'foo': 'bar'}) | sh.grep(regexp='foo')
    assert(proc.stdout == b'foo=bar\n')

def test_stdin_str(sh):
    proc = sh> (sh.cat < 'hello')
    assert(proc.stdout == b'hello')

def test_stdin_bytes(sh):
    proc = sh> (sh.cat < b'hello')
    assert(proc.stdout == b'hello')

def test_stdin_file(sh):
    with named_temp_file() as (file, path):
        file.write(b'hello')
        file.close()
        file = open(path, 'rb')
        proc = sh> (sh.cat < file)
        assert(proc.stdout == b'hello')
        assert(file.closed)

def test_stdin_path(sh):
    with named_temp_file() as (file, path):
        file.write(b'hello')
        file.close()
        proc = sh> (sh.cat < path)
        assert(proc.stdout == b'hello')

def test_shell_env(sh):
    sh = sh(env={'foo': 'bar'})
    proc = sh> sh.env | sh.grep('foo')
    assert(proc.stdout == b'foo=bar\n')

def test_shell_env_op(sh):
    sh = sh % {'foo': 'bar'}
    proc = sh> sh.env | sh.grep('foo')
    assert(proc.stdout == b'foo=bar\n')

def test_shell_cwd(sh):
    cwd = pathlib.Path('.').resolve()
    sh = sh(cwd=cwd)
    proc = sh> sh.pwd
    assert(proc.stdout == f'{cwd}\n'.encode())

def test_shell_cwd_op(sh):
    cwd = pathlib.Path('.').resolve()
    sh = sh @ cwd
    proc = sh> sh.pwd
    assert(proc.stdout == f'{cwd}\n'.encode())

def test_command_env(sh):
    proc = sh> sh.env.env({'foo': 'bar'}) | sh.grep('foo')
    assert(proc.stdout == b'foo=bar\n')

def test_command_env_op(sh):
    proc = sh> sh.env % {'foo': 'bar'} | sh.grep('foo')
    assert(proc.stdout == b'foo=bar\n')

def test_command_cwd(sh):
    cwd = pathlib.Path('.').resolve().parent
    proc = sh> sh.pwd.cwd(cwd)
    assert(proc.stdout == f'{cwd}\n'.encode())

def test_command_cwd_op(sh):
    cwd = pathlib.Path('.').resolve().parent
    proc = sh> sh.pwd @ cwd
    assert(proc.stdout == f'{cwd}\n'.encode())

def test_command_cwd_chain(sh):
    cwd = pathlib.Path('.').resolve().parent
    proc = sh> sh.pwd.cwd('/does/not/exist').cwd(cwd)
    assert(proc.stdout == f'{cwd}\n'.encode())

def test_stdout_file(sh):
    with named_temp_file() as (file, path):
        sh.echo('hello') > file
        # Input files should be closed.
        # Output files do not need to be.
        assert(not file.closed)
        assert(path.read_bytes() == b'hello\n')

def test_stdout_path(sh):
    with named_temp_file() as (file, path):
        file.close()
        sh.echo('hello') > path
        assert(path.read_bytes() == b'hello\n')

def test_stdout_str(sh):
    with named_temp_file() as (file, path):
        file.close()
        sh.echo('hello') > str(path)
        assert(path.read_bytes() == b'hello\n')

def test_stdout_bytes(sh):
    with named_temp_file() as (file, path):
        file.close()
        sh.echo('hello') > bytes(path)
        assert(path.read_bytes() == b'hello\n')

def test_stdout_nowhere(sh):
    proc = sh.echo('hello') > sh.nowhere
    assert(proc.stdout is None)

def test_join(sh):
    proc = sh> sh.python(c='import sys; sys.stderr.write("hello")').join()
    assert(proc.stdout == b'hello')

def test_command_path(sh):
    proc = sh> sh['/bin/echo']('hello')
    assert(proc.stdout == b'hello\n')
