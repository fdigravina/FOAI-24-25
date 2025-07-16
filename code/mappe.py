import csv
import folium
import subprocess
import pickle

from geopy.geocoders import Nominatim

class tsp_bb_agent:
	
	def __init__(self, graph, filename, out_file, original_to_prolog, prolog_to_original):
		self.graph = graph
		self.filename = filename
		self.out_file = out_file
		self.original_to_prolog = original_to_prolog
		self.prolog_to_original = prolog_to_original
	
	
	def run_prolog(self):
		if self.filename == 'code/input_pure.txt':
			#print ('Running pure version')
			result = subprocess.run(
				['swipl', '-g', 'main', '-t', 'halt', 'code/tsp_bb_pure.pl'],
				capture_output=False,
				text=True,
				timeout=300
			)
		else:
			#print ('Running weighted version')
			result = subprocess.run(
				['swipl', '-g', 'main', '-t', 'halt', 'code/tsp_bb.pl'],
				capture_output=False,
				text=True,
				timeout=300
			)
		
		return result.stdout
	
	def returnPath(self):
		_ = self.run_prolog()
		
		with open(self.out_file, 'r') as f:
			lines = f.readlines()
			
			best_path = None
			best_cost = None
			
			for line in lines:
				line = line.strip()
				if line.startswith('BEST_PATH:'):
					path_str = line.replace('BEST_PATH: ', '')
					path_str = path_str.strip('[]')
					if path_str:
						prolog_path = [int(x.strip()) for x in path_str.split(',')]
						best_path = [self.prolog_to_original[n] for n in prolog_path]
					else:
						best_path = []
				elif line.startswith('BEST_COST:'):
					cost_str = line.replace('BEST_COST: ', '')
					best_cost = int(cost_str)
			
			print(f"Percorso migliore trovato: {best_path}")
			print(f"Costo: {best_cost}\n\n\n")
			
			return best_path
		


with open("code/graph_data.pkl", "rb") as f:
    G, GPure, diz1, diz2, original_to_prolog, prolog_to_original = pickle.load(f)

#print(prolog_to_original, original_to_prolog)

agente_tsp_bb = tsp_bb_agent (graph=GPure, filename='code/input_pure.txt', out_file='code/tsp_results_pure.txt', original_to_prolog=original_to_prolog, prolog_to_original=prolog_to_original)
path = agente_tsp_bb.returnPath()

agente_tsp_bb = tsp_bb_agent (graph=G, filename='code/input.txt', out_file='code/tsp_results.txt', original_to_prolog=original_to_prolog, prolog_to_original=prolog_to_original)
path2 = agente_tsp_bb.returnPath()

citta2 = []
citta1 = []

#print(path)
#print (path2)

for p in path:
	citta1.append(diz1[p])
for p in path2:
	citta2.append(diz1[p])

for citta in [citta1,citta2]:
	geolocator = Nominatim(user_agent="city_route")
	mappa = folium.Map(location=None, zoom_start=6)

	coordinate = []
	lista = []

	with open ('code/comuni.csv', 'r', encoding='utf-8') as f:
		reader = csv.reader(f)
		for row in reader:
			lista.append((row[0], row[1], row[2]))
	if citta == citta2:
		for p in path2:
			for r in lista:
				if r[0] == diz1[p]:
					coordinate.append((float(r[1]), float(r[2])))
	else:
		for p in path:
			for r in lista:
				if r[0] == diz1[p]:
					coordinate.append((float(r[1]), float(r[2])))
					#print (r[0])
					
	if citta == citta2:
		folium.PolyLine(locations=coordinate, color='blue', weight=5).add_to(mappa)
	else:
		folium.PolyLine(locations=coordinate, color='red', weight=5).add_to(mappa)
	for i in range(len(coordinate)):
		folium.Marker(coordinate[i], popup=citta[i]).add_to(mappa)

	folium.Marker(coordinate[0], popup=citta[0]).add_to(mappa)

	mappa.fit_bounds([[36.6, 6.2], [47.0, 19.0]])
	if citta == citta1:
		mappa.save('code/city_route_map_pure.html')
	elif citta == citta2 or citta1 == citta2:
		mappa.save('code/city_route_map_with_weight.html')