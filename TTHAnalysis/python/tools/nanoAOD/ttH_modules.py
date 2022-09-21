import os
import ROOT 
import copy 
conf = dict(
        muPt = 5, 
        elePt = 7, 
        miniRelIso = 0.4, 
        sip3d = 8, 
        dxy =  0.05, 
        dz = 0.1, 
        eleId = "mvaFall17V2noIso_WPL",
        muoId = "looseId"
)

ttH_skim_cut = ("nMuon + nElectron >= 2 &&" + 
                "Sum$(Muon_pt > {muPt} && Muon_miniPFRelIso_all < {miniRelIso} && Muon_sip3d < {sip3d} && Muon_{muoId} ) +"
                "Sum$(Electron_pt > {muPt} && Electron_miniPFRelIso_all < {miniRelIso} && Electron_sip3d < {sip3d}  && Electron_{eleId} ) >= 2").format(**conf)


muonSelection     = lambda l : abs(l.eta) < 2.4 and l.pt > conf["muPt" ] and l.miniPFRelIso_all < conf["miniRelIso"] and l.sip3d < conf["sip3d"] and abs(l.dxy) < conf["dxy"] and abs(l.dz) < conf["dz"] and getattr(l, conf["muoId"])
electronSelection = lambda l : abs(l.eta) < 2.5 and l.pt > conf["elePt"] and l.miniPFRelIso_all < conf["miniRelIso"] and l.sip3d < conf["sip3d"] and abs(l.dxy) < conf["dxy"] and abs(l.dz) < conf["dz"] and getattr(l, conf["eleId"])

from CMGTools.TTHAnalysis.tools.nanoAOD.ttHPrescalingLepSkimmer import ttHPrescalingLepSkimmer
# NB: do not wrap lepSkim a lambda, as we modify the configuration in the cfg itself 
lepSkim = ttHPrescalingLepSkimmer(5, 
                muonSel = muonSelection, electronSel = electronSelection,
                minLeptonsNoPrescale = 2, # things with less than 2 leptons are rejected irrespectively of the prescale
                minLeptons = 2, requireSameSignPair = True,
                jetSel = lambda j : j.pt > 25 and abs(j.eta) < 2.4 and j.jetId > 0, 
                minJets = 4, minMET = 70)
from PhysicsTools.NanoAODTools.postprocessing.modules.common.collectionMerger import collectionMerger
lepMerge = collectionMerger(input = ["Electron","Muon"], 
                            output = "LepGood", 
                            selector = dict(Muon = muonSelection, Electron = electronSelection))
lepMerge_2 = lambda x : collectionMerger(input = ["Electron","Muon"], 
                            output = "LepGood", 
                            selector = dict(Muon = muonSelection, Electron = electronSelection))

from CMGTools.TTHAnalysis.tools.nanoAOD.ttHLeptonCombMasses import ttHLeptonCombMasses
lepMasses = ttHLeptonCombMasses( [ ("Muon",muonSelection), ("Electron",electronSelection) ], maxLeps = 4)

from CMGTools.TTHAnalysis.tools.nanoAOD.autoPuWeight import autoPuWeight
from CMGTools.TTHAnalysis.tools.nanoAOD.yearTagger import yearTag
from CMGTools.TTHAnalysis.tools.nanoAOD.xsecTagger import xsecTag
from CMGTools.TTHAnalysis.tools.nanoAOD.lepJetBTagAdder import lepJetBTagDeepFlav, lepJetBTagDeepFlavC

from CMGTools.TTHAnalysis.tools.nanoAOD.LepMVAULFriend import lepMVA


ttH_sequence_step1 = [lepSkim, lepMerge, autoPuWeight, yearTag, lepJetBTagDeepFlav, lepMVA, xsecTag, lepMasses]

