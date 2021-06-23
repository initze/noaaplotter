from distutils.core import setup

setup(
    name='noaaplotter',
    version='0.2.0dev',
    packages=['noaaplotter'],
    url='https://github.com/initze/noaaplotter',
    license='',
    author='Ingmar Nitze',
    author_email='ingmar.nitze@awi.de',
    description='Package to plot fancy climate/weather data of NOAA',
    install_requires=['pandas>=0.25.3', 'numpy>=1.17.4', 'matplotlib>=3.1.1'],
    scripts=['plot_daily.py', 'plot_monthly.py']
)
