from typing import Any, Dict, List, Optional

from dash.dependencies import Input, Output
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go



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
		return pd.read_csv('aggregate.csv').set_index(['date']).sort_index()


	def _get_quants_winnings(self) -> Dict[str, int]:
		winnings = {(x + 1): y for x, y in enumerate(range(50, 0, -5))}
		ranks = self._dataframe.set_index('name').loc[:, 'rank']
		ranks.loc[ranks > 10] = 0
		quants_with_money = ranks.replace(winnings).groupby(ranks.index).sum().sort_values(ascending = False)
		return quants_with_money.to_dict()

	@staticmethod
	def _beautify_column_name(column: str) -> str:
		return column.capitalize().replace('_', ' ')


	def _get_dataframe_columns(self) -> List[Dict[str, str]]:
		return [
			{'label': self._beautify_column_name(column), 'value': column}
			for column in self._dataframe.columns
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
		return {
			'data': traces,
			'layout': {
				'height': '800px',
				'yaxis': {'autorange': 'reversed', 'range': [0, 10]}
			}
		}


	def _init_app_content(self) -> dash.Dash:
		self._app.layout = html.Div(
				children=[
		            html.H1(children='Hello Dash'),

			dcc.Tabs(id="tabs", children=[
				dcc.Tab(label='Historical plots', children=[
					html.Div(id='', children=[
				         dcc.Dropdown(
					         id='quants',
					         options=[{'label': quant, 'value': quant} for quant in self._quants.keys()],
					         value=list(self._quants.keys())[:10],
					         multi=True,
				         ),
				         dcc.Dropdown(
					         id='column-select',
					         options=self._get_dataframe_columns(),
					         value='rank'
				         ),
			        ]),
					dcc.Graph(id='main')
				]),
				dcc.Tab(label='Statistics', children=[
					html.Div('lol', 'kek')
				])

			]),
		], className='container')

		@self._app.callback(
			Output('main', 'figure'),
			[Input('column-select', 'value'), Input('quants', 'value')])
		def generate_figure_of_selected_column(column_name: Optional[str], selected_quants: Optional[List[str]]):
			return self._generate_figure(column = column_name, selected_quants = selected_quants)


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
