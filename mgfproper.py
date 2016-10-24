#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import math
from glob import glob
from optparse import OptionParser, OptionGroup



#################################################################################################################
#   PARAMETERS

# default values for command line options
#  - mass tag search
tags_default = "147.1,175.1"		# tags in comma separated list in Da.  Use double brackets, no spaces or units.  --> example: tags_default = "147.1,175.1"
error_default = 0.5					# mass error in Da.  Don't use brackets or units  --> example: error_default = 0.5
limit_default = "5%"				# minimal height the mass tag peak, either as a non-normalised absolute value or as a percentage   --> example: limit_default = "5%"
onetag_default = False				# remove spectra having more than one tag, False or True
dotags_default = True				# do mass tag based selection of spectra, False or True
#  - mascot annotation
bold_default = False				# annotation requires bold (-> first appearance), False or True
red_default = False					# annotation requires red (-> highest rank), False or True
score_default = 40					# annotation requires a minimum score.  Don't use brackets or units  --> example: score_default = 40
domascot_default = True				# no mascot annotation, False or True

# other parameters
separator = "\t"					# separator code CSV formaat ( "\t" = tab)

# code starts below, do not change unless you know what you are doing!
#################################################################################################################






### CODE
print " "
print "MGF proper - MGF cleanup for MS library search approach: select spectra on specific fragments and annotate using Mascot XML data"
print "  Author:\tWim Fremout / Royal Institute for Cultural Heritage, Brussels, Belgium (18 Nov 2011)"
print "  Licence:\tGNU GPL version 3.0\n"

usage = "usage: %prog [options] ORIGINAL_MGF"

parser = OptionParser(usage=usage, version="%prog 0.2")
parser.add_option("-s", "--sample", help="sample name (default: base name of the original MGF file)", action="store", type="string", dest="SAMPLE")
parser.add_option("-d", "--desc", help="long sample description, use \"", action="store", type="string", dest="DESC")
parser.add_option("-v", "--verbose", help="be very verbose", action="store_true", dest="VERBOSE", default=False)
group = OptionGroup(parser, "Mass tag selection of spectra")
group.add_option("--tags", help="tags in comma separated list in Da (default: " + tags_default + ")", action="store", type="string", dest="TAGS", default=tags_default) 
group.add_option("--error", help="mass error in Da (default: " + str(error_default) + ")", action="store", type="float", dest="ERROR", default=error_default)
group.add_option("--limit", help="minimal height the mass tag peak, either as a non-normalised absolute value or as a percentage (default: " + limit_default + ")", action="store", type="string", dest="LIMIT", default=limit_default)
group.add_option("--onetag", help="remove spectra having more than one tag", action="store_true", dest="ONETAG", default=onetag_default)
group.add_option("--notags", help="no mass tag based selection of spectra", action="store_false", dest="DOTAGS", default=dotags_default)
parser.add_option_group(group)
group = OptionGroup(parser, "Mascot annotation using XML file")
group.add_option("--mascot", help="use specified XML file (default: same base name as the original MGF file)", action="store", type="string", dest="XMLFILE")
group.add_option("--bold", help="annotation requires bold (-> first appearance)", action="store_true", dest="BOLD", default=bold_default)
group.add_option("--red", help="annotation requires red (-> highest rank)", action="store_true", dest="RED", default=red_default)
group.add_option("--score", help="annotation requires a minimum score (default: " + str(score_default) + ")", action="store", type="int", dest="SCORE", default=score_default)
group.add_option("--nomascot", help="no mascot annotation", action="store_false", dest="DOMASCOT", default=domascot_default)
parser.add_option_group(group)

(options, args) = parser.parse_args()


#test argumenten en commandline opties
commentsInvar = []

if len(args) == 0:
  exit()
elif len(args) > 1:
  parser.error("incorrect number of arguments")
  exit()

try:
  fh=file(args[0])
except IOError:
  print "! MGF file was not found !"
  print "Aborted"
  exit()
  
commentsInvar.append("13Mgffile=" + args[0].replace(" ", "_"))

if options.XMLFILE == None: options.XMLFILE = args[0].replace(".mgf", ".xml")
try:
  fh=file(options.XMLFILE)
except IOError:
  print "! Mascot XML file was not found !"
  print "Skipping Mascot annotation"
  options.DOMASCOT = False
  
if options.DOMASCOT: commentsInvar.append("14Mascotxml=" + options.XMLFILE.replace(" ", "_"))

if options.SAMPLE == None: options.SAMPLE = args[0].replace(".mgf", "")

