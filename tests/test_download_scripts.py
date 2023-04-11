import unittest
from pathlib import Path
import os


class MyTestCase(unittest.TestCase):

    def test_00_download_script_noaa(self):
        output_file = Path('test_kotzebue_download_script.csv')
        start_date = '2020-01-01'
        end_date = '2023-12-31'
        station_id = 'USW00026616'
        token = 'LaVQzwUgOBQLBRwoTpOLyRbIKDTHAVVe'

        for n_jobs in [1, 2, 4]:
            if output_file.exists():
                os.remove(output_file)
            s_dl = f'download_data.py -o {output_file} -t {token} -sid {station_id} -start {start_date} \
            -end {end_date} -n_jobs {n_jobs} '
            os.system(s_dl)
            if not os.path.exists(output_file):
                s_dl = f'python ../scripts/download_data.py -o {output_file} -t {token} -sid {station_id} \
                -start {start_date} -end {end_date} -n_jobs {n_jobs}'
                os.system(s_dl)
            exists = os.path.exists(output_file)
            self.assertTrue(exists)

            #cleanup
            if output_file.exists():
                os.remove(output_file)


if __name__ == '__main__':
    unittest.main()
