import shush
from shush.pytest import cap, forgive

sh = shush.Shell()

def test_example(cap):
    sh> sh.echo('foofoo')
    with forgive(cap.out.matches('ofo')):
        sh> sh.ls('barbar')
    with forgive(cap.err.matches('zba')):
        sh> sh.ls('bazbaz')
