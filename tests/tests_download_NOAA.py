import unittest
from noaaplotter.download_utils import download_from_noaa
import os
from pathlib import Path
import pandas as pd

class DownloadTest(unittest.TestCase):
    def test_download(self):
        output_file = Path('test_kotzebue.csv')

        start_date= '2020-01-01'
        end_date = '2023-12-31'
        station_id = 'USW00026616'
        token = 'LaVQzwUgOBQLBRwoTpOLyRbIKDTHAVVe'
        datatypes = ['TMIN', 'TMAX', 'PRCP', 'SNOW']

        for n_jobs in [1,2,4]:
            if output_file.exists():
                os.remove(output_file)
            download_from_noaa(output_file, start_date, end_date, datatypes, '', station_id, token, n_jobs=n_jobs)
            exists = os.path.exists(output_file)
            self.assertTrue(exists)

    def test_read_csv(self):
        output_file = Path('test_kotzebue.csv')
        df = pd.read_csv(output_file)
        self.assertTrue(isinstance(df, pd.DataFrame))



if __name__ == '__main__':
    unittest.main()
