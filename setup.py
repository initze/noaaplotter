from distutils.core import setup

setup(
    name='noaaplotter',
    version='0.2.0',
    packages=['noaaplotter'],
    url='https://github.com/initze/noaaplotter',
    license='',
    author='Ingmar Nitze',
    author_email='ingmar.nitze@awi.de',
    description='Package to plot fancy climate/weather data of NOAA',
    install_requires=['pandas', 
                      'numpy', 
                      'matplotlib', 
                      'requests',
                      'joblib',
                      'tqdm'],
    scripts=['plot_daily.py', 'plot_monthly.py', 'download_data.py']
)
