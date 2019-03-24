import re
import pandas as pd
import urllib.request
###############################################################
url = "http://psephos.adam-carr.net/countries/m/mali/mali20131.txt"
###############################################################

# reading in the raw txt
pf = urllib.request.urlopen(url)
raw = pf.read().decode('ISO-8859-1')
pf.close

# 1) cutting up the raw text into big chunks, the keyword on which the cutting happens is "REGION"
a = True
byreg = []
while a == True:
	if re.search(r'(\n)([A-Z]+?\sREGION.+?\n)([A-Z]+?\sREGION)',raw, flags=re.DOTALL) != None:
		j = re.search(r'(\n)([A-Z]+?\sREGION.+?\n)([A-Z]+?\sREGION)',raw, flags=re.DOTALL).group(2)
		byreg.append(j)
		raw = raw.replace(j,"")
	else:
		j = re.search(r'(\n)([A-Z]+?\sREGION.+)',raw, flags=re.DOTALL).group(2)
		byreg.append(j)
		raw = raw.replace(j,"")
		a = False
	
# 2) getting the region names from each of the big chunks
regns = []
for reg in byreg:
	regn = re.search(r'([A-Z]+?)(\sREGION)',reg).group(1)
	#print(regn) 
	regns.append(regn)


# 3) cut up each region chunk into its constituency chunks, the keyword on which the cutting happens is "seat" or "seats"
regconsts = []
for reg in byreg:

	contsts = []

	while re.search(r'([A-Z\s-]+?\([0-9]\sseat[s]?\).+?)(\n[A-Z\s-]+?\([0-9]\sseat[s]?\))', reg, flags = re.DOTALL) != None:
		j = re.search(r'([A-Z\s-]+?\([0-9]\sseat[s]?\).+?)(\n[A-Z\s-]+?\([0-9]\sseat[s]?\))', reg, flags = re.DOTALL).group(1)

		contsts.append(j)
		reg = reg.replace(j,"")

	j = re.search(r'(.+?)([A-Z\s-]+?\([0-9]\sseat[s]?\).+)', reg, flags = re.DOTALL).group(2)			
	contsts.append(j)
	regconsts.append(contsts)


# 4) getting the constituency name from each of the smaller constituency chunks
cnames = []
for rc in regconsts:
	regcnms = []
	for const in rc:
		#print(const)
		constname = re.search(r'.+?\([0-9]\sseat.*?\)', const).group(0)
		regcnms.append(constname)
	cnames.append(regcnms)


# 5) getting the vote and deputy information from every constituency chunk
votes = []
deps = []
for reg in regconsts:
	regvotes = []
	regdeps = []
	for const in reg:

		#print(const)

		voteblock = re.search(r'(Party.+?\n-+?.\n)(.+?)(\n--------)', const, flags = re.DOTALL).group(2)
		#print(voteblock)
		regvotes.append(voteblock)

		try:
			depblock = re.search(r'(Deputies.+?\n-+?.\n)(.+)', const, flags = re.DOTALL).group(2)
		except:
			depblock = re.search(r'(Total.+?\n-+?.\n)(.+)', const, flags = re.DOTALL).group(2)

		# special case: there are some deputies which were published on abamako.com, but which 
		# do not end up on the supreme court's official list. these cases are flagged with "_yyyyyy"
		if re.search(r'appear', depblock) != None:
			dbaux = depblock[:]
			depblock = re.search(r'(.+?)(\n-----)', dbaux, flags = re.DOTALL).group(1)
			note = re.search(r'(.+?-+?.\n)(.+)', dbaux, flags = re.DOTALL).group(2)


			for candidate in depblock.split():
				if re.search(r"%s\s*?\n" % candidate, depblock) != None:
					thisk = candidate
					depblock = re.sub(r'%s' % thisk, r'%s_yyyyyy' % thisk, depblock)

		#print(depblock)
		regdeps.append(depblock)

	votes.append(regvotes)
	deps.append(regdeps)


