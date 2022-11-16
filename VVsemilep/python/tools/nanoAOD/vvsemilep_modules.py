import os
import ROOT 
import copy 
conf = dict(
        muPt = 15, 
        elePt = 15, 
        sip3dloose = 8, 
        sip3dtight = 4, 
        dxy =  0.05, 
        dz = 0.1, 
        eleIdloose = "mvaFall17V2Iso_WPL",
        eleIdtight = "mvaFall17V2Iso_WP90",
        muIdloose = "looseId",
        muIdtight = "tightId",
        mutrk = "isTracker",
        muIsoloose=0.40,
        muIsotight=0.15,
        fatjetptcut=200,
        jetptcut=25,
        jeteta=2.4
)



vvsemilep_skim_cut = ("nMuon + nElectron >= 1 &&" +
                      "( (Sum$(Jet_pt > {jetptcut} && abs(Jet_eta) < {jeteta}  && Jet_jetId > 0) > 1 ) || (Sum$(FatJet_pt > {fatjetptcut} && abs(FatJet_eta) < {jeteta}) > 0) ) &&" + 
                      "Sum$(Muon_pt > {muPt}  && Muon_{mutrk} && Muon_sip3d < {sip3dloose} && Muon_{muIdloose} &&  Muon_pfRelIso03_all < {muIsoloose}) +"
                      "Sum$(Electron_pt > {elePt} && Electron_sip3d < {sip3dloose}  && Electron_{eleIdloose} ) >= 1").format(**conf)


muonSelection     = lambda l : abs(l.eta) < 2.4 and l.pt > conf["muPt" ] and l.sip3d < conf["sip3dloose"] and \
                    abs(l.dxy) < conf["dxy"] and abs(l.dz) < conf["dz"] and getattr(l, conf["muIdloose"]) and  \
                    getattr(l, conf["mutrk"]) and l.pfRelIso03_all < conf["muIsoloose"]
electronSelection = lambda l : abs(l.eta) < 2.5 and l.pt > conf["elePt"] and l.sip3d < conf["sip3dloose"] and abs(l.dxy) < conf["dxy"] and abs(l.dz) < conf["dz"] and getattr(l, conf["eleIdloose"])

def clean_and_FO_selection_VVsemilep(lep,year, subera): ##am for tight leptn ids not sure if era is needed now
    return lep.pt>conf["elePt"] and (abs(lep.pdgId)!=11 or (ttH_idEmu_cuts_E3(lep) ))

tightLeptonSel = lambda lep,year,era : clean_and_FO_selection_VVsemilep(lep,year,era) and lep.sip3d < conf["sip3dtight"] and (abs(lep.pdgId)!=13 or (lep.tightId and lep.pfRelIso03_all < conf["muIsotight"])) and (abs(lep.pdgId)!=11 or lep.mvaFall17V2Iso_WP90)

foTauSel = lambda tau: tau.pt > 20 and abs(tau.eta)<2.3 and abs(tau.dxy) < 1000 and abs(tau.dz) < 0.2  and (int(tau.idDeepTau2017v2p1VSjet)>>1 & 1) # VVLoose WP
tightTauSel = lambda tau: (int(tau.idDeepTau2017v2p1VSjet)>>2 & 1) # VLoose WP

from CMGTools.VVsemilep.tools.nanoAOD.ttHPrescalingLepSkimmer import ttHPrescalingLepSkimmer
# NB: do not wrap lepSkim a lambda, as we modify the configuration in the cfg itself 
lepSkim = ttHPrescalingLepSkimmer(5, 
                muonSel = muonSelection, electronSel = electronSelection,
                minLeptonsNoPrescale = 1, # things with less than 2 leptons are rejected irrespectively of the prescale
                minLeptons = 1, requireOppSignPair = True,
                jetSel = lambda j : j.pt > conf["jetptcut"] and abs(j.eta) <  conf["jeteta"] and j.jetId > 0, 
                fatjetSel = lambda f : f.pt > conf["fatjetptcut"] and abs(f.eta) < conf["jeteta"],  ##not all samples have fatjets
                minJets = 4, minMET = 70, minFatJets = 1)