if options.DESC == None: options.DESC = options.SAMPLE
commentsInvar.append("05Sample=\"" + options.DESC + "\"")

if '%' in options.LIMIT:
  options.LIMIT = float(options.LIMIT.replace('%',"")) * 9.99
  limitispercent = True
else:
  options.LIMIT = float(options.LIMIT)
  limitispercent = False


#verbose: argumenten opsommen:
if options.VERBOSE:
  print "ORIGINAL MGF FILE:", args, "\n"
  print "PARAMETERS"
  print "  select mass tags:", options.DOTAGS
  if options.DOTAGS:
    print "   - tags:", options.TAGS
    print "   - mass error:", options.ERROR
    print "   - lower limit:", options.LIMIT
    print "   - onetag:", options.ONETAG
  print "  mascot annotation:", options.DOMASCOT
  if options.DOMASCOT:
    print "   - mascot XML file:", options.XMLFILE
    print "   - require bold:", options.BOLD
    print "   - require red:", options.RED
    print "   - require score:", options.SCORE


### VERWERK XML IN EEN MEER LEESBAAR FORMAAT
logfile = open(args[0].replace('.mgf','.mgfproper.log',1), 'w')


if options.DOMASCOT:
  logfile.write("MASCOT RESULTS\n")
  logfile.write(" - export XML: " + options.XMLFILE + "\n")
  logfile.write(" - require bold: " + str(options.BOLD) + "\n")
  logfile.write(" - require red: " + str(options.RED) + "\n")
  logfile.write(" - require score: " + str(options.SCORE) + "\n\n")
  
  print " ... reading mascot XML file: " + options.XMLFILE
  
  xmlfile = open(options.XMLFILE, 'r')
  xmlmodus = ""
  mresult= []
  
  for line in xmlfile:
    #xmlmodus bepaalt hoe we de lijn gaan verwerken
    if "<header>" in line or "<search_parameters>" in line: xmlmodus = "header"
    elif "<hits>" in line:
      logfile.write("\n\n" + separator.join(["spectrum", "pass", "mascot query", "rank", "isbold", "isunique", "calc Mr", "charge", "miscleavages", "score", "expect", "sequence", "var modifications", "position", "mascot protein hit", "accession", "description"]) + "\n")
    elif "<hit number=" in line:
      xmlmodus = "protein"
      proteine = []
      proteine.append(line.split('"')[1])	#0 hit
      proteine.extend(["", ""]) 		#1 prot accession, 2 prot desc
    elif "<peptide query=" in line:
      xmlmodus = "peptide"
      peptide = []
      peptide.append("")			#0 gereserveerd voor pep_scan_title (waarmee we kunnen vergelijken met mgf spectrum titels)
      peptide.append(line.split('"')[1])  	#1 query nr
      peptide.append(line.split('"')[3])  	#2 rank
      peptide.append(line.split('"')[5])  	#3 isbold
      peptide.append(line.split('"')[7])  	#4 isunique
      peptide.extend(["", "", "", "", "", "", "", "", "", ""])			
	#5 calc mr, 6 charge, 7 miss, 8 score, 9 expect, 10 res before, 11 seq, 12 res after, 13 mod, 14 mod pos
      peptide.extend(proteine)			#15 prot hit, 16 prot accession, 17 prot desc
    elif "</peptide>" in line: 
      #opkuis in peptide-lijst
      for i in range(len(peptide)): 
	peptide[i] = peptide[i].replace("&gt;", ">").strip()
      #berekenen of deze peptideannotatie in beschouwing moet genomen worden (bold, red, score)
      vw3 = True
      if options.BOLD: vw1 = (int(peptide[3]) == 1)	#bold: first appearance
      else: vw1 = True
      if options.RED: vw2 = (int(peptide[2]) == 1)	#red: highest rank
      else: vw2 = True
      if options.SCORE > 0: vw3 = (float(peptide[8]) >= options.SCORE)	
      else: vw3 = True
      #mresult lijst: [spectrum-nummer, consider-bool, peptideannotatie-lijst]
      mresult.append(peptide[0].split(":")[0])
      mresult.append(vw1 and vw2 and vw3)
      mresult.append(peptide)
      logfile.write(peptide[0].split(":")[0] + separator + str(vw1 and vw2 and vw3) + separator + separator.join(peptide[1:10]) + separator + ".".join(peptide[10:13]) + separator + separator.join(peptide[13:]) + "\n")
      if options.VERBOSE: 
	print "\n    -> reading Mascot peptide hit", peptide[0].split(":")[0]
	print "    ->" + ",".join(peptide[1:17])
    elif "</hits>" in line: break		#uitbreken uit loop (tijdswinst + verhinderen dat peptide queries ingelezen worden
    
    if xmlmodus == "header" or xmlmodus == "parameters": 
      if "_DISTILLER_RAWFILE" in line: 
	mascot_rawfile = line.split('\\')[-1].replace("</user_parameter>", "").strip()
	commentsInvar.append("12Rawfile=" + mascot_rawfile.replace(" ", "_"))
	logfile.write("rawfile: " + mascot_rawfile)
      elif "<FILENAME>" in line:       logfile.write("mgf file: " + line.replace("<FILENAME>", "").replace("</FILENAME>", ""))
      elif "<URI>" in line:            
	commentsInvar.append("15Mascotlink=" + line.replace("<URI>", "").replace("</URI>", ""))
	logfile.write("mascot search: " + line.replace("<URI>", "").replace("</URI>", ""))
      elif "<DB>" in line:             logfile.write("library: " + line.replace("<DB>", "").replace("</DB>", ""))
      elif "<TAXONOMY>" in line:       logfile.write("taxonomy: " + line.replace("<TAXONOMY>", "").replace("</TAXONOMY>", ""))
      elif "<CLE>" in line:
	logfile.write("enzyme: " + line.replace("<CLE>", "").replace("</CLE>", ""))
	if "Trypsin" in line: commentsInvar.append("08Pep=Tryptic")
      elif "<PFA>" in line:            logfile.write("max missed cleavages: " + line.replace("<PFA>", "").replace("</PFA>", ""))
      elif "<MODS>" in line:           logfile.write("fixed modifications: " + line.replace("<MODS>", "").replace("</MODS>", ""))
      elif "<IT_MODS>" in line:        logfile.write("variable modifications: " + line.replace("<IT_MODS>", "").replace("</IT_MODS>", ""))
      elif "<TOL>" in line:            logfile.write("peptide mass tolerance: " + line.replace("<TOL>", "").replace("</TOL>", ""))
      elif "<ITOL>" in line:           logfile.write("fragment mass tolerance: " + line.replace("<ITOL>", "").replace("</ITOL>", ""))
      elif "<MASS>" in line:           logfile.write("mass values: " + line.replace("<MASS>", "").replace("</MASS>", ""))
      elif "<INSTRUMENT>" in line:
	logfile.write("instrument: " + line.replace("<INSTRUMENT>", "").replace("</INSTRUMENT>", ""))
	if "ESI-QUAD-TOF" in line: commentsInvar.append("09Inst=qtof")
  
    if xmlmodus == "protein":
      if "<protein accession=" in line: proteine[1] = line.split('"')[1]
      elif "<prot_desc>" in line:       proteine[2] = line.replace("<prot_desc>", "").replace("</prot_desc>", "")
      
    if xmlmodus == "peptide":
      if "<pep_scan_title>" in line: peptide[0] =     line.replace("<pep_scan_title>", "").replace("</pep_scan_title>", "")
      elif "<pep_calc_mr>" in line: peptide[5] =      line.replace("<pep_calc_mr>", "").replace("</pep_calc_mr>", "")
      elif "<pep_exp_z>" in line: peptide[6] =        line.replace("<pep_exp_z>", "").replace("</pep_exp_z>", "")
      elif "<pep_miss>" in line:  peptide[7] =        line.replace("<pep_miss>", "").replace("</pep_miss>", "")
      elif "<pep_score>" in line: peptide[8] =        line.replace("<pep_score>", "").replace("</pep_score>", "")
      elif "<pep_expect>" in line: peptide[9] =       line.replace("<pep_expect>", "").replace("</pep_expect>", "") 
      elif "<pep_res_before>" in line: peptide[10] =  line.replace("<pep_res_before>", "").replace("</pep_res_before>", "")
      elif "<pep_seq>" in line: peptide[11] =         line.replace("<pep_seq>", "").replace("</pep_seq>", "")
      elif "<pep_res_after>" in line: peptide[12] =   line.replace("<pep_res_after>", "").replace("</pep_res_after>", "")
      elif "<pep_var_mod>" in line: peptide[13] =     line.replace("<pep_var_mod>", "").replace("</pep_var_mod>", "")
      elif "<pep_var_mod_pos>" in line: peptide[14] = line.replace("<pep_var_mod_pos>", "").replace("</pep_var_mod_pos>", "")      
  
  logfile.write("\n\n\n")
  xmlfile.close()