# 6) turning the deputies for each constituency into lists
newdeps = []
for reg in deps:
	regdeps = []
	for constd in reg:
		# special case: if the supreme court published a different list of candidates to the one abamako.com
		# said won, include those list in a second list
		if "abamako.com" in constd:
			print(constd)	

			dep1 = re.search(r'(.+?)(\n-+?.\nAlthough.+?elected:.\n)(.+)', constd, flags = re.DOTALL).group(1)
			dep2 = re.search(r'(.+?)(\n-+?.\nAlthough.+?elected:.\n)(.+)', constd, flags = re.DOTALL).group(3)

			dep1 = [s.strip() for s in dep1.splitlines()]
			dep2 = [s.strip() for s in dep2.splitlines()]

			# remove empty deputies
			dep2filtered = list(filter(lambda x: not re.match(r'^\s*$', x), dep2))

			# flag the second (supreme court list) candidates with "_zzzzz"
			dep2filttagged = []
			for cand in dep2filtered:
				dep2filttagged.append(cand + "_zzzzz")

			regdeps.append([dep1, dep2filttagged])

		else:
			# if no difference between abamako.com and supreme court list, add a second, empty list
			# to the one in which the court and the website both agree
			regdeps.append([[s.strip() for s in constd.splitlines()], ['']])

	newdeps.append(regdeps)

# 7) removing "----" and empty candidates (for the empty ones, dont remove the second lists
# created above in cases there where there was no alternative list of candidates imposed by the supreme court)
for reg in newdeps:
	for const in reg:
		for deplist in const:
			for idx, dep in enumerate(deplist):
				if "----" in dep:
					del deplist[idx]
			a = True	
			while a == True:
				for idx, dep in enumerate(deplist):
					a = False
					if dep == '' and idx > 0:
						del deplist[idx]	
						a = True				


# 8) creating a single list of (correctly flagged for both exceptions) deputies
deps = []
for reg in newdeps:
	regdeps = []
	for const in reg:
		cdeps = []
		for dl in const:
			for dep in dl:
				cdeps.append(dep)


		cdfilt = list(filter(lambda x: not re.match(r'^\s*$', x), cdeps))		
		#print(cdfilt)

		regdeps.append(cdfilt)
	deps.append(regdeps)


# 9) create a list of votes for each party and constituency:
# [party name, votes in first round, vote share first round, votes in second round, vote share second round]
newvotes = []
for reg in votes:
	regvotes = []
	for const in reg:
		cvts = []
		constvotes = const.splitlines()
		for part in constvotes:
			pname = re.search(r'(.+?)(\s{2,})', part).group(1)
			#print(pname)
			votes1 = re.search(r'(\s{2,})([0-9,]+?\s|Unopposed)', part).group(2).strip()
			#print(votes1)
			if votes1 != 'Unopposed':
				voteshare1 = re.search(r'(\s{2,})([0-9,]+?\s+?)([0-9]{2}\.[0-9])', part).group(3)
				#print(voteshare1)
				re2ndround = re.search(r'(\s{2,})([0-9,]+?\s+?)([0-9]{2}\.[0-9])(\s{2,})([0-9,]+?)(\s+)([0-9]{2}\.[0-9])', part)
				if re2ndround != None:
					votes2 = re2ndround.group(5).strip()
					voteshare2 = re2ndround.group(7).strip()
				else:
					votes2 = ''
					voteshare2 = ''
			else:
				voteshare1 = ''
				votes2 = ''
				voteshare2 = ''

			cvts.append([pname, votes1, voteshare1, votes2, voteshare2])

		regvotes.append(cvts)

	newvotes.append(regvotes)


# 10) putting everything together in list of tuples
tldep = []
tlpart = []
for idr, reg in enumerate(newvotes):
	rnm = regns[idr]
	for idc, const in enumerate(reg):
		cnm = cnames[idr][idc]
		for dep in deps[idr][idc]:
			#print((rnm, cnm, dep))
			tldep.append((rnm, cnm, dep))
			#print((rnm, cnm, dep))
		for part in newvotes[idr][idc]:
			#print((rnm, cnm) + tuple(part))
			tlpart.append((rnm, cnm) + tuple(part))
			#print((rnm, cnm) + tuple(part))			



# 11) creating pandas dataframes out of tuple lists
colnames = ['region', 'constituency', 'deputy']
outdep = pd.DataFrame(tldep, columns=colnames)		

colnames = ['region', 'constituency', 'party', 'votes_r1', 'voteshare_r1', 'votes_r2', 'voteshare_r2']
outpart = pd.DataFrame(tlpart, columns=colnames)	

# print(outdep)
# print('\n\n\n')
# print(outpart)


outdep.to_csv('MLI_2013_deps_cleaned.csv', encoding = 'ISO-8859-1', index = False, na_rep='')
outpart.to_csv('MLI_2013_parts_cleaned.csv', encoding = 'ISO-8859-1', index = False, na_rep='')