#==== 
from PhysicsTools.NanoAODTools.postprocessing.tools import deltaR
from CMGTools.TTHAnalysis.tools.nanoAOD.ttHLepQCDFakeRateAnalyzer import ttHLepQCDFakeRateAnalyzer
centralJetSel = lambda j : j.pt > 25 and abs(j.eta) < 2.4 and j.jetId > 0
lepFR = ttHLepQCDFakeRateAnalyzer(jetSel = centralJetSel,
                                  pairSel = lambda pair : deltaR(pair[0].eta, pair[0].phi, pair[1].eta, pair[1].phi) > 0.7,
                                  maxLeptons = 1, requirePair = True)
from CMGTools.TTHAnalysis.tools.nanoAOD.nBJetCounter import nBJetCounter
nBJetDeepFlav25NoRecl = lambda : nBJetCounter("DeepFlav25", "btagDeepFlavB", centralJetSel)

ttH_sequence_step1_FR = [m for m in ttH_sequence_step1 if m != lepSkim] + [ lepFR, nBJetDeepFlav25NoRecl() ]
ttH_skim_cut_FR = ("nMuon + nElectron >= 1 && nJet >= 1 && Sum$(Jet_pt > 25 && abs(Jet_eta)<2.4) >= 1 &&" + 
       "Sum$(Muon_pt > {muPt} && Muon_miniPFRelIso_all < {miniRelIso} && Muon_sip3d < {sip3d}) +"
       "Sum$(Electron_pt > {muPt} && Electron_miniPFRelIso_all < {miniRelIso} && Electron_sip3d < {sip3d}) ").format(**conf)


#==== items below are normally run as friends ====

def ttH_idEmu_cuts_E3(lep):
    if (abs(lep.pdgId)!=11): return True
    if (lep.hoe>=(0.10-0.00*(abs(lep.eta+lep.deltaEtaSC)>1.479))): return False
    if (lep.eInvMinusPInv<=-0.04): return False
    if (lep.sieie>=(0.011+0.019*(abs(lep.eta+lep.deltaEtaSC)>1.479))): return False
    return True

def conept_TTH(lep):
    if (abs(lep.pdgId)!=11 and abs(lep.pdgId)!=13): return lep.pt
    if (abs(lep.pdgId)==13 and lep.mediumId>0 and lep.mvaTTHUL > 0.85) or (abs(lep.pdgId) == 11 and lep.mvaTTHUL > 0.90): return lep.pt
    else: return 0.90 * lep.pt * (1 + lep.jetRelIso)

def smoothBFlav(jetpt,ptmin,ptmax,year, subera,scale_loose=1.0):
    wploose = ([0.0508, 0.0480], [0.0532], [0.0490])
    wpmedium = ([0.2598,0.2489], [0.3040], [0.2783])
    x = min(max(0.0, jetpt - ptmin)/(ptmax-ptmin), 1.0)
    return x*wploose[year-2016][subera]*scale_loose + (1-x)*wpmedium[year-2016][subera]


def clean_and_FO_selection_TTH(lep,year, subera):
    bTagCut = ([0.2598,0.2489], [0.3040], [0.2783])[year-2016][subera]
    return lep.conept>10 and lep.jetBTagDeepFlav<bTagCut and (abs(lep.pdgId)!=11 or (ttH_idEmu_cuts_E3(lep) )) \
        and (lep.mvaTTHUL>(0.85 if abs(lep.pdgId)==13 else 0.90) or \
             (abs(lep.pdgId)==13 and lep.jetBTagDeepFlav< smoothBFlav(0.9*lep.pt*(1+lep.jetRelIso), 20, 45, year, subera) and lep.jetRelIso < 0.50) or \
             (abs(lep.pdgId)==11 and lep.mvaFall17V2noIso_WP90 and lep.jetBTagDeepFlav< smoothBFlav(0.9*lep.pt*(1+lep.jetRelIso), 20, 45, year, subera)and lep.jetRelIso < 1.0 ))

tightLeptonSel = lambda lep,year,era : clean_and_FO_selection_TTH(lep,year,era) and (abs(lep.pdgId)!=13 or lep.mediumId>0) and lep.mvaTTHUL > (0.85 if abs(lep.pdgId)==13 else 0.90)