from PhysicsTools.NanoAODTools.postprocessing.modules.common.collectionMerger import collectionMerger
lepMerge = collectionMerger(input = ["Electron","Muon"], 
                            output = "LepGood", 
                            selector = dict(Muon = muonSelection, Electron = electronSelection))


from CMGTools.VVsemilep.tools.nanoAOD.ttHLeptonCombMasses import ttHLeptonCombMasses
lepMasses = ttHLeptonCombMasses( [ ("Muon",muonSelection), ("Electron",electronSelection) ], maxLeps = 4)

from CMGTools.VVsemilep.tools.nanoAOD.autoPuWeight import autoPuWeight
from CMGTools.VVsemilep.tools.nanoAOD.yearTagger import yearTag
from CMGTools.VVsemilep.tools.nanoAOD.xsecTagger import xsecTag
from CMGTools.VVsemilep.tools.nanoAOD.lepJetBTagAdder import lepJetBTagDeepFlav, lepJetBTagDeepFlavC
from CMGTools.VVsemilep.tools.nanoAOD.LepMVAULFriend import lepMVA



vvsemilep_sequence_step1 = [lepSkim, lepMerge, autoPuWeight, yearTag, lepJetBTagDeepFlav, xsecTag, lepMasses]

#==== 
from PhysicsTools.NanoAODTools.postprocessing.tools import deltaR
from CMGTools.VVsemilep.tools.nanoAOD.ttHLepQCDFakeRateAnalyzer import ttHLepQCDFakeRateAnalyzer
centralJetSel = lambda j : j.pt > conf["jetptcut"] and abs(j.eta) < conf["jeteta"] and j.jetId > 0
lepFR = ttHLepQCDFakeRateAnalyzer(jetSel = centralJetSel,
                                  pairSel = lambda pair : deltaR(pair[0].eta, pair[0].phi, pair[1].eta, pair[1].phi) > 0.7,
                                  maxLeptons = 1, requirePair = True)
from CMGTools.VVsemilep.tools.nanoAOD.nBJetCounter import nBJetCounter
nBJetDeepFlav25NoRecl = lambda : nBJetCounter("DeepFlav25", "btagDeepFlavB", centralJetSel)

ttH_sequence_step1_FR = [m for m in vvsemilep_sequence_step1 if m != lepSkim] + [ lepFR, nBJetDeepFlav25NoRecl() ]
ttH_skim_cut_FR = ("nMuon + nElectron >= 1 && nJet >= 1 && Sum$(Jet_pt > 25 && abs(Jet_eta)<2.4) >= 1 &&" + 
                   "Sum$(Muon_pt > {muPt} && Muon_sip3d < {sip3dloose}) +"
                   "Sum$(Electron_pt > {muPt}  && Electron_sip3d < {sip3dloose}) ").format(**conf)


#==== items below are normally run as friends ====

def ttH_idEmu_cuts_E3(lep):
    if (abs(lep.pdgId)!=11): return True
    if (lep.hoe>=(0.10-0.00*(abs(lep.eta+lep.deltaEtaSC)>1.479))): return False
    if (lep.eInvMinusPInv<=-0.04): return False
    if (lep.sieie>=(0.011+0.019*(abs(lep.eta+lep.deltaEtaSC)>1.479))): return False
    return True

def conept_TTH(lep):
    if (abs(lep.pdgId)!=11 and abs(lep.pdgId)!=13): return lep.pt
    if (abs(lep.pdgId)==13 and lep.mediumId>0 and lep.mvaTTH > 0.85) or (abs(lep.pdgId) == 11 and lep.mvaTTH > 0.90): return lep.pt
    else: return 0.90 * lep.pt * (1 + lep.jetRelIso)

def smoothBFlav(jetpt,ptmin,ptmax,year, subera,scale_loose=1.0):
    wploose = ([0.0508, 0.0480], [0.0532], [0.0490])
    wpmedium = ([0.2598,0.2489], [0.3040], [0.2783])
    x = min(max(0.0, jetpt - ptmin)/(ptmax-ptmin), 1.0)
    return x*wploose[year-2016][subera]*scale_loose + (1-x)*wpmedium[year-2016][subera]



