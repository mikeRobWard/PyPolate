from setuptools import setup, find_packages

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
    'Programming Language :: Python :: 3',
    'Topic :: Scientific/Engineering :: GIS'
]

setup(
    name ='pypolate',
    version = '0.0.1',
    description = 'A package for performing spatial interpolation with vector data',
    long_description=open('README.md').read() + '\n\n' + open('CHANGELOG.txt').read(),
    long_description_content_type = "text/markdown/html",
    url = 'https://github.com/mikeRobWard/PyPolate',
    author = 'Michael Ward & John Fitzgibbons',
    author_email='michaelward94@gmail.com',
    license='GPLv3+',
    classifiers=classifiers,
    keywords='spatial interpolation',
    packages=find_packages(),
    install_requires=['geopandas', 'pandas'],
    python_requires=">=3.7"
)