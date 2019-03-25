import re
import pandas as pd
import urllib.request
###############################################################
url = "http://psephos.adam-carr.net/countries/n/nigeria/nigeria20072.txt"
###############################################################

# reading in the raw txt
pf = urllib.request.urlopen(url)
raw = pf.read().decode('ISO-8859-1')
pf.close

# 1) cut of raw text into state chunks
statchunks = re.split(r'[A-Z\s]+?\sSTATE', raw, flags = re.DOTALL)
del statchunks[0]
aux = re.findall(r'[A-Z\s-]+?\sSTATE', raw, flags = re.DOTALL)

# 2) get state names
statnms = []
for snm in aux:
	a = re.sub(r'-+?', '', snm).strip()
	statnms.append(a)
# for s in statnms:
# 	print(s)

# 3) get constituency names and vote information by (constituency within) state
cnmsbystat = []
votesbystat = []
for stat in statchunks:
	aux = re.findall(r'[A-Z\s()-]+?\n', stat, flags = re.DOTALL)

	csinstat = []
	for aix in aux:
		if re.search(r'-{2,}?',aix.strip(), flags=re.DOTALL) != None:
			continue
		elif aix.strip() == '':
			continue
		else:
			csinstat.append(aix.strip())
	cnmsbystat.append(csinstat)

	votesinstat = []
	aux = re.split(r'[A-Z\s-]+?\n={2,}?.\n', stat, flags = re.DOTALL)
	for aix in aux:
		#print(5555)
		#print(aix)
		if re.search(r'(Candidate.+?\n)(.+?)(\nTotal)', aix, flags = re.DOTALL) != None:
			a = re.search(r'(Candidate.+?\n)(-{2,}?.\n)(.+?)(-{2,}.\nTotal)', aix, flags = re.DOTALL).group(3).strip()
		# else:
		# 	print(aix)

			votesinstat.append(a)
	
	votesbystat.append(votesinstat)

# for stat in votesbystat:
# 	for c in stat:
# 		print(c)

# for stat in cnmsbystat:
# 	for c in stat:
# 		print(c)


#3) create a list of votes for each party and constituency:
#[candidate name, party name, votes, vote share]
vbys = []
for stat in votesbystat:
	svts = []
	for c in stat:
		plines = c.splitlines()
		cvts = []		
		for p in plines:
			#print(p)
			cname = re.search(r'(.+?)(\s{2,})', p).group(1)
			
			if re.search(r'([A-z\s]+?)(\s{2,})([A-z\s-]+?)(\s{2,})', p) != None:
				pname = re.search(r'([A-z\s]+?)(\s{2,})([A-z\s-]+?)(\s{2,})', p).group(3)
			else:
				pname = ''

			#print(pname)
			
			if re.search(r'(.+?)(\s{2,}?)(.*?)(\s{2,}?)([0-9,]+?)(\s{2,}?)', p) != None:
				votes = re.search(r'(.+?)(\s{2,}?)(.*?)(\s{2,}?)([0-9,]+?)(\s{2,}?)', p).group(5)
			elif re.search(r'[0-9,]+?', p) != None:
				votes = re.search(r'[0-9,]+?', p).group(0)
			else:
				votes = ''

			#print(votes)	

			if re.search(r'(.+?)(\s{2,}?)(.*?)(\s{2,}?)([0-9,]+?)(\s{2,}?)([0-9\.]+)', p) != None:
				voteshare = re.search(r'(.+?)(\s{2,}?)(.*?)(\s{2,}?)([0-9,]+?)(\s{2,}?)([0-9\.]+)', p).group(7)
			else:
				voteshare = ''
			#print(voteshare) 	

			cvts.append([cname, pname, votes, voteshare])

		svts.append(cvts)

	vbys.append(svts)

# print(len(votesbystat), len(cnmsbystat))

# for ids, _ in enumerate(votesbystat):
# 	for idc, __ in enumerate(votesbystat[ids]):
# 		try:
# 			a, b = len(votesbystat[ids][idc]), len(cnmsbystat[ids][idc])
# 		except IndexError:
# 			print(ids, idc)
# 			print(len(votesbystat[ids]))
# 			print(len(cnmsbystat[ids]))

# 4) putting everything together in list of tuples
tlpart = []
for ids, stat in enumerate(vbys):
	snm = statnms[ids]
	for idc, const in enumerate(stat):
		cnm = cnmsbystat[ids][idc]
		for part in const:
			tlpart.append( (snm, cnm) + tuple(part) )

# 5) creating pandas dataframes out of tuple lists
colnames = ['state', 'constituency', 'candidate', 'party', 'votes', 'voteshare']
outpart = pd.DataFrame(tlpart, columns=colnames)	
print(outpart)

outpart.to_csv('NGA_2007_cleaned.csv', encoding = 'ISO-8859-1', index = False, na_rep='')