jevariations=['jes%s'%x for x in ["FlavorQCD", "RelativeBal", "HF", "BBEC1", "EC2", "Absolute", "BBEC1_year", "EC2_year", "Absolute_year", "HF_year", "RelativeSample_year" ]] + ['jer%d'%j for j in range(6)]
from CMGTools.VVsemilep.tools.combinedObjectTaggerForCleaning import CombinedObjectTaggerForCleaning
from CMGTools.VVsemilep.tools.nanoAOD.fastCombinedObjectRecleaner import fastCombinedObjectRecleaner
recleaner_step1 = lambda : CombinedObjectTaggerForCleaning("InternalRecl",
                                                           looseLeptonSel = lambda lep : lep. pt > conf["elePt"] and lep.sip3d < conf["sip3dloose"] and (abs(lep.pdgId)!=11 or lep.mvaFall17V2Iso_WPL) and (abs(lep.pdgId)!=13 or lep.looseId),
                                                           cleaningLeptonSel = clean_and_FO_selection_VVsemilep,
                                                           FOLeptonSel = clean_and_FO_selection_VVsemilep,
                                                           tightLeptonSel = tightLeptonSel,
                                                           FOTauSel = foTauSel,
                                                           tightTauSel = tightTauSel,
                                                           selectJet =    lambda jet: jet.pt > conf["jetptcut"] and abs(jet.eta) < conf["jeteta"] and jet.jetId > 0, # pt and eta cuts are (hard)coded in the step2 
                                                           selectFatJet = lambda fatjet: fatjet.pt > conf["fatjetptcut"] and abs(fatjet.eta) < conf["jeteta"], 
                                                           coneptdef =    lambda lep: conept_TTH(lep),
)
recleaner_step2_mc_allvariations = lambda : fastCombinedObjectRecleaner(label="Recl", inlabel="_InternalRecl",
                                                                        cleanTausWithLooseLeptons=True,
                                                                        cleanJetsWithFOTaus=True,
                                                                        doVetoZ=False, doVetoLMf=False, doVetoLMt=False,
                                                                        jetPts=[25,30],
                                                                        jetPtsFwd=[25,60], # second number for 2.7 < abseta < 3, the first for the rest
                                                                        btagL_thr=99, # they are set at runtime 
                                                                        btagM_thr=99,
                                                                        isMC = True,
                                                                        variations= jevariations,
                                                                        
)

recleaner_step2_mc = lambda : fastCombinedObjectRecleaner(label="Recl", inlabel="_InternalRecl",
                                                          cleanTausWithLooseLeptons=True,
                                                          cleanJetsWithFOTaus=True,
                                                          doVetoZ=False, doVetoLMf=False, doVetoLMt=False,
                                                          jetPts=[25,30],
                                                          jetPtsFwd=[25,60], # second number for 2.7 < abseta < 3, the first for the rest
                                                          btagL_thr=99, # they are set at runtime 
                                                          btagM_thr=99,
                                                          isMC = True,
                                                          
)
recleaner_step2_data = lambda : fastCombinedObjectRecleaner(label="Recl", inlabel="_InternalRecl",
                                         cleanTausWithLooseLeptons=True,
                                         cleanJetsWithFOTaus=True,
                                         doVetoZ=False, doVetoLMf=False, doVetoLMt=False,
                                         jetPts=[25,30],
                                         jetPtsFwd=[25,60], # second number for 2.7 < abseta < 3, the first for the rest
                                         btagL_thr=-99., # they are set at runtime  
                                         btagM_thr=-99., # they are set at runtime  
                                         isMC = False,
                                         variations = []

)

tauFOs = lambda t : t.idDeepTau2017v2p1VSe & 1 and t.idDeepTau2017v2p1VSmu & 1
countTaus_veto             = lambda : ObjTagger('Tight'            ,'TauSel_Recl', [lambda t : t.idDeepTau2017v2p1VSjet&4]) # to veto in tauless categories
countTaus_FO               = lambda : ObjTagger('FO'               ,'TauSel_Recl', [tauFOs]                               ) # actual FO (the FO above is used for jet cleaning, and corresponds to the loose)
from CMGTools.VVsemilep.tools.nanoAOD.tauMatcher import tauScaleFactors


