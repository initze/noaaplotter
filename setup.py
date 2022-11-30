from distutils.core import setup

setup(
    name='noaaplotter',
    version='0.3.1',
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
    scripts=['plot_daily.py', 'plot_monthly.py', 'download_data.py', 'download_data_ERA5.py']
)
