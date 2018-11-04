from dateutil.rrule import DAILY, rrule, MO, TU, WE, TH, FR
import datetime
import os
import sys

import pandas as pd
import requests



BASE_URL = 'https://www.quantopian.com/contest/download_results?date='
START_DATE = '20180101'
END_DATE = '20181031'



def get_date_range(start_date: str, end_date: str) -> rrule:
	start_date = datetime.datetime.strptime(start_date, '%Y%m%d').date()
	end_date = datetime.datetime.strptime(end_date, '%Y%m%d').date()
	return rrule(DAILY, dtstart=start_date, until=end_date, byweekday=(MO,TU,WE,TH,FR))


def download_data(sequential_errors_count: int = 20) -> None:
	errors_count = 0
	headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'}
	dates = get_date_range(START_DATE, END_DATE)
	for date in sorted(dates, reverse = True):
		date = date.strftime('%Y-%m-%d')
		file_name = f'data/{date}.csv'
		if os.path.isfile(file_name):
			continue
		if errors_count == sequential_errors_count:
			print('Too many days have broken data.')
			break
		
		url = BASE_URL + date
		r = requests.get(url, headers = headers)
		if r.status_code == 200:
			with open(file_name, 'w+') as f:
				f.writelines(r.content.decode('utf-8'))
			print(f'Day {date} downloaded succesfully.')
			errors_count = 0
		else:
			print(f'Can\'t download url {url}')
			errors_count += 1


def aggregate_data() -> None:
	try:
		os.remove('aggregate.csv')
	except:
		pass
	files = os.listdir('data')
	csv_files = [f for f in files if f.endswith('.csv')]
	list_dataframes = []
	for csv_file in csv_files:
		dataframe = pd.read_csv(os.path.join('data', csv_file))
		dataframe['date'] = csv_file[:10]
		list_dataframes.append(dataframe)

	results = pd.concat(list_dataframes)
	results.to_csv('aggregate.csv', index = False)


if __name__ == '__main__':
	if len(sys.argv) == 2:
		method = sys.argv[1]
		if method == 'aggregate':
			aggregate_data()
		elif method == 'download':
			download_data()
		else:
			raise AssertionError(f'{method} is not a valid method.')
	else:
		raise AssertionError(f'Need to specify a valid method.')
