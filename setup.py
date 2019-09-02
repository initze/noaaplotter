from distutils.core import setup

setup(
    name='noaaplotter',
    version='0.1.0',
    packages=['noaaplotter'],
    url='https://github.com/initze/noaaplotter',
    license='',
    author='initze',
    author_email='ingmar.nitze@awi.de',
    description='Package to plot fancy climate/weather data of NOAA',
    install_requires=['pandas', 'numpy', 'seaborn', 'matplotlib']
)
