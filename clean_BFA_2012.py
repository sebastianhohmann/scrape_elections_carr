import re
import pandas as pd
import urllib.request
###############################################################
url = "http://psephos.adam-carr.net/countries/b/burkinafaso/burkinafaso20022.txt"
###############################################################

# reading in the raw txt
pf = urllib.request.urlopen(url)
raw = pf.read().decode('ISO-8859-1')
pf.close

# 1) cut of raw text into region chunks
constchunks = re.split(r'REGION\s[0-9]+:.+?\n', raw, flags = re.DOTALL)
del constchunks[0]

constnms = re.findall(r'REGION\s[0-9]+:.+?\)', raw, flags = re.DOTALL)

# 2) getting the vote and deputy information from every constituency chunk
votes = []
for c in constchunks:

	#voteblock = re.search(r'(Party.+?\n-+?.\n)', c, flags = re.DOTALL).group(1)
	voteblock = re.search(r'(Party.+?\n-+?.\n)(.+?)(\n--------)', c, flags = re.DOTALL).group(2)
	votes.append(voteblock)

# 3) create a list of votes for each party and constituency:
# [party name, votes, vote share, number of seats]
vbyr = []
for const in votes:
	cvts = []
	constvotes = const.splitlines()
	for part in constvotes:
		pname = re.search(r'(.+?)(\s{2,})', part).group(1)
		#print(pname)
		votes = re.search(r'(\s{2,})([0-9,]+?\s|Unopposed)', part).group(2).strip()
		#print(votes1)
		if votes != 'Unopposed':
			voteshare = re.search(r'(\s{2,})([0-9,]+?\s+?)([0-9]{2}\.[0-9])', part).group(3)
			seats = re.search(r'(\s{2,})([0-9,]+?\s+?)([0-9]{2}\.[0-9]\s+?)([0-9-])', part).group(4)
			#print(voteshare1)
		else:
			voteshare = ''
		cvts.append([pname, votes, voteshare, seats])
	vbyr.append(cvts)


# 4) putting everything together in list of tuples
tlpart = []
for idr, reg in enumerate(vbyr):
	rnm = constnms[idr]
	for part in reg:
		tlpart.append((rnm,) + tuple(part))

# 5) creating pandas dataframes out of tuple lists
colnames = ['region', 'party', 'votes', 'voteshare', 'seats']
outpart = pd.DataFrame(tlpart, columns=colnames)	
print(outpart)

outpart.to_csv('BFA_2012_cleaned.csv', encoding = 'ISO-8859-1', index = False, na_rep='')