### VERWERK MGF
print " ... reading MGF file: " + args[0]
mgffile = open(args[0], 'r')
mspfile = open(args[0].replace('.mgf','.mgfproper.msp',1), 'w')

n = 0	#spectrum teller, initialiseren (0 -> header regels)

#header in log
if options.DOTAGS:
  logfile.write("MASS TAG ANALYSIS\n")
  logfile.write(" - mass tags: " + options.TAGS + "\n")
  logfile.write(" - mass errors: " +  str(options.ERROR) + "\n")
  logfile.write(" - intensity limit: " + str(options.LIMIT) + "\n")
  logfile.write(" - one tag: " + str(options.ONETAG) + "\n\n")
  
  options.TAGS = options.TAGS.split(',')
  tresult = []
  
  for i in range(0, len(options.TAGS)):
    tresult.append(options.TAGS[i] + " delta")
    tresult.append(options.TAGS[i] + " intensity")
    tresult.append(options.TAGS[i] + " keep")
  logfile.write("spectrum" + separator + separator.join(map(str, tresult)) + separator + "# of tags\n")

#mgf inlezen en lijn per lijn verwerken
for line in mgffile:
  
  #mgf header
  if n == 0 and not "BEGIN IONS" in line:
    #eerste regels overnemen, of toch grotendeels
    if "DISTILLER_RAWFILE" in line: 
      line = " rawfile=" + line.split('\\')[-1].strip()
      if options.DOMASCOT:
	if not mascot_rawfile in line.replace("rawfile=", ""):
	  print "\n! Mascot results XML and MGF file are based on different measurements !"
	  print "Skip annotation\n"
	  options.DOMASCOT = False
  
  #eerste lijn van een spectrum
  elif "BEGIN IONS" in line:
    n = n + 1
    spectrumx = []	#spectrum (her)initialiseren
    spectrumy = []
    spectrumn = []
    if options.VERBOSE: print "\n    -> reading spectrum ", n
    if options.DOTAGS:
     tresult = []
     for i in range(0, len(options.TAGS)):	#tresult (tag finder results) lijst initialiseren
       tresult.append(0)
       tresult.append(0)
       tresult.append(False)
     tresult.append(0)
  
  #rest van spectrum
  else:
    if "TITLE=" in line: 
      line = line.strip().replace("TITLE=","").strip()
      title = line.split(":")[0]
      seqzlist = []
      protlist = []
      titletemp = ""
      commentsVar = []
      
      #zoeken in mascot results
      if options.DOMASCOT: 
	for i in range(len(mresult[::3])):
	  if int(mresult[i*3]) == int(title):
	    if line == mresult[i*3 + 2][0]: 	#testen of volledige titels overeenkomen om zeker te zijn dat het hetzelfde spectrum is
	      if mresult[i*3 + 1]:		#testen op de voorwaardes (BOLD, RED, SCORE)
		# titel maken
		seqz = mresult[i*3 + 2][11] + "/" + mresult[i*3 + 2][6]  	#sequentie/z
		prot = mresult[i*3 + 2][16]				#prot_asc
		#bestaat die sequentie/z al, dan voegen we enkel proteine toe aan de lijst, anders nieuwe entries
		try: j = seqzlist.index(seqz)
		except ValueError: j = -1
		if  j >= 0: 	#sequentie bestaat al (op positie j in de seqz-lijst)
		  protlist[j] = protlist[j] + "/" + prot
		else:		#sequentie bestaat nog niet
		  seqzlist.append(seqz)
		  protlist.append(prot)
		# comments  (probleem: wat doen als er meerdere mascot hits zijn?)
		if len(seqzlist) == 1:	#eerste hit --> gegevens overnemen
		  commentsVar.append("01Fullname=" + ".".join(mresult[i*3 + 2][10:13]) + "/" +  mresult[i*3 + 2][6])
		  if mresult[i*3 + 2][13] != "": commentsVar.append("02Mods=\"" + mresult[i*3 + 2][13] + "\"")
		  else: commentsVar.append("02Mods=0")
		  if mresult[i*3 + 2][14] != "": commentsVar.append("03Modpos=" + mresult[i*3 + 2][14])
		  commentsVar.append("04Protein=\"" + mresult[i*3 + 2][16] + " " + mresult[i*3 + 2][17] + "\"") 
		else: commentsVar.append("00MultipleMascotAnnotations")
	    else:
	      print "! Spectrum ", mresult[i*3], " does not correspond in XML and MGF !"
	for i in range(len(seqzlist)):
	  seqzlist[i] = seqzlist[i] + " (" + protlist[i] + ")"
	if len(seqzlist) > 0: seqz = "; ".join(seqzlist) + "; "
	else: seqz =  "unannotated; "
      else: seqz = ""
      title =  seqz + args[0].replace(".mgf", "") + " #" + title
	      
    elif "PEPMASS=" in line:
      pepmass = float(line.replace("PEPMASS=", "").strip().split(" ")[0])
      commentsVar.append("06Parent=" + str(pepmass))
      
    elif "CHARGE=" in line:
      commentsVar.append("07Charge=" + line.replace("CHARGE=", "").strip())
      
    elif "RAWSCANS=" in line: pass
    
    elif "SCANS=" in line:
      commentsVar.append("10Scans=" + line.replace("SCANS=", "").strip())

    elif "RTINSECONDS=" in line:
      commentsVar.append("11RT=" + line.replace("RTINSECONDS=", "").strip())    
    
    elif "\t" in line:
      temp = line.strip().split()
      spectrumx.append(float(temp[0]))
      spectrumy.append(float(temp[1]))
      spectrumn.append(0)

    #laatste regel van spectrum --> alle berekeningen
    elif "END IONS" in line:
      f = 999 / max(spectrumy)		#factor voor normalisatie (MSP max:999)
      for i in range(len(spectrumx)):
	#NORMALISEREN
	spectrumn[i] = spectrumy[i] * f
	#TAGS ZOEKEN (= tresult INVULLEN)
	if options.DOTAGS:
	  for j in range(len(options.TAGS)):	#tags overlopen
	    #voor elke x-waarde tussen tag +/- error:
	    if (spectrumx[i] > float(options.TAGS[j]) - float(options.ERROR)) and (spectrumx[i] < float(options.TAGS[j]) + float(options.ERROR)):
	      #als er nog geen tag-hit is of als die er wel is, maar verder verwijderd van de tag, toevoegen (of overschrijven) in tresult
	      if (tresult[j * 3 + 1] == 0) or (tresult[j * 3] > abs(spectrumx[i]) - float(options.TAGS[j])):
		tresult[j * 3] = abs(spectrumx[i] - float(options.TAGS[j]))
		tresult[j * 3 + 1] = spectrumy[i]
		# test of minimum limiet piekhoogte gehaald
		if limitispercent:
		  tresult[j * 3 + 2] = (spectrumn[i] >= options.LIMIT)
		else:
		  tresult[j * 3 + 2] = (spectrumy[i] >= options.LIMIT)
      
      #selecteren op basis van tags + tresult loggen
      if options.DOTAGS:
	for i in range(len(options.TAGS)): 
	  tresult[-1] = tresult[-1] + tresult[i * 3 + 2]
	tresult.insert(0, title.split("#")[1])	#spectrum nr toevoegen aan tresult
	logfile.write(separator.join(map(str, tresult)) + "\n")
	if options.VERBOSE: print "    -> ", tresult
      
      #schrijven van spectra: 3 situaties afhankelijk van DOTAGS en ONETAG
      if (options.DOTAGS and options.ONETAG and tresult[-1] == 1) \
	  or (options.DOTAGS and not options.ONETAG and tresult[-1] > 0) \
	  or (not options.DOTAGS): 
	mspfile.write("Name: " + title + "\n")
	mspfile.write("PRECURSORMZ: " + "%.2f" % round(pepmass,2) + "\n")
	commentsVar.extend(commentsInvar)
	commentsVar.sort()
	for i in range(len(commentsVar)): commentsVar[i] = commentsVar[i][2:].strip()
	mspfile.write("Comments: " + " ".join(commentsVar) + "\n")
	mspfile.write("Num Peaks: " + str(len(spectrumx)) + "\n")
	for i in range(len(spectrumx)):
	  spx = min(spectrumx)
	  j = spectrumx.index(spx)
	  mspfile.write(str(spectrumx.pop(j)) + " " + str("%.2f" % round(spectrumn.pop(j), 2)) + "\n")
	mspfile.write("\n")


mgffile.close()
print " ... saving MSP file: " + args[0].replace('.mgf','.mgfproper.msp',1)
print "       -> can be used directly in NIST MSSearch or MSPepSearch"
mspfile.close()
print " ... saving LOG file: " + args[0].replace('.mgf','.mgfproper.log',1)
print "       -> contains useful intermediary information"
logfile.close()

print "All done."