countTaus = [countTaus_veto,countTaus_FO]






from CMGTools.VVsemilep.tools.hjDummCalc import HjDummyCalc
hjDummy = lambda : HjDummyCalc(variations  = [ 'jes%s'%v for v in jecGroups] + ['jer%s'%x for x in ['barrel','endcap1','endcap2highpt','endcap2lowpt' ,'forwardhighpt','forwardlowpt']  ]  + ['HEM'])

from CMGTools.VVsemilep.tools.objTagger import ObjTagger
isMatchRightCharge = lambda : ObjTagger('isMatchRightCharge','LepGood', [lambda l,g : (l.genPartFlav==1 or l.genPartFlav == 15) and (g.pdgId*l.pdgId > 0) ], linkColl='GenPart',linkVar='genPartIdx')
mcMatchId     = lambda : ObjTagger('mcMatchId','LepGood', [lambda l : (l.genPartFlav==1 or l.genPartFlav == 15) ])
mcPromptGamma = lambda : ObjTagger('mcPromptGamma','LepGood', [lambda l : (l.genPartFlav==22)])
mcMatch_seq   = [ isMatchRightCharge, mcMatchId ,mcPromptGamma]


from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetmetHelperRun2 import createJMECorrector


jetmetUncertainties2016APVAll = createJMECorrector(dataYear='UL2016_preVFP', jesUncert="Merged", splitJER=True)
jetmetUncertainties2016All = createJMECorrector(dataYear='UL2016', jesUncert="Merged", splitJER=True)
jetmetUncertainties2017All = createJMECorrector(dataYear='UL2017', jesUncert="Merged", splitJER=True)
jetmetUncertainties2018All = createJMECorrector(dataYear='UL2018', jesUncert="Merged", splitJER=True)

jetmetUncertainties2016APVTotal = createJMECorrector(dataYear='UL2016_preVFP', jesUncert="Total")
jetmetUncertainties2016Total = createJMECorrector(dataYear='UL2016', jesUncert="Total")
jetmetUncertainties2017Total = createJMECorrector(dataYear='UL2017', jesUncert="Total")
jetmetUncertainties2018Total = createJMECorrector(dataYear='UL2018', jesUncert="Total")




def _fires(ev, path):
    if not hasattr(ev,path): return False 
    return getattr( ev,path ) 
    