foTauSel = lambda tau: tau.pt > 20 and abs(tau.eta)<2.3 and abs(tau.dxy) < 1000 and abs(tau.dz) < 0.2  and (int(tau.idDeepTau2017v2p1VSjet)>>1 & 1) # VVLoose WP
tightTauSel = lambda tau: (int(tau.idDeepTau2017v2p1VSjet)>>2 & 1) # VLoose WP
jevariations=['jes%s'%x for x in ["FlavorQCD", "RelativeBal", "HF", "BBEC1", "EC2", "Absolute", "BBEC1_year", "EC2_year", "Absolute_year", "HF_year", "RelativeSample_year" ]] + ['jer%d'%j for j in range(6)]
from CMGTools.TTHAnalysis.tools.combinedObjectTaggerForCleaning import CombinedObjectTaggerForCleaning
from CMGTools.TTHAnalysis.tools.nanoAOD.fastCombinedObjectRecleaner import fastCombinedObjectRecleaner
recleaner_step1 = lambda : CombinedObjectTaggerForCleaning("InternalRecl",
                                                           looseLeptonSel = lambda lep : lep.miniPFRelIso_all < 0.4 and lep.sip3d < 8 and (abs(lep.pdgId)!=11 or lep.lostHits<=1) and (abs(lep.pdgId)!=13 or lep.looseId),
                                                           cleaningLeptonSel = clean_and_FO_selection_TTH,
                                                           FOLeptonSel = clean_and_FO_selection_TTH,
                                                           tightLeptonSel = tightLeptonSel,
                                                           FOTauSel = foTauSel,
                                                           tightTauSel = tightTauSel,
                                                           selectJet = lambda jet: jet.jetId > 0, # pt and eta cuts are (hard)coded in the step2 
                                                           coneptdef = lambda lep: conept_TTH(lep),
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
tauVeto_2lss_1tau  = lambda t : t.idDeepTau2017v2p1VSjet & 16
tauTight_2lss_1tau = lambda t : tauFOs(t) and t.idDeepTau2017v2p1VSjet & 4
countTaus_veto             = lambda : ObjTagger('Tight'            ,'TauSel_Recl', [lambda t : t.idDeepTau2017v2p1VSjet&4]) # to veto in tauless categories
countTaus_FO               = lambda : ObjTagger('FO'               ,'TauSel_Recl', [tauFOs]                               ) # actual FO (the FO above is used for jet cleaning, and corresponds to the loose)
countTaus_2lss1tau_Veto    = lambda : ObjTagger('2lss1tau_Veto'    ,'TauSel_Recl', [tauVeto_2lss_1tau]                    ) # veto ID for 2lss1tau category 
countTaus_2lss1tau_Tight   = lambda : ObjTagger('2lss1tau_Tight'   ,'TauSel_Recl', [tauTight_2lss_1tau]                   ) # tight ID for 2lss1tau category 
from CMGTools.TTHAnalysis.tools.nanoAOD.tauMatcher import tauScaleFactors


countTaus = [countTaus_veto,countTaus_FO,countTaus_2lss1tau_Veto,countTaus_2lss1tau_Tight]



from CMGTools.TTHAnalysis.tools.eventVars_2lss import EventVars2LSS
eventVars               = lambda : EventVars2LSS('','Recl', tauTight_2lss_1tau=tauTight_2lss_1tau)
eventVars_allvariations = lambda : EventVars2LSS('','Recl',variations = jevariations, tauTight_2lss_1tau=tauTight_2lss_1tau)




from CMGTools.TTHAnalysis.tools.hjDummCalc import HjDummyCalc
hjDummy = lambda : HjDummyCalc(variations  = [ 'jes%s'%v for v in jecGroups] + ['jer%s'%x for x in ['barrel','endcap1','endcap2highpt','endcap2lowpt' ,'forwardhighpt','forwardlowpt']  ]  + ['HEM'])

from CMGTools.TTHAnalysis.tools.objTagger import ObjTagger
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
    Trigger_3e={
        2016 : lambda ev : _fires(ev,'HLT_Ele16_Ele12_Ele8_CaloIdL_TrackIdL'),
        2017 : lambda ev : _fires(ev,'HLT_Ele16_Ele12_Ele8_CaloIdL_TrackIdL'),
        2018 : lambda ev : _fires(ev,'HLT_Ele16_Ele12_Ele8_CaloIdL_TrackIdL'), # prescaled in the two years according to https://twiki.cern.ch/twiki/bin/view/CMS/EgHLTRunIISummary#2018
    },
    Trigger_3m={
        2016 : lambda ev : _fires(ev,'HLT_TripleMu_12_10_5'),
        2017 : lambda ev : _fires(ev,'HLT_TripleMu_12_10_5'),
        2018 : lambda ev : _fires(ev,'HLT_TripleMu_12_10_5'),
    },
    Trigger_mee={
        2016 : lambda ev : _fires(ev,'HLT_Mu8_DiEle12_CaloIdL_TrackIdL'),
        2017 : lambda ev : _fires(ev,'HLT_Mu8_DiEle12_CaloIdL_TrackIdL'),
        2018 : lambda ev : _fires(ev,'HLT_Mu8_DiEle12_CaloIdL_TrackIdL'),
    },
    Trigger_mme={
        2016 : lambda ev : _fires(ev,'HLT_DiMu9_Ele9_CaloIdL_TrackIdL'),
        2017 : lambda ev : _fires(ev,'HLT_DiMu9_Ele9_CaloIdL_TrackIdL_DZ'),
        2018 : lambda ev : _fires(ev,'HLT_DiMu9_Ele9_CaloIdL_TrackIdL_DZ'),
    },
    Trigger_2lss={
        2016 : lambda ev : ev.Trigger_1e or ev.Trigger_1m or ev.Trigger_2e or ev.Trigger_2m or ev.Trigger_em,
        2017 : lambda ev : ev.Trigger_1e or ev.Trigger_1m or ev.Trigger_2e or ev.Trigger_2m or ev.Trigger_em,
        2018 : lambda ev : ev.Trigger_1e or ev.Trigger_1m or ev.Trigger_2e or ev.Trigger_2m or ev.Trigger_em,
    },
    Trigger_3l={
        2016 : lambda ev : ev.Trigger_2lss or ev.Trigger_3e or ev.Trigger_3m or ev.Trigger_mee or ev.Trigger_mme,
        2017 : lambda ev : ev.Trigger_2lss or ev.Trigger_3e or ev.Trigger_3m or ev.Trigger_mee or ev.Trigger_mme,
        2018 : lambda ev : ev.Trigger_2lss or ev.Trigger_3e or ev.Trigger_3m or ev.Trigger_mee or ev.Trigger_mme,
    },
    Trigger_MET={
        2016 : lambda ev : _fires(ev,'HLT_PFMET120_PFMHT120_IDTight'),
        2017 : lambda ev : _fires(ev,'HLT_PFMET120_PFMHT120_IDTight'),
        2018 : lambda ev : _fires(ev,'HLT_PFMET120_PFMHT120_IDTight'),
    }
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
    Trigger_3e={
        2016 :  ['HLT_Ele16_Ele12_Ele8_CaloIdL_TrackIdL'],
        2017 :  ['HLT_Ele16_Ele12_Ele8_CaloIdL_TrackIdL'],
        2018 :  ['HLT_Ele16_Ele12_Ele8_CaloIdL_TrackIdL'], # prescaled in the two years according to https://twiki.cern.ch/twiki/bin/view/CMS/EgHLTRunIISummary#2018
    },
    Trigger_3m={
        2016 :  ['HLT_TripleMu_12_10_5'],
        2017 :  ['HLT_TripleMu_12_10_5'],
        2018 :  ['HLT_TripleMu_12_10_5'],
    },
    Trigger_mee={
        2016 :  ['HLT_Mu8_DiEle12_CaloIdL_TrackIdL'],
        2017 :  ['HLT_Mu8_DiEle12_CaloIdL_TrackIdL'],
        2018 :  ['HLT_Mu8_DiEle12_CaloIdL_TrackIdL'],
    },
    Trigger_mme={
        2016 :  ['HLT_DiMu9_Ele9_CaloIdL_TrackIdL'   ],
        2017 :  ['HLT_DiMu9_Ele9_CaloIdL_TrackIdL_DZ'],
        2018 :  ['HLT_DiMu9_Ele9_CaloIdL_TrackIdL_DZ'],
    },
    Trigger_MET={ 
        2016 : ["HLT_PFMET120_PFMHT120_IDTight"],
        2017 : ["HLT_PFMET120_PFMHT120_IDTight"],
        2018 : ["HLT_PFMET120_PFMHT120_IDTight"],
    }
)


