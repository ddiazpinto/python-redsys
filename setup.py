import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='redsys',
    version='0.2.7',
    packages=find_packages(),
    include_package_data=True,
    license='MIT License',
    description='A simple, clean and less dependant client for handle payments through RedSys.',
    long_description=README,
    url='https://github.com/ddiazpinto/python-redsys',
    author='David D&iacute;az',
    author_email='d.diazp@gmail.com',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
