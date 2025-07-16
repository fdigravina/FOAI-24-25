import pickle
import random
import csv
import networkx as nx
import matplotlib.pyplot as plt
import folium
import geopandas as gpd
import numpy as np
import warnings
import subprocess

from geopy.geocoders import Nominatim
from shapely.geometry import LineString, Polygon

warnings.simplefilter(action='ignore', category=FutureWarning)

def confini():
	
	italy = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
	italy = italy[italy.name == 'Italy']

	#italy = italy[~italy.name.isin(['Sicily', 'Sardinia'])]

	italy_polygon = italy.explode()
	
	coordinate_lista = []

	# Itera attraverso i poligoni all'interno di italy_polygon
	for poligono in italy_polygon.geometry:
		# Ottieni le coordinate del poligono e aggiungile alla lista
		coordinate_poligono = list(poligono.exterior.coords)
		coordinate_lista.append(coordinate_poligono)
	
	# Separate the x and y coordinates
	x_coords = [coord[0] for coord in coordinate_lista[0]]
	y_coords = [coord[1] for coord in coordinate_lista[0]]
	

	plt.plot(x_coords, y_coords, marker='o', linestyle='-', color='b')

	plt.xlabel('X-axis')
	plt.ylabel('Y-axis')
	plt.title('Plot of Coordinates')

	plt.grid(True)
	plt.show()

	
	#print(coordinate_lista[0])
	return coordinate_lista[0]

def is_segment_within_polygon(segment, polygon_coords):
	polygon = Polygon(polygon_coords)
	segment_line = LineString(segment)
	
	'''
	print (polygon_coords)
	print (segment_line)
	xs, ys = zip(*polygon_coords)
	plt.figure()
	plt.plot(xs,ys) 
	plt.show()
	'''
	
	#print (polygon, segment_line)
	#print (segment_line.intersects(polygon.boundary))
	return not segment_line.intersects(polygon.boundary)


def create_limited_graph(min_nodes=5, max_nodes=20):
	
	comuni = []
	with open('code/nomi.csv', 'r', encoding='utf-8') as file:
		reader = csv.reader(file)
		for row in reader:
			comuni.append((int(row[0]), row[1]))
	
	num_nodes = random.randint(min_nodes, max_nodes)
	comuni_selezionati = random.sample(comuni, num_nodes)
	selected_ids = set(comune[0] for comune in comuni_selezionati)
	
	G_full, GPure_full, diz1_full, diz2_full = readGraph()
	
	G = G_full.subgraph(selected_ids).copy()
	GPure = GPure_full.subgraph(selected_ids).copy()
	
	diz1 = {k: v for k, v in diz1_full.items() if k in selected_ids}
	diz2 = {k: v for k, v in diz2_full.items() if v in selected_ids}
	
	id_originali = list(G.nodes())
	original_to_prolog = {id_originali[i]: i + 1 for i in range(len(id_originali))}
	prolog_to_original = {v: k for k, v in original_to_prolog.items()}
	
	return G, GPure, diz1, diz2, original_to_prolog, prolog_to_original