from CMGTools.TTHAnalysis.tools.evtTagger import EvtTagger

Trigger_1e   = lambda : EvtTagger('Trigger_1e',[ lambda ev : triggerGroups['Trigger_1e'][ev.year](ev) ])
Trigger_1m   = lambda : EvtTagger('Trigger_1m',[ lambda ev : triggerGroups['Trigger_1m'][ev.year](ev) ])
Trigger_2e   = lambda : EvtTagger('Trigger_2e',[ lambda ev : triggerGroups['Trigger_2e'][ev.year](ev) ])
Trigger_2m   = lambda : EvtTagger('Trigger_2m',[ lambda ev : triggerGroups['Trigger_2m'][ev.year](ev) ])
Trigger_em   = lambda : EvtTagger('Trigger_em',[ lambda ev : triggerGroups['Trigger_em'][ev.year](ev) ])
Trigger_3e   = lambda : EvtTagger('Trigger_3e',[ lambda ev : triggerGroups['Trigger_3e'][ev.year](ev) ])
Trigger_3m   = lambda : EvtTagger('Trigger_3m',[ lambda ev : triggerGroups['Trigger_3m'][ev.year](ev) ])
Trigger_mee  = lambda : EvtTagger('Trigger_mee',[ lambda ev : triggerGroups['Trigger_mee'][ev.year](ev) ])
Trigger_mme  = lambda : EvtTagger('Trigger_mme',[ lambda ev : triggerGroups['Trigger_mme'][ev.year](ev) ])
Trigger_2lss = lambda : EvtTagger('Trigger_2lss',[ lambda ev : triggerGroups['Trigger_2lss'][ev.year](ev) ])
Trigger_3l   = lambda : EvtTagger('Trigger_3l',[ lambda ev : triggerGroups['Trigger_3l'][ev.year](ev) ])
Trigger_MET  = lambda : EvtTagger('Trigger_MET',[ lambda ev : triggerGroups['Trigger_MET'][ev.year](ev) ])

