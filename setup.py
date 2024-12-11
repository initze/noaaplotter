from distutils.core import setup

setup(
    name='noaaplotter',
    version='0.5.2',
    packages=['noaaplotter'],
    url='https://github.com/initze/noaaplotter',
    license='',
    author='Ingmar Nitze',
    author_email='ingmar.nitze@awi.de',
    description='Package to plot fancy climate/weather data of NOAA',
    install_requires=[
        'pandas>=2.2', 
        'numpy>=2.2', 
        'matplotlib>=3.9', 
        'requests', 
        'joblib>=1.4', 
        'tqdm>=4.67', 
        'geemap>=0.35'
    ],
    scripts=[
        'scripts/plot_daily.py', 
        'scripts/plot_monthly.py', 
        'scripts/download_data.py', 
        'scripts/download_data_ERA5.py'
    ]
)