def readGraph ():
	
	G = nx.Graph()
	diz1 = {}
	diz2 = {}
	
	with open('code/nomi.csv', 'r', encoding='utf-8') as file:
		reader = csv.reader(file)
		for row in reader:
			id_val = int(row[0])
			nome = row[1]
			diz1[id_val] = nome
			diz2[nome] = id_val
			G.add_node(id_val)
	
	lista = {}
	with open ('code/comuni.csv', 'r', encoding='utf-8') as f:
		reader = csv.reader(f)
		for row in reader:
			lista[row[0]] = (row[1], row[2])  # nome, lat, lon
	
	with open ('code/dataset.csv', 'r', encoding='utf-8') as f:
		ita = confini()
		reader = csv.reader(f)
		for row in reader:
			if row[0] != row[1]:
					seg = [(float(lista[row[0]][1]), float(lista[row[0]][0])), (float(lista[row[1]][1]), float(lista[row[1]][0]))]
					w = float(row[2])
					if is_segment_within_polygon(seg, ita):
						G.add_edge(diz2[row[0]], diz2[row[1]], weight=w)
					else:
						G.add_edge(diz2[row[0]], diz2[row[1]], weight=w*1.5) # uso barca
	
	n = G.number_of_nodes()
	
	listaMeteo = np.zeros(n)
	
	with open('code/predizione.txt', 'r') as f:
		righe = f.readlines()
		for riga in righe:
			line = riga[18:]
			nodo, meteo = line.strip().split(': ')
			meteoNum = 0
			if meteo == 'pioggia_lieve':
				meteoNum = 1
			if meteo == 'pioggia_media':
				meteoNum = 2
			if meteo == 'pioggia_forte':
				meteoNum = 3
			listaMeteo[int(nodo)] = meteoNum
	
	with open ('code/predici.pl', 'r') as f:
		righe = f.readlines()
		for riga in righe:
			if riga.startswith('situazione'):
				nodo, meteo = riga.strip().split(", ")[0][11:], riga.strip().split(", ")[1][:-2]
				meteoNum = 0
				if meteo == 'pioggia_lieve':
					meteoNum = 1
				if meteo == 'pioggia_media':
					meteoNum = 2
				if meteo == 'pioggia_forte':
					meteoNum = 3
				listaMeteo[int(nodo)] = meteoNum
	
	GPure = G.copy()
	
	dissestata = random.choices(population=[0, 1, 2, 3], weights=[0.7, 0.15, 0.1, 0.05], k=n**2)    # condizioni normali, quasi normali, dissestata, quasi inagibile
	lavori_in_corso = random.choices (population=[0, 1], weights=[0.95, 0.05], k=n**2)
	
	for i in G.nodes:
		for j in G.nodes:
			
			if i == j:
				continue
			
			if G[i][j]['weight'] == 2 ** 30:
				continue
			
			dissestamento = max(dissestata[i], dissestata[j])
			lavori = max (lavori_in_corso[i], lavori_in_corso[j])
			meteo = max (listaMeteo[i], listaMeteo[j])
			
			#print (G[i][j]['weight'], type(G[i][j]['weight']))
			
			if dissestamento == 1:
				G[i][j]['weight'] = float(G[i][j]['weight']) * 1.1
			
			if dissestamento == 2:
				G[i][j]['weight'] = float(G[i][j]['weight']) * 1.2
			
			if dissestamento == 3:
				G[i][j]['weight'] = float(G[i][j]['weight']) * 1.4
			
			if lavori == 1:
				G[i][j]['weight'] = float(G[i][j]['weight']) * 1.5
			
			if meteo == 1:
				G[i][j]['weight'] = float(G[i][j]['weight']) * 1.1
			
			if meteo == 2:
				G[i][j]['weight'] = float(G[i][j]['weight']) * 1.2
			
			if meteo == 3:
				G[i][j]['weight'] = float(G[i][j]['weight']) * 1.3
			
			G[i][j]['weight'] = int(G[i][j]['weight'])
			GPure[i][j]['weight'] = int(GPure[i][j]['weight'])
		
	return G, GPure, diz1, diz2


class graph_file:
	
	def __init__(self, filename, graph, original_to_prolog, prolog_to_original):
		self.graph = graph
		self.filename = filename
		self.original_to_prolog = original_to_prolog
		self.prolog_to_original = prolog_to_original
		self.create_input_file()
	
	def create_input_file(self):
		with open(self.filename, 'w') as f:
			f.write(f"bound({50000}).\n")	# bound iniziale
			
			for node1 in self.graph.nodes():
				for node2 in self.graph.nodes():
					if node1 != node2 and self.graph.has_edge(node1, node2):
						weight = self.graph[node1][node2]['weight']
						id1 = self.original_to_prolog[node1]
						id2 = self.original_to_prolog[node2]
						f.write(f"edge({id1}, {id2}, {weight}).\n")
						f.write(f"edge({id2}, {id1}, {weight}).\n")
		

G, GPure, diz1, diz2, original_to_prolog, prolog_to_original = create_limited_graph(min_nodes=8, max_nodes=12)

G_file = graph_file (graph=GPure, filename='code/input_pure.txt', original_to_prolog=original_to_prolog, prolog_to_original=prolog_to_original)
G_file = graph_file (graph=G, filename='code/input.txt', original_to_prolog=original_to_prolog, prolog_to_original=prolog_to_original)

with open("code/graph_data.pkl", "wb") as f:
    pickle.dump((G, GPure, diz1, diz2, original_to_prolog, prolog_to_original), f)