triggerSequence = [Trigger_1e,Trigger_1m,Trigger_2e,Trigger_2m,Trigger_em,Trigger_3e,Trigger_3m,Trigger_mee,Trigger_mme,Trigger_2lss,Trigger_3l]


from CMGTools.TTHAnalysis.tools.BDT_eventReco_cpp import BDT_eventReco

BDThttTT_Hj = lambda : BDT_eventReco(os.environ["CMSSW_BASE"]+'/src/CMGTools/TTHAnalysis/data/kinMVA/tth/TMVAClassification_bloose_BDTG.weights.xml',
                                     os.environ["CMSSW_BASE"]+'/src/CMGTools/TTHAnalysis/data/kinMVA/tth/TMVAClassification_btight_BDTG.weights.xml',
                                     os.environ["CMSSW_BASE"]+'/src/CMGTools/TTHAnalysis/data/kinMVA/tth/Hjtagger_legacy_xgboost_v1.weights.xml',
                                     os.environ["CMSSW_BASE"]+'/src/CMGTools/TTHAnalysis/data/kinMVA/tth/Hjj_csv_BDTG.weights.xml',
                                     os.environ["CMSSW_BASE"]+'/src/CMGTools/TTHAnalysis/data/kinMVA/tth/resTop_xgb_csv_order_deepCTag.xml.gz',
                                     os.environ["CMSSW_BASE"]+'/src/CMGTools/TTHAnalysis/data/kinMVA/tth/HTT_HadTopTagger_2017_nomasscut_nvar17_resolved.xml',
                                     os.environ["CMSSW_BASE"]+'/src/CMGTools/TTHAnalysis/data/kinMVA/tth/TF_jets_kinfit_httTT.root',
                                     algostring = 'k_httTT_Hj',
                                     selection = [
                                         lambda leps,jets,event : len(leps)>=2,
                                         lambda leps,jets,event : leps[0].conePt>20 and leps[1].conePt>10,
                                     ]
)

