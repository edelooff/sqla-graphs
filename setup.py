import os
from setuptools import setup, find_packages


def contents(filename):
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, filename)) as fp:
        return fp.read()


setup(
    name='sqla-graphs',
    version='0.1',
    author='Elmer de Looff',
    author_email='elmer.delooff@gmail.com',
    description='Graphviz generators for SQLAlchemy models or databeses.',
    long_description=contents('README.rst'),
    url='https://github.com/edelooff/sqla-graphs',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Topic :: Database :: Front-Ends'],
    packages=find_packages(),
    install_requires=[
        'pydot>=1.2.2',
        'sqlalchemy>=1.0'],
    zip_safe=False,
)
