#!/usr/bin/python3
from setuptools import setup, find_packages
import shutil

with open('README.md') as f:
    long_description = f.read()
shutil.copyfile('icat/__main__.py', 'icat/icat')

setup(
    name='icat',
    version='0.0.39',
    license='GPL3',
    url='https://github.com/gretchycat/icat',
    author='Gretchen Maculo',
    author_email='gretchen.maculo@gmail.com',
    description='print images on an ansi capable terminal',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=[
        'Pillow',
    ],
    tests_require=[
    ],
    scripts=['icat/icat']
)