BDThttTT_allvariations =  lambda : BDT_eventReco(os.environ["CMSSW_BASE"]+'/src/CMGTools/TTHAnalysis/data/kinMVA/tth/TMVAClassification_bloose_BDTG.weights.xml',
                                                 os.environ["CMSSW_BASE"]+'/src/CMGTools/TTHAnalysis/data/kinMVA/tth/TMVAClassification_btight_BDTG.weights.xml',
                                                 os.environ["CMSSW_BASE"]+'/src/CMGTools/TTHAnalysis/data/kinMVA/tth/Hjtagger_legacy_xgboost_v1.weights.xml',
                                                 os.environ["CMSSW_BASE"]+'/src/CMGTools/TTHAnalysis/data/kinMVA/tth/Hjj_csv_BDTG.weights.xml',
                                                 os.environ["CMSSW_BASE"]+'/src/CMGTools/TTHAnalysis/data/kinMVA/tth/resTop_xgb_csv_order_deepCTag.xml.gz',
                                                 os.environ["CMSSW_BASE"]+'/src/CMGTools/TTHAnalysis/data/kinMVA/tth/HTT_HadTopTagger_2017_nomasscut_nvar17_resolved.xml',
                                                 os.environ["CMSSW_BASE"]+'/src/CMGTools/TTHAnalysis/data/kinMVA/tth/TF_jets_kinfit_httTT.root',
                                                 algostring = 'k_httTT_Hj',
                                                 selection = [
                                                     lambda leps,jets,event : len(leps)>=2,
                                                          lambda leps,jets,event : leps[0].conePt>20 and leps[1].conePt>10,
                                                 ],
                                                 variations = jevariations,
                                             )

from CMGTools.TTHAnalysis.tools.finalMVA_DNN import finalMVA_DNN
finalMVA = lambda : finalMVA_DNN() # use this for data
finalMVA_allVars = lambda : finalMVA_DNN( variations = jevariations)
finalMVA_input = lambda : finalMVA_DNN(doSystJEC=False, fillInputs=True) # use this for training

from CMGTools.TTHAnalysis.tools.finalMVA_DNN_3l import finalMVA_DNN_3l
finalMVA3L = lambda : finalMVA_DNN_3l() # use this for data
finalMVA3L_allVars = lambda : finalMVA_DNN_3l(variations = jevariations )

from CMGTools.TTHAnalysis.tools.finalMVA_DNN_2lss1tau import finalMVA_DNN_2lss1tau
finalMVA2lss1tau = lambda : finalMVA_DNN_2lss1tau() # use this for data
finalMVA2lss1tau_allVars = lambda : finalMVA_DNN_2lss1tau(variations = [ 'jes%s'%v for v in jecGroups] + ['jer%s'%x for x in ['barrel','endcap1','endcap2highpt','endcap2lowpt' ,'forwardhighpt','forwardlowpt']  ]  + ['HEM'])

from CMGTools.TTHAnalysis.tools.nanoAOD.finalMVA_4l import FinalMVA_4L
finalMVA_4l = lambda : FinalMVA_4L()


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

from CMGTools.TTHAnalysis.tools.nanoAOD.lepScaleFactors import lepScaleFactors
leptonSFs = lambda : lepScaleFactors()

scaleFactorSequence_2016APV = [btagSF2016APV_dj,bTagSFs] 
scaleFactorSequence_2016    = [btagSF2016_dj,bTagSFs] 
scaleFactorSequence_2017    = [btagSF2017_dj,bTagSFs] 
scaleFactorSequence_2018    = [btagSF2018_dj,bTagSFs]

