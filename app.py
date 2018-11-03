from typing import Any, Dict, List, Optional

from dash.dependencies import Input, Output, State
from textwrap import dedent

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
import settings.dev as settings


class VisualApp:

	def __init__(self) -> None:
		self._dataframe = self._load_data()
		self._quants: Dict[str, int] = self._get_quants_winnings()
		self._app = dash.Dash(__name__)
		self._init_app()
		self._init_app_content()


	def run(self) -> None:
		self._app.run_server(debug=True)


	def _load_data(self) -> pd.DataFrame:
		return pd.read_csv('aggregate.csv').set_index(['name', 'date']).sort_index()


	def _get_quants_winnings(self) -> Dict[str, int]:
		'''
		Calculates the most profitable quants and outputs them in form of a dictionary sorted in a descending order.
		Also calls a method which adds new column into the :attr:`self._dataframe` dataframe.
		:return:
		'''
		daily_winnings = {(x + 1): y for x, y in enumerate(range(50, 0, -5))}
		rankings = self._dataframe.loc[:, 'rank']
		rankings.loc[rankings > 10] = 0
		winnings = rankings.replace(daily_winnings)
		self._add_cumulative_sum(winnings = winnings)
		quants_with_money = winnings.groupby(winnings.index.get_level_values('name')).sum().sort_values(ascending = False)
		return quants_with_money.to_dict()


	def _add_cumulative_sum(self, winnings: pd.DataFrame) -> None:
		'''
		Transforms the rankings into a new column with cumulative winnings
		'''
		winnings = winnings.to_frame() \
			.reset_index()
		winnings.loc[winnings['rank'] == 0, 'rank'] = None
		winnings = pd.pivot_table(winnings, 'rank', 'name', 'date') \
			.cumsum(axis = 1) \
			.fillna(axis= 1, method = 'ffill') \
			.stack() \
			.to_frame() \
			.rename(columns = {0: 'cumsum_winnings'})

		self._dataframe = self._dataframe.merge(winnings, how = 'outer', left_index = True, right_index = True)
		self._dataframe.reset_index('name', inplace = True)

	@staticmethod
	def _beautify_column_name(column: str) -> str:
		return column.capitalize().replace('_', ' ')


	def _get_dataframe_columns(self) -> List[Dict[str, str]]:
		return [
			{'label': self._beautify_column_name(column), 'value': column}
			for column in sorted(self._dataframe.columns, reverse = True)
			if column not in settings.OMITTED_COLUMNS
		]


	def _generate_traces(self, column: str, selected_quants: Optional[List[str]]) -> List[Any]:
		traces = []
		dataframe = self._dataframe
		for nickname in dataframe['name'].unique():
			if nickname in selected_quants:
				quant = dataframe[dataframe['name'] == nickname]
				traces.append(go.Scatter(
					x = quant.index.tolist(),
					y = quant[column].values.tolist(),
					name = nickname
				))
		return traces


	def _generate_figure(self, column: Optional[str], selected_quants: Optional[List[str]]) -> Dict[str, Any]:
		traces = []
		if column is not None:
			traces = self._generate_traces(column, selected_quants = selected_quants)
		reverse_y_axis = 'reversed' if column in settings.COLUMNS_WITH_REVERSED_Y_AXIS else True
		return {
			'data': traces,
			'layout': {
				'height': 700,
				'title': self._beautify_column_name(column),
				'yaxis': {'autorange': reverse_y_axis, 'side': 'right'},
			}
		}


	def _init_app_content(self) -> dash.Dash:

		self._app.layout = html.Div(children = [
			self._init_app_description(),
			self._init_app_settings(),
			dcc.Tabs(id="tabs", children = [
				dcc.Tab(label='Historical plots', children = [
					html.Div(children = [dcc.Graph(id='main')], className= 'container-fluid')
				]),
				dcc.Tab(label='Statistics', children = [
					html.Div(
						dcc.Markdown(dedent('''
							### Statistics
							Other statistics and analysis will be added in the future.
							You can submit a Pull Request on [Github](https://github.com/OskarGottlieb/) if you feel
							like contributing to this project.
						''')),
					className='container')
				])
			], className='container')
		])

		@self._app.callback(
			Output('main', 'figure'),
			[Input('dropdown_column', 'value'), Input('slider_rankings', 'value'), Input('dropdown_quants', 'value')],
			[State('radio_select_quants', 'value')]
		)
		def generate_figure_of_selected_column(
				column_name: Optional[str],
				slider_rankings: Optional[List[int]],
				dropdown_quants: Optional[List[str]],
				radio_select_quants_value: str
		):
			'''

			:param column_name: Column from the aggregated csv file
			:param ranked_quants:
			:return:
			'''
			if radio_select_quants_value == 'rank':
				first_quant, last_quant = slider_rankings
				selected_quants = list(self._quants.keys())[first_quant:last_quant]
			else:
				selected_quants = dropdown_quants
			return self._generate_figure(column = column_name, selected_quants = selected_quants)

		@self._app.callback(
			Output('slider_rankings', 'disabled'),
			[Input('radio_select_quants', 'value')])
		def toggle_selection_of_quants_by_slider(radio_quant_select_value: str):
			return radio_quant_select_value == 'name'

		@self._app.callback(
			Output('dropdown_quants', 'disabled'),
			[Input('radio_select_quants', 'value')])
		def toggle_selection_of_quants_by_nickname(radio_quant_select_value: str):
			return radio_quant_select_value == 'rank'

		@self._app.callback(
			Output('dropdown_quants', 'value'),
			[Input('slider_rankings', 'value')],
			[State('radio_select_quants', 'value')])
		def toggle_selection_of_quants_by_nickname(slider_rankings: Optional[List[int]], radio_select_quants_value: str):
			if radio_select_quants_value == 'rank':
				first_quant, last_quant = slider_rankings
				return list(self._quants.keys())[first_quant:last_quant]


	def _init_app_description(self) -> html.Div:
		'''

		'''
		return html.Div(children = [
			dcc.Markdown(dedent('''
			     # Quantopian Contest Analytics
			     [Quantopian](https://www.quantopian.com) is a crowd-sourced hedge-fund which organizes a daily trading
			     contest. Anyone can submit an algorithm in order to compete for daily prize pool or eventually get money
			     allocated to his or her algorithm.
			     
			     This website was created as a way to visualize the statistics related to quant's strategies which
			     Quantopian outputs. In the future I'd like to add ad-hoc analysis, such as clustering strategies
			     based on their characteristics (leverage, exposure to various factors, etc..). Feel free to play around
			     with it, the code is freely available on my [Github](https://github.com/OskarGottlieb/) profile.
			     
			     The application is written almost entirely in [Dash](https://github.com/plotly/dash). This allows
			     you to play around interactively with the plots - you can zoom in/out, make and download a screenshot, etc..
			'''))
		], className='container')

	def _init_app_settings(self) -> html.Div:
		return html.Div(id='', children=[
			html.Hr(),
			dcc.Markdown(dedent('''
				## Settings
				Below you can select the quants to display either by their sorted cumulative contest winnings or you can
				handpick them from the dropdown menu. So far the application only supports plotting values of the various
				time series which Quantopian outputs. You can select the time series to be plotted from the drop down
				menu as well.
			''')),
			html.Div(children = [
				html.Div(children= [
					dcc.Markdown(dedent('''
						### Select Quants:
					''')),
					dcc.RadioItems(
						id='radio_select_quants',
						options=[
							{'label': 'By cumulative winnings', 'value': 'rank'},
							{'label': 'By nicknames', 'value': 'name'}
						],
						value='rank',
					)
				], className='col-md-3 col-sm-3, col-xs-12'),
				html.Div(children=[
					dcc.Markdown(dedent('''
						#### Quants by cumulative winnings:
					''')),
					dcc.RangeSlider(
						id='slider_rankings',
						min=1,
						max=len(self._quants),
						marks={q: q for q in range(1, len(self._quants), 10)},
						step=1,
						value=[1, 10],
					),
				], className='col-md-9 col-sm-9, col-xs-12'),
				html.Div(children=[
					dcc.Markdown(dedent('''
						### Value to plot:
					''')),
					dcc.Dropdown(
						id='dropdown_column',
						options = self._get_dataframe_columns(),
						value='cumsum_winnings'
					),
				], className='col-md-3 col-sm-3, col-xs-12'),
				html.Div(children=[
					dcc.Markdown(dedent('''
						#### Quants by nicknames:
					''')),
					dcc.Dropdown(
						id='dropdown_quants',
						options=[{'label': quant, 'value': quant} for quant in sorted(self._quants.keys())],
						value=list(self._quants.keys())[:10],
						multi=True,
					),
				], className='col-md-9 col-sm-9, col-xs-12'),
			], className = 'row'),
			html.Hr(),
		], className = 'container')

	def _init_app(self) -> None:
		self._app = dash.Dash(
			__name__,
			external_scripts = [{
				'src': 'https://cdnjs.cloudflare.com/ajax/libs/lodash.js/4.17.10/lodash.core.js',
				'integrity': 'sha256-Qqd/EfdABZUcAxjOkMi8eGEivtdTkh3b65xCZL4qAQA=',
				'crossorigin': 'anonymous'
			}],
			external_stylesheets = [{
				'href': 'https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css',
				'rel': 'stylesheet',
				'integrity': 'sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO',
				'crossorigin': 'anonymous'
			}]
		)


if __name__ == '__main__':
	app = VisualApp()
	app.run()
