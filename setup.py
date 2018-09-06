from setuptools import setup, find_packages
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='Lucky CAT',
    version='0.1',
    license='GPL3',
    author='Thomas Barabosch',
    author_email='thomas.barabosch@fkie.fraunhofer.de',
    url='https://github.com/fkie-cad/luckycat',
    packages=find_packages(),
    package_data={'luckycat': ['luckycat/logging.conf']},
    scripts=['luckycat/frontend/luckycat_frontend.py',
             'luckycat/backend/luckycat_backend.py'],
    long_description=long_description,
    long_description_content_type='text/markdown'
)
