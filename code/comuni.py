import pandas as pd
import numpy as np
import random

import math

def haversine(lat1, lon1, lat2, lon2):
	
	R = 6371.0
	
	lat1 = math.radians(lat1)
	lon1 = math.radians(lon1)
	lat2 = math.radians(lat2)
	lon2 = math.radians(lon2)
	
	dlat = lat2 - lat1
	dlon = lon2 - lon1
	
	a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
	c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
	distance = R * c
	
	return distance


def converti (situazione):
	if situazione == 0:
		return 'sole'
	if situazione == 1:
		return 'pioggia_lieve'
	if situazione == 2:
		return 'pioggia_media'
	return 'pioggia_forte'


df = pd.read_csv ('data/comuni_completo.csv')


nomiS = df['nome'].to_numpy()
latS = df['lat'].to_numpy(dtype=float)
lonS = df['lon'].to_numpy(dtype=float)

cities = []

with open('data/cities.txt', 'r', encoding='utf-8') as f:
	content = f.read()
	cities = eval(content)


nomi = []
lat = []
lon = []

for idx in range(len(nomiS)):
	if nomiS[idx] in cities:
		if random.random() < 0.5:
			nomi.append(nomiS[idx])
			lat.append(latS[idx])
			lon.append(lonS[idx])

n = len(nomi)
dim = int(n * 0.9)


pioggia = random.choices(population=[0, 1, 2, 3], weights=[0.6, 0.2, 0.13, 0.07], k=dim)    # sole, pioggia lieve, media, forte
pioggia.extend([-1] * (n - dim))    # -1 indica che non conosco la situazione meteorologica
random.shuffle(pioggia)

distanze = np.zeros (n**2)
idx = 0


with open ('code/predici.pl', 'w') as file:
	
	for i in range (n):
		for j in range (n):
			if i == j:
				idx += 1
				continue
			distanze[idx] = haversine(lat[i], lon[i], lat[j], lon[j])
			line = 'arco(' + str(i) + ', ' + str(j) + ', ' + str(int(distanze[idx])) + ').\n'
			file.write(line)
			idx += 1
	
	for i in range (n):
		if pioggia[i] == -1:
			continue
		line = 'situazione(' + str(i) + ', ' + converti(pioggia[i]) + ').\n'
		file.write(line)


lim_velocita = 90   # strade extraurbane

tempi = np.zeros (n**2)

for i in range(n**2):
	tempi[i] = distanze[i] / lim_velocita  # tempo = spazio / velocità

idx = 0


with open ('data/nomi.csv', 'w', encoding='utf-8') as f:
	for i in range(n):
		stringa = str(i) + ',' + nomi[i] + '\n'
		f.write (stringa)

with open ('data/dataset.csv', 'w', encoding='utf-8') as f:
	for i in range (n):
		for j in range (n):
			stringa = nomi[i] + ',' + nomi[j] +',' + str(tempi[idx] * 60) + '\n'
			f.write(stringa)
			idx += 1