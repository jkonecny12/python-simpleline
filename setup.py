#!/usr/bin/python3

from distutils.core import setup

setup(name='simpleline', version='0.2',
      description='Python text UI framework',
      author='Jiri Konecny', author_email='jkonecny@redhat.com',
      url='http://git.fedoraproject.org/git/?p=python-simpleline.git',
      packages=['simpleline', 'simpleline.render', 'simpleline.render.screen', 'simpleline.event_loop', 'simpleline.utils'])
