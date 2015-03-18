from optparse import OptionParser
parser = OptionParser()
parser.add_option("--inputFiles", dest="inputFiles", default='relValFiles.pkl', type="string", action="store", help="pkl file with eos filenames")
parser.add_option("--outputFile", dest="outputFile", default='relValData.pkl', type="string", action="store", help="pkl file with output data")
(options, args) = parser.parse_args()

import ROOT
from DataFormats.FWLite import Events, Handle
from PhysicsTools.PythonAnalysis import *
from math import *
import sys, os, copy, random, subprocess, datetime
import pickle

small = False

ROOT.gSystem.Load("libFWCoreFWLite.so")
ROOT.AutoLibraryLoader.enable()

maxEvts=-1

edmCollections = [ \
  ("vector<reco::PFMET>", "pfMet", ""), #, "RECO")
  ("vector<reco::CaloMET>", "caloMet",""),
  ("vector<reco::PFCandidate>", "particleFlow", "")
] 

from categories import *
inputFiles = options.inputFiles.split(',')
print "Running over files:",inputFiles
print "Writing to:",options.outputFile

handles={v[1]:Handle(v[0]) for v in edmCollections}
res={}

events = Events(inputFiles)
events.toBegin()
products={}
size=events.size() if not small else 10

missingCollections=[]
for nev in range(size):
  if nev%1000==0:print nev,'/',size
  events.to(nev)
  eaux=events.eventAuxiliary()
  run=eaux.run()            
  event=eaux.event()
  lumi=eaux.luminosityBlock()
  evkey = ":".join(str(x) for x in [run,lumi,event])
  for v in [ x for x in edmCollections if x[1] not in missingCollections]:
    try:
      events.getByLabel(v[1:],handles[v[1]])
      products[v[1]]=handles[v[1]].product()
    except:
      products[v[1]]=None
      print "Not found:",v[1]
      missingCollections.append(v[1])
  sumPt={"sumPt_"+t['name']:0. for t in allCategories}
  MEx={"MEx_"+t['name']:0. for t in allCategories}
  MEy={"MEy_"+t['name']:0. for t in allCategories}
  mult={"mult_"+t['name']:0 for t in allCategories}
  print "Event",nev,'size',products['particleFlow'].size()
  for p in range(products['particleFlow'].size()):
    cand = products['particleFlow'][p]
    l=label[cand.particleId()]
    for c in allCategories:
      if c['type']==l:
        aeta=abs(cand.eta())
        if aeta>=c['etaRange'][0] and aeta<c['etaRange'][1]:
          sumPt["sumPt_"+c['name']]+=cand.pt() 
          mult["mult_"  +c['name']]+=1 
          MEx["MEx_"    +c['name']]+=-cand.px() 
          MEy["MEy_"    +c['name']]+=-cand.py()
  d={}
  if products["pfMet"] and "pfMet" not in missingCollections:
    d.update({'met':products["pfMet"][0].pt(),  'sumEt':products["pfMet"][0].sumEt(), 'metPhi':products["pfMet"][0].phi()})
  if products["caloMet"] and "caloMet" not in missingCollections:
    d.update({'caloMet':products["caloMet"][0].pt(),  'caloSumEt':products["caloMet"][0].sumEt(), 'caloMetPhi':products["caloMet"][0].phi()})
  d.update(sumPt)
  d.update(mult)
  d.update({'MET_'+c['name']:sqrt(MEx["MEx_"+c['name']]**2+MEy["MEy_"+c['name']]**2) for c in allCategories })
  res[evkey]=d
print res[evkey]
pickle.dump(res, file(options.outputFile,'w'))
print "Written",options.outputFile