triggerGroups=dict(
    Trigger_1e={
        2016 : lambda ev : _fires(ev,'HLT_Ele27_WPTight_Gsf') or _fires(ev,'HLT_Ele25_eta2p1_WPTight_Gsf') or _fires(ev,'HLT_Ele27_eta2p1_WPLoose_Gsf'),
        2017 : lambda ev : _fires(ev,'HLT_Ele32_WPTight_Gsf') or _fires(ev,'HLT_Ele35_WPTight_Gsf'),
        2018 : lambda ev : _fires(ev,'HLT_Ele32_WPTight_Gsf'),
    },
    Trigger_1m={
        2016 : lambda ev : _fires(ev,'HLT_IsoMu24') or _fires(ev,'HLT_IsoTkMu24') or _fires(ev,'HLT_IsoMu22_eta2p1') or _fires(ev,'HLT_IsoTkMu22_eta2p1') or _fires(ev,'HLT_IsoMu22') or _fires(ev,'HLT_IsoTkMu22'),
        2017 : lambda ev : _fires(ev,'HLT_IsoMu24') or _fires(ev,'HLT_IsoMu27'),
        2018 : lambda ev : _fires(ev,'HLT_IsoMu24'),
    },
    Trigger_2e={
        2016 : lambda ev : _fires(ev,'HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL_DZ'),
        2017 : lambda ev : _fires(ev,'HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL'),
        2018 : lambda ev : _fires(ev,'HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL'),
    },
    Trigger_2m={
        2016 : lambda ev : _fires(ev,'HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL') or _fires(ev,'HLT_Mu17_TrkIsoVVL_TkMu8_TrkIsoVVL') or  _fires(ev,'HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ') or _fires(ev,'HLT_Mu17_TrkIsoVVL_TkMu8_TrkIsoVVL_DZ'),
        2017 : lambda ev : _fires(ev,'HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass8') or _fires(ev,'HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8'),
        2018 : lambda ev : _fires(ev,'HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8'),
    },
    Trigger_em={
        2016 :  lambda ev : _fires(ev, 'HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL') or _fires(ev,'HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ') \
        or _fires(ev, 'HLT_Mu23_TrkIsoVVL_Ele8_CaloIdL_TrackIdL_IsoVL') or _fires(ev,'HLT_Mu23_TrkIsoVVL_Ele8_CaloIdL_TrackIdL_IsoVL_DZ'),
        2017 :  lambda ev : _fires(ev,'HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL')\
        or _fires(ev,'HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL_DZ')\
        or _fires(ev,'HLT_Mu12_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ')\
        or _fires(ev,'HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ'),
        2018 :  lambda ev : _fires(ev,'HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL')\
        or _fires(ev,'HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ')\
        or _fires(ev,'HLT_Mu12_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ'),
    },
    Trigger_2l={
        2016 : lambda ev : ev.Trigger_1e or ev.Trigger_1m or ev.Trigger_2e or ev.Trigger_2m or ev.Trigger_em,
        2017 : lambda ev : ev.Trigger_1e or ev.Trigger_1m or ev.Trigger_2e or ev.Trigger_2m or ev.Trigger_em,
        2018 : lambda ev : ev.Trigger_1e or ev.Trigger_1m or ev.Trigger_2e or ev.Trigger_2m or ev.Trigger_em,
    },

)


triggerGroups_dict=dict(
    Trigger_1e={
        2016 :  ['HLT_Ele27_WPTight_Gsf' , 'HLT_Ele25_eta2p1_WPTight_Gsf' , 'HLT_Ele27_eta2p1_WPLoose_Gsf'],
        2017 :  ['HLT_Ele32_WPTight_Gsf' , 'HLT_Ele35_WPTight_Gsf'],
        2018 :  ['HLT_Ele32_WPTight_Gsf'],
    },
    Trigger_1m={
        2016 :  ['HLT_IsoMu24' , 'HLT_IsoTkMu24' , 'HLT_IsoMu22_eta2p1' , 'HLT_IsoTkMu22_eta2p1' , 'HLT_IsoMu22' , 'HLT_IsoTkMu22'],
        2017 :  ['HLT_IsoMu24' , 'HLT_IsoMu27'],
        2018 :  ['HLT_IsoMu24'],
    },
    Trigger_2e={
        2016 :  ['HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL_DZ'],
        2017 :  ['HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL'],
        2018 :  ['HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL'],
    },
    Trigger_2m={
        2016 :  ['HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL' , 'HLT_Mu17_TrkIsoVVL_TkMu8_TrkIsoVVL' ,  'HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ' , 'HLT_Mu17_TrkIsoVVL_TkMu8_TrkIsoVVL_DZ'],
        2017 :  ['HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass8' , 'HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8'],
        2018 :  ['HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8'],
    },
    Trigger_em={
        2016 :   ['HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL' , 'HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ', 'HLT_Mu23_TrkIsoVVL_Ele8_CaloIdL_TrackIdL_IsoVL' , 'HLT_Mu23_TrkIsoVVL_Ele8_CaloIdL_TrackIdL_IsoVL_DZ'],
        2017 :   ['HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL', 'HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL_DZ'        , 'HLT_Mu12_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ'        , 'HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ'],
        2018 :   ['HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL', 'HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ'        , 'HLT_Mu12_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ'],
    },
 
)


from CMGTools.VVsemilep.tools.evtTagger import EvtTagger

