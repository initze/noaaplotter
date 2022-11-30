from distutils.core import setup

setup(
    name='noaaplotter',
    version='0.4.0',
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
                      'tqdm',
                      'earthengine-api',
                      'geemap'],
    scripts=['scripts/plot_daily.py', 'scripts/plot_monthly.py', 'scripts/download_data.py', 'scripts/download_data_ERA5.py']
)