# scaleFactorSequence_allVars_2016 = [btagSF2016_dj_allVars,bTagSFs_allvars] 
# scaleFactorSequence_allVars_2017 = [btagSF2017_dj_allVars,bTagSFs_allvars] 
# scaleFactorSequence_allVars_2018 = [btagSF2018_dj_allVars,bTagSFs_allvars]


from CMGTools.TTHAnalysis.tools.nanoAOD.higgsDecayFinder import higgsDecayFinder
higgsDecay = lambda : higgsDecayFinder()

from CMGTools.TTHAnalysis.tools.nanoAOD.VHsplitter import VHsplitter
vhsplitter = lambda : VHsplitter()

# from CMGTools.TTHAnalysis.tools.synchTools import SynchTuples
# synchTuples = lambda : SynchTuples()


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
from CMGTools.TTHAnalysis.tools.nanoAOD.ttH_gen_reco import ttH_gen_reco
#
#from CMGTools.TTHAnalysis.tools.topRecoSemiLept import TopRecoSemiLept
#topRecoModule = lambda : TopRecoSemiLept(constraints=['kWHadMass','kWLepMass','kTopLepMass','kTopHadMass'])

from CMGTools.TTHAnalysis.tools.nanoAOD.LepMVAULFriend import lepMVA_2016, lepMVA_2016APV, lepMVA_2017, lepMVA_2018

# TTH differential analysis
from CMGTools.TTHAnalysis.tools.higgsDiffGenTTH import higgsDiffGenTTH
from CMGTools.TTHAnalysis.tools.higgsDiffRecoTTH import higgsDiffRecoTTH, higgsDiffRecoTTH_noWmassConstraint
from CMGTools.TTHAnalysis.tools.higgsDiffCompTTH import higgsDiffCompTTH, higgsDiffCompTTH_noWmassConstraint
from CMGTools.TTHAnalysis.tools.higgsDiffRegressionTTH import higgsDiffRegressionTTH

from CMGTools.TTHAnalysis.tools.nanoAOD.ttH_genericTreeVarForSR import ttH_genericTreeVarForSR

ttH_2lss_tree = lambda  : ttH_genericTreeVarForSR(2, 
                                               ['len(leps) < 2                                          ',
                                                'leps[0].pt < 25 or leps[1].pt < 15                     ',
                                                'event.nLepTight_Recl > 2                               ',
                                                'leps[0].pdgId*leps[1].pdgId < 0                        ',
                                                'abs(event.mZ1_Recl-91.2)<10                            ',
                                                'leps[0].genPartFlav != 1 and leps[0].genPartFlav != 15 ',
                                                'leps[1].genPartFlav != 1 and leps[1].genPartFlav != 15 ',
                                                'event.nTauSel_Recl_Tight > 0                           ',
                                                'not ((event.nJet25_Recl>=3 and (event.nBJetLoose25_Recl >= 2 or event.nBJetMedium25_Recl >= 1)) or (event.nBJetMedium25_Recl >= 1 and (event.nJet25_Recl+event.nFwdJet_Recl-event.nBJetLoose25_Recl) > 0)) ',
])

ttH_2lss1tau_tree = lambda : ttH_genericTreeVarForSR(2, 
                                                   ['len(leps) < 2                                          ',
                                                    'leps[0].pt < 25 or leps[1].pt < 15                     ',
                                                    'leps[1].conePt < (15 if abs(leps[1].pdgId)==11 else 10)',
                                                    'leps[1].pdgId*leps[0].pdgId < 0',
                                                    'abs(event.mZ1_Recl-91.2)<10',
                                                    'event.nLepTight_Recl > 2 ',
                                                    'event.nTauSel_Recl_2lss1tau_Tight < 1', 
                                                    'leps[0].genPartFlav != 1 and leps[0].genPartFlav != 15 ',
                                                    'leps[1].genPartFlav != 1 and leps[1].genPartFlav != 15 ',
                                                    'not ((event.nJet25_Recl>=3 and (event.nBJetLoose25_Recl >= 2 or event.nBJetMedium25_Recl >= 1)) or (event.nBJetMedium25_Recl >= 1 and (event.nJet25_Recl+event.nFwdJet_Recl-event.nBJetLoose25_Recl) > 0)) ',
                                                    '''thetau.charge*leps[0].pdgId<0'''
                                                ],
                                                     execute=['''taus = [ t for t in Collection(event,'TauSel_Recl')]''',
                                                              '''thetau=taus[int(event.Tau_tight2lss1tau_idx)] if event.Tau_tight2lss1tau_idx > -1 else None;'''],
                                                     extraVars=[('Tau_pt','thetau.pt'), ('Tau_eta','thetau.eta'), ('Tau_phi','thetau.phi')], is2lss1tau=True)

