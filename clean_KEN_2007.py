import re
import pandas as pd
import urllib.request
###############################################################
url = "http://psephos.adam-carr.net/countries/k/kenya/kenya20072.txt"
###############################################################

# reading in the raw txt
pf = urllib.request.urlopen(url)
raw = pf.read().decode('ISO-8859-1')
pf.close

# 1) cut of raw text into province chunks
provchunks = re.split(r'[A-Z\s]+?\sPROVINCE', raw, flags = re.DOTALL)
del provchunks[0]
aux = re.findall(r'[A-Z\s-]+?\sPROVINCE', raw, flags = re.DOTALL)

# 2) get province names
provnms = []
for pnm in aux:
	a = re.sub(r'-+?', '', pnm).strip()
	provnms.append(a)

# 3) get constituency names and vote information by (constituency within) province
cnmsbyprov = []
votesbyprov = []
for prov in provchunks:
	aux = re.findall(r'[A-Z\s-]+?\n', prov, flags = re.DOTALL)

	csinprov = []
	for aix in aux:
		if re.search(r'-{2,}?',aix.strip(), flags=re.DOTALL) != None:
			continue
		elif aix.strip() == '':
			continue
		else:
			csinprov.append(aix.strip())
	cnmsbyprov.append(csinprov)

	votesinprov = []
	aux = re.split(r'[A-Z\s]+?\n', prov, flags = re.DOTALL)
	for aix in aux:
		#print(5555)
		#print(aix)
		if re.search(r'(Candidate.+?\n)(.+?)(\nTotal)', aix, flags = re.DOTALL) != None:
			a = re.search(r'(Candidate.+?\n)(-{2,}?\n)(.+?)(-{2,}\nTotal)', aix, flags = re.DOTALL).group(3).strip()

			votesinprov.append(a)
	
	votesbyprov.append(votesinprov)

# for prov in votesbyprov:
# 	for c in prov:
# 		print(c)

# for prov in cnmsbyprov:
# 	for c in prov:
# 		print(c)


#3) create a list of votes for each party and constituency:
#[candidate name, party name, votes, vote share]
vbyp = []
for prov in votesbyprov:
	pvts = []
	for c in prov:
		plines = c.splitlines()
		cvts = []		
		for p in plines:
			cname = re.search(r'(.+?)(\s{2,})', p).group(1)
			
			if re.search(r'([A-z\s]+?)(\s{2,})([A-z\s-]+?)(\s{2,})', p) != None:
				pname = re.search(r'([A-z\s]+?)(\s{2,})([A-z\s-]+?)(\s{2,})', p).group(3)
			else:
				pname = ''

			#print(pname)
			
			votes = re.search(r'(.+?)(\s{2,}?)(.*?)(\s{2,}?)([0-9,]+?)(\s{2,}?)', p).group(5) 	
			#print(votes)

			voteshare = re.search(r'(.+?)(\s{2,}?)(.*?)(\s{2,}?)([0-9,]+?)(\s{2,}?)([0-9\.]+)', p).group(7)
			#print(voteshare) 	

			cvts.append([cname, pname, votes, voteshare])

		pvts.append(cvts)

	vbyp.append(pvts)


# 4) putting everything together in list of tuples
tlpart = []
for idp, prov in enumerate(vbyp):
	pnm = provnms[idp]
	for idc, const in enumerate(prov):
		cnm = cnmsbyprov[idp][idc]
		for part in const:
			tlpart.append( (pnm, cnm) + tuple(part) )

# 5) creating pandas dataframes out of tuple lists
colnames = ['province', 'constituency', 'candidate', 'party', 'votes', 'voteshare']
outpart = pd.DataFrame(tlpart, columns=colnames)	
print(outpart)

outpart.to_csv('KEN_2007_cleaned.csv', encoding = 'ISO-8859-1', index = False, na_rep='')

