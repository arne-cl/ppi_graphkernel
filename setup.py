# -*- coding: utf-8 -*-

# This is your "setup.py" file.
# See the following sites for general guide to Python packaging:
#   * `The Hitchhiker's Guide to Packaging <http://guide.python-distribute.org/>`_
#   * `Python Project Howto <http://infinitemonkeycorps.net/docs/pph/>`_

from setuptools import setup, find_packages
import sys, os

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README')).read()
#NEWS = open(os.path.join(here, 'NEWS.rst')).read()


version = '1.0.0'

install_requires = [
    # List your project dependencies here.
    # For more details, see:
    # http://packages.python.org/distribute/setuptools.html#declaring-dependencies
    "enum", "numpy"
]


setup(name='ppi_graphkernel',
    version=version,
    description="all-dependency-paths graph kernel for protein-protein interaction extraction",
    long_description=README + '\n\n',
    # Get classifiers from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    # classifiers=[c.strip() for c in """
    #     Development Status :: 4 - Beta
    #     License :: OSI Approved :: MIT License
    #     Operating System :: OS Independent
    #     Programming Language :: Python :: 2.6
    #     Programming Language :: Python :: 2.7
    #     Programming Language :: Python :: 3
    #     Topic :: Software Development :: Libraries :: Python Modules
    #     """.split('\n') if c.strip()],
    # ],
    keywords='graph kernel bionlp ppi',
    author='Antti Airola, Sampo Pyysalo, Jari Björne, Tapio Pahikkala, Filip Ginter and Tapio Salakoski',
    author_email='',
    url='',
    license='GPL v3',
    packages=find_packages("src"),
    package_dir = {'': "src"},include_package_data=True,
    zip_safe=False,
    install_requires=install_requires
#    entry_points={
#       'console_scripts':
#            ['discoursegraphs=discoursegraphs:main']
#    }
)