ttH_3l_tree = lambda : ttH_genericTreeVarForSR(3, 
                                             ['len(leps) < 3                                          ',
                                              'leps[0].pt < 25 or leps[1].pt < 15 or leps[2].pt<10    ',
                                              'event.nLepTight_Recl > 3                               ',
                                              'abs(event.mZ1_Recl-91.2)<10                            ',
                                              'leps[0].genPartFlav != 1 and leps[0].genPartFlav != 15 ',
                                              'leps[1].genPartFlav != 1 and leps[1].genPartFlav != 15 ',
                                              'leps[2].genPartFlav != 1 and leps[2].genPartFlav != 15 ',
                                              'event.nTauSel_Recl_Tight > 0                           ',
                                              'not  (event.nJet25_Recl>=2 and (event.nBJetLoose25_Recl >= 2 or event.nBJetMedium25_Recl >= 1) and (event.nJet25_Recl >= 4 or event.MET_pt*0.6 + event.mhtJet25_Recl*0.4 > 30 + 15*(event.mZ1_Recl > 0)) or (event.nBJetMedium25_Recl >= 1 and (event.nJet25_Recl+event.nFwdJet_Recl-event.nBJetLoose25_Recl) > 0))'
])


from CMGTools.TTHAnalysis.tools.nanoAOD.mvaCP_2lss import mvaCP_2lss
MVAcp_2lss = lambda : mvaCP_2lss(variations = []) # for data
MVAcp_2lss_allvars = lambda : mvaCP_2lss(variations = [ 'jes%s'%v for v in jecGroups] + ['jer%s'%x for x in ['barrel','endcap1','endcap2highpt','endcap2lowpt' ,'forwardhighpt','forwardlowpt']  ]  + ['HEM'])

from CMGTools.TTHAnalysis.tools.nanoAOD.mvaCP_3l import mvaCP_3l
MVAcp_3l = lambda : mvaCP_3l(variations = []) # for data
MVAcp_3l_allvars = lambda : mvaCP_3l(variations = [ 'jes%s'%v for v in jecGroups] + ['jer%s'%x for x in ['barrel','endcap1','endcap2highpt','endcap2lowpt' ,'forwardhighpt','forwardlowpt']  ]  + ['HEM'])

from CMGTools.TTHAnalysis.tools.nanoAOD.mvaCP_2lss1tau import mvaCP_2lss1tau
MVAcp_2lss1tau = lambda : mvaCP_2lss1tau(variations = []) # for data
MVAcp_2lss1tau_allvars = lambda : mvaCP_2lss1tau(variations = [ 'jes%s'%v for v in jecGroups] + ['jer%s'%x for x in ['barrel','endcap1','endcap2highpt','endcap2lowpt' ,'forwardhighpt','forwardlowpt']  ]  + ['HEM'])


from CMGTools.TTHAnalysis.tools.nanoAOD.selectParticleAndPartonInfo import selectParticleAndPartonInfo
ttW_diff_gen_info = lambda : selectParticleAndPartonInfo( dresslepSel_ = lambda x : x.pt>20 and abs(x.eta) < 2.4,
                                                          dressjetSel_ = lambda x : x.pt>25 and abs(x.eta) < 2.4 ) 
                                               