Trigger_1e   = lambda : EvtTagger('Trigger_1e',[ lambda ev : triggerGroups['Trigger_1e'][ev.year](ev) ])
Trigger_1m   = lambda : EvtTagger('Trigger_1m',[ lambda ev : triggerGroups['Trigger_1m'][ev.year](ev) ])
Trigger_2e   = lambda : EvtTagger('Trigger_2e',[ lambda ev : triggerGroups['Trigger_2e'][ev.year](ev) ])
Trigger_2m   = lambda : EvtTagger('Trigger_2m',[ lambda ev : triggerGroups['Trigger_2m'][ev.year](ev) ])
Trigger_em   = lambda : EvtTagger('Trigger_em',[ lambda ev : triggerGroups['Trigger_em'][ev.year](ev) ])
Trigger_2l   = lambda : EvtTagger('Trigger_2l',[ lambda ev : triggerGroups['Trigger_2l'][ev.year](ev) ])



triggerSequence = [Trigger_1e,Trigger_1m,Trigger_2e,Trigger_2m,Trigger_em,Trigger_2l]

from PhysicsTools.NanoAODTools.postprocessing.modules.btv.btagSFProducer import btagSFProducer


# btagSF2016_dj_allVars = lambda : btagSFProducer("UL2016",'deepjet',collName="JetSel_Recl",storeOutput=False,perJesComponents=True)
# btagSF2016APV_dj_allVars = lambda : btagSFProducer("UL2016APV",'deepjet',collName="JetSel_Recl",storeOutput=False,perJesComponents=True)
# btagSF2017_dj_allVars = lambda : btagSFProducer("UL2017",'deepjet',collName="JetSel_Recl",storeOutput=False,perJesComponents=True)
# btagSF2018_dj_allVars = lambda : btagSFProducer("UL2018",'deepjet',collName="JetSel_Recl",storeOutput=False,perJesComponents=True)

btagSF2016APV_dj = lambda : btagSFProducer("UL2016APV",'deepjet' ,selectedWPs=['shape_corr'], collName="JetSel_Recl")
btagSF2016_dj    = lambda : btagSFProducer("UL2016",'deepjet'    ,selectedWPs=['shape_corr'], collName="JetSel_Recl")
btagSF2017_dj    = lambda : btagSFProducer("UL2017",'deepjet'    ,selectedWPs=['shape_corr'], collName="JetSel_Recl")
btagSF2018_dj    = lambda : btagSFProducer("UL2018",'deepjet'    ,selectedWPs=['shape_corr'], collName="JetSel_Recl")

from CMGTools.TTHAnalysis.tools.nanoAOD.BtagSFs import BtagSFs
bTagSFs = lambda : BtagSFs("JetSel_Recl",
                           corrs = {"" : 1.},
)

# bTagSFs_allvars = lambda : BtagSFs("JetSel_Recl",
#                                    corrs=jecGroups,
#                        )

from CMGTools.VVsemilep.tools.nanoAOD.lepScaleFactors import lepScaleFactors
leptonSFs = lambda : lepScaleFactors()

scaleFactorSequence_2016APV = [btagSF2016APV_dj,bTagSFs] 
scaleFactorSequence_2016    = [btagSF2016_dj,bTagSFs] 
scaleFactorSequence_2017    = [btagSF2017_dj,bTagSFs] 
scaleFactorSequence_2018    = [btagSF2018_dj,bTagSFs]

# scaleFactorSequence_allVars_2016 = [btagSF2016_dj_allVars,bTagSFs_allvars] 
# scaleFactorSequence_allVars_2017 = [btagSF2017_dj_allVars,bTagSFs_allvars] 
# scaleFactorSequence_allVars_2018 = [btagSF2018_dj_allVars,bTagSFs_allvars]



# instructions to friend trees  code 

# 0_jmeUnc_v1
# mc only (per year) 
# jetmetUncertainties2016 
# jetmetUncertainties2017
# jetmetUncertainties2018

# 3_recleaner_v0 (recleaner, also containing mc matching and trigger bits) 
# recleaner_step1,recleaner_step2_mc,mcMatch_seq,higgsDecay,triggerSequence (MC)
# recleaner_step1,recleaner_step2_data,triggerSequence (data)

# 4_leptonSFs_v0 (lepton, trigger and btag scale factors, to run after recleaning) 
# mc only (per year)
# scaleFactorSequence_2016
# scaleFactorSequence_2017
# scaleFactorSequence_2018

# 5_evtVars_v0
