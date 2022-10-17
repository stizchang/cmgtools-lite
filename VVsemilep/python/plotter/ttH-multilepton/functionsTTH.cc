#include "TFile.h"
#include "TH2.h"
#include "TF1.h"
#include "TH2Poly.h"
#include "TGraphAsymmErrors.h"
#include "TRandom3.h"

#include <iostream>
#include <vector>
#include <algorithm>
#include <numeric>
#include <map>

float ttH_MVAto1D_6_2lss_Marco (float kinMVA_2lss_ttbar, float kinMVA_2lss_ttV){

  return 2*((kinMVA_2lss_ttbar>=-0.2)+(kinMVA_2lss_ttbar>=0.3))+(kinMVA_2lss_ttV>=-0.1)+1;

}
float ttH_MVAto1D_3_3l_Marco (float kinMVA_3l_ttbar, float kinMVA_3l_ttV){

  if (kinMVA_3l_ttbar<0.3 && kinMVA_3l_ttV<-0.1) return 1;
  else if (kinMVA_3l_ttbar>=0.3 && kinMVA_3l_ttV>=-0.1) return 3;
  else return 2;

}

#include "binning_2d_thresholds.h"
float ttH_MVAto1D_7_2lss_Marco (float kinMVA_2lss_ttbar, float kinMVA_2lss_ttV){

//________________
//|   |   |   | 7 |
//|   |   | 4 |___|
//| 1 | 2 |___| 6 |
//|   |   |   |___|
//|   |   | 3 | 5 |
//|___|___|___|___|
//

  if (kinMVA_2lss_ttbar<cuts_2lss_ttbar0) return 1;
  else if (kinMVA_2lss_ttbar<cuts_2lss_ttbar1) return 2;
  else if (kinMVA_2lss_ttbar<cuts_2lss_ttbar2) return 3+(kinMVA_2lss_ttV>=cuts_2lss_ttV0);
  else return 5+(kinMVA_2lss_ttV>=cuts_2lss_ttV1)+(kinMVA_2lss_ttV>=cuts_2lss_ttV2);

}
float ttH_MVAto1D_5_3l_Marco (float kinMVA_3l_ttbar, float kinMVA_3l_ttV){

  int reg = 2*((kinMVA_3l_ttbar>=cuts_3l_ttbar1)+(kinMVA_3l_ttbar>=cuts_3l_ttbar2))+(kinMVA_3l_ttV>=cuts_3l_ttV1)+1;
  if (reg==2) reg=1;
  if (reg>2) reg = reg-1;
  return reg;

}


float newBinning(float x, float y){
  float r =  4*((y>-0.16)+(y>0.28))+(x>-0.22)+(x>0.09)+(x>0.42)+1;
  if (r==9) r-=4;
  if (r>9) r-=1;
  return r;
}

//#include "GetBinning.C"


float ttH_MVAto1D_6_flex (float kinMVA_2lss_ttbar, float kinMVA_2lss_ttV, int pdg1, int pdg2, float ttVcut, float ttcut1, float ttcut2){

  return 2*((kinMVA_2lss_ttbar>=ttcut1)+(kinMVA_2lss_ttbar>=ttcut2)) + (kinMVA_2lss_ttV>=ttVcut)+1;

}

float returnInputX(float x, float y) {return x;}

float mvaCat(float ttH, float rest, float ttW, float thq){
  float ret = 0; 
  if (ttH > rest && ttH > ttW && ttH > thq){
    ret =  ttH;
  }
  if (ttW > ttH && ttW > rest && ttW > thq){
    ret= ttW+1;
  }
  if (thq > ttH && thq > ttW && thq > rest){
    ret= thq+2;
  }
  if (rest > ttH && rest > thq && rest > ttW){
    ret= rest+3;
  }
  return ret;

}

int ttH_catIndex_2lss(int LepGood1_pdgId, int LepGood2_pdgId, float tth, float ttw, float thq, float rest)
{

//2lss_ee_ttH
//2lss_ee_rest
//2lss_ee_ttw
//2lss_ee_thq
//2lss_em_ttH
//2lss_em_rest
//2lss_em_ttw
//2lss_em_thq
//2lss_mm_ttH
//2lss_mm_rest
//2lss_mm_ttw
//2lss_mm_thq  
  int flch = 0;
  int procch = 0;

  if (abs(LepGood1_pdgId)+abs(LepGood2_pdgId) == 22)
    flch = 0;
  else if (abs(LepGood1_pdgId)+abs(LepGood2_pdgId) == 24)
    flch = 1;
  else if (abs(LepGood1_pdgId)+abs(LepGood2_pdgId) == 26)
    flch = 2;
  else
    cout << "[2lss]: It shouldnt be here. pdgids are " << abs(LepGood1_pdgId) << " " << abs(LepGood2_pdgId)  << endl;

  if (tth >= ttw && tth >= thq && tth >= rest)
    procch = 0;
  else if (rest >= tth && rest >= ttw && rest >= thq)
    procch = 1;
  else if (ttw >= tth && ttw >= rest && ttw >= thq)
    procch = 2;
  else if (thq >= tth && thq >= rest && thq >= ttw)
    procch = 3;
  else 
    cout << "[2lss]: It shouldnt be here. DNN scores are " << tth << " " << rest << " " << ttw << " " << thq << endl;
      
  return flch*4+procch+1;

}


std::vector<TString> bin2lsslabels = {
  "ee_ttHnode","ee_Restnode","ee_ttWnode","ee_tHQnode",
  "em_ttHnode","em_Restnode","em_ttWnode","em_tHQnode",
  "mm_ttHnode","mm_Restnode","mm_ttWnode","mm_tHQnode"
};
TFile* f2lssBins;

std::map<TString,int> bins2lss = {{"ee_ttHnode",5},{"ee_Restnode",8},{"ee_ttWnode",6},{"ee_tHQnode",4},
				  {"em_ttHnode",13},{"em_Restnode",8},{"em_ttWnode",19},{"em_tHQnode",11},
				  {"mm_ttHnode",13},{"mm_Restnode",11},{"mm_ttWnode",15},{"mm_tHQnode",7}};
std::map<TString, TH1F*> binHistos2lss;
std::map<TString, int> bins2lsscumul;


std::map<TString, int> bins2lsscumul_cp;
std::map<TString,int> bins2lss_withcp = {{"ee_ttHnode",5*2},{"ee_Restnode",8},{"ee_ttWnode",6},{"ee_tHQnode",4},
					 {"em_ttHnode",13*4},{"em_Restnode",8},{"em_ttWnode",19},{"em_tHQnode",11},
					 {"mm_ttHnode",13*4},{"mm_Restnode",11},{"mm_ttWnode",15},{"mm_tHQnode",7}};


int ttH_catIndex_2lss_MVA_CP(int LepGood1_pdgId, int LepGood2_pdgId, float tth, float ttw, float thq, float rest, float cp)
{
  if (!f2lssBins){
    int offset = 0;
    f2lssBins = TFile::Open("../../data/kinMVA/DNNBin_v3_xmas.root");
    for (auto & la : bin2lsslabels){
      int bins = bins2lss[la];
      binHistos2lss[la] = (TH1F*) f2lssBins->Get(Form("%s_2018_Map_nBin%d", la.Data(), bins));
      bins2lsscumul_cp[la] = offset;
      offset += bins2lss_withcp[la];
    }
  }
  
  int idx = ttH_catIndex_2lss(LepGood1_pdgId, LepGood2_pdgId, tth,ttw, thq,rest); 
  TString binLabel = bin2lsslabels[idx-1];
  float mvavar = 0;
  int cpidx=0; int cpbins=1;
  if (tth >= ttw && tth >= thq && tth >= rest){
    mvavar = tth;
    if (abs(LepGood1_pdgId) + abs(LepGood2_pdgId) == 22){
      cpbins=2;
      if (cp < 0.165208) cpidx=0;
      else cpidx=1;
    }
    else{
      cpbins=4;
      if      (cp < 0.128845)  cpidx = 0;
      else if (cp < 0.165208)  cpidx = 1;
      else if (cp < 0.2208)    cpidx = 2;
      else                     cpidx = 3;
    }
  }
  else if (rest >= tth && rest >= ttw && rest >= thq)
    mvavar =rest;
  else if (ttw >= tth && ttw >= rest && ttw >= thq)
    mvavar = ttw;
  else if (thq >= tth && thq >= rest && thq >= ttw)
    mvavar = thq;
  else 
    cout << "It shouldnt be here" << endl;
  return binHistos2lss[binLabel]->FindBin( mvavar ) + binHistos2lss[binLabel]->GetNbinsX()*cpidx + bins2lsscumul_cp[binLabel];

}

int ttH_catIndex_2lss_MVA_CP_ttH(int LepGood1_pdgId, int LepGood2_pdgId, float tth, float ttw, float thq, float rest, float cp)
{
  int b;
  b = -99;
  int bin = ttH_catIndex_2lss_MVA_CP(LepGood1_pdgId, LepGood2_pdgId, tth,  ttw, thq, rest, cp);
  if (bin <=10) b = bin;
  else if (bin>=29 && bin<=80) b =bin-18;
  else if (bin>=119 && bin<=170) b = bin-(18+38);
  else 
    b=-99;
  return b;
}

int ttH_catIndex_2lss_MVA_CP_Rest(int LepGood1_pdgId, int LepGood2_pdgId, float tth, float ttw, float thq, float rest, float cp)
{
  int b;
  b = -99;
  int bin = ttH_catIndex_2lss_MVA_CP(LepGood1_pdgId, LepGood2_pdgId, tth,  ttw, thq, rest, cp);
  if (bin >10 && bin <=18) b = bin-10;
  else if (bin>80 && bin<=88) b =bin-62-10;
  else if (bin>170 && bin<=181) b = bin-(62+82+10);
  else 
    b=-99;
  return b;
}
//fixme
int ttH_catIndex_2lss_MVA_CP_ttW(int LepGood1_pdgId, int LepGood2_pdgId, float tth, float ttw, float thq, float rest, float cp)
{
  int b;
  b = -99;
  int bin = ttH_catIndex_2lss_MVA_CP(LepGood1_pdgId, LepGood2_pdgId, tth,  ttw, thq, rest, cp);
  if (bin >=19 && bin <25) b = bin-10-8;
  else if (bin>88 && bin<=107) b =bin-64-10-8;
  else if (bin>=181 && bin<=196) b = bin-(74+64+10+8);
  else 
    b=-99;
  return b;
}
int ttH_catIndex_2lss_MVA_CP_tH(int LepGood1_pdgId, int LepGood2_pdgId, float tth, float ttw, float thq, float rest, float cp)
{
  int b;
  b = -99;
  int bin = ttH_catIndex_2lss_MVA_CP(LepGood1_pdgId, LepGood2_pdgId, tth,  ttw, thq, rest, cp);
  if (bin >=25 && bin <29) b = bin-10-8-6;
  else if (bin>107 && bin<=119) b =bin-79-10-8-6;
  else if (bin>196 && bin<=203) b = bin-(78+79+10+8+6);
  else 
    b=-99;
  return b;
}



int ttH_catIndex_2lss_MVA(int LepGood1_pdgId, int LepGood2_pdgId, float tth, float ttw, float thq, float rest)
{
  if (!f2lssBins){
    int offset = 0;
    f2lssBins = TFile::Open("../../data/kinMVA/DNNBin_v3_xmas.root");
    for (auto & la : bin2lsslabels){
      int bins = bins2lss[la];
      binHistos2lss[la] = (TH1F*) f2lssBins->Get(Form("%s_2018_Map_nBin%d", la.Data(), bins));
      bins2lsscumul[la] = offset;
      offset += bins;
    }
  }
  int idx = ttH_catIndex_2lss(LepGood1_pdgId, LepGood2_pdgId, tth,ttw, thq,rest); 
  TString binLabel = bin2lsslabels[idx-1];
  float mvavar = 0;
  if (tth >= ttw && tth >= thq && tth >= rest)
    mvavar = tth;
  else if (rest >= tth && rest >= ttw && rest >= thq)
    mvavar =rest;
  else if (ttw >= tth && ttw >= rest && ttw >= thq)
    mvavar = ttw;
  else if (thq >= tth && thq >= rest && thq >= ttw)
    mvavar = thq;
  else 
    cout << "It shouldnt be here" << endl;

  return binHistos2lss[binLabel]->FindBin( mvavar ) + bins2lsscumul[binLabel];

}


// for plots

int ttH_2lss_node( float tth, float ttw, float thq, float rest ){

  int procch = 0;
  if (tth >= ttw && tth >= thq && tth >= rest)
    procch = 0;
  else if (rest >= tth && rest >= ttw && rest >= thq)
    procch = 1;
  else if (ttw >= tth && ttw >= rest && ttw >= thq)
    procch = 2;
  else if (thq >= tth && thq >= rest && thq >= ttw)
    procch = 3;
  else 
    cout << "[2lss]: It shouldnt be here. DNN scores are " << tth << " " << rest << " " << ttw << " " << thq << endl;

  return procch;
}


std::vector<TString> bin2lsslabels_plots = {
  "ee_ttHnode" , "em_ttHnode" ,  "mm_ttHnode", 
  "ee_Restnode", "em_Restnode",  "mm_Restnode",
  "ee_ttWnode" , "em_ttWnode" ,  "mm_ttWnode",
  "ee_tHQnode" , "em_tHQnode" ,  "mm_tHQnode",

};

std::map<TString, TH1F*> binHistos2lss_plots;
TFile* f2lssBins_plots;


int ttH_catIndex_2lss_plots(int LepGood1_pdgId, int LepGood2_pdgId, float tth, float ttw, float thq, float rest)
{

  if (!f2lssBins_plots){
    f2lssBins_plots = TFile::Open("../../data/kinMVA/DNNBin_v3_xmas.root");
    for (auto & la : bin2lsslabels_plots){
      int bins = bins2lss[la];
      binHistos2lss_plots[la] = (TH1F*) f2lssBins_plots->Get(Form("%s_2018_Map_nBin%d", la.Data(), bins));
    }
  }

  int idx = ttH_catIndex_2lss(LepGood1_pdgId, LepGood2_pdgId, tth,ttw, thq,rest); 
  TString binLabel = bin2lsslabels[idx-1];
  int offset=0;
  int node = ttH_2lss_node(tth, ttw,thq, rest);
  if (abs(LepGood1_pdgId*LepGood2_pdgId) == 143){
    if (node == 0) offset = 5;
    else if (node == 1) offset = 8;
    else if (node == 2) offset = 6;
    else offset = 4;
  }
  if (abs(LepGood1_pdgId*LepGood2_pdgId) == 169){
    if (node == 0) offset = 5+13;
    else if (node == 1) offset = 8+8;
    else if (node == 2) offset = 6+19;
    else offset = 4+11;
  }

  float mvavar = 0;
  if (tth >= ttw && tth >= thq && tth >= rest)
    mvavar = tth;
  else if (rest >= tth && rest >= ttw && rest >= thq)
    mvavar =rest;
  else if (ttw >= tth && ttw >= rest && ttw >= thq)
    mvavar = ttw;
  else if (thq >= tth && thq >= rest && thq >= ttw)
    mvavar = thq;
  else 
    cout << "It shouldnt be here" << endl;


  return binHistos2lss_plots[binLabel]->FindBin( mvavar ) + offset;
    

}


float ttH_catIndex_2lss1tau( float tth, float thq, float bkg)
{

  if ((tth > thq)  && (tth > bkg)){
    if (tth < 0.49)       return 0;
    else if (tth < 0.57)  return 1;
    else if (tth < 0.64)  return 2;
    else if (tth < 0.74)  return 3;
    else if (tth < 0.85)  return 4;
    else                  return 5;
  }
  else if ((thq > tth) && (thq > bkg)){
    if      (thq < 0.49) return 6;
    else if (thq < 0.57) return 7;
    else if (thq < 0.70) return 8;
    else                 return 9;
  }
  else{
    if (bkg < 0.5)         return 10;
    else if ( bkg < 0.56 ) return 11;
    else if ( bkg < 0.62 ) return 12;
    else if ( bkg < 0.71 ) return 13;
    else                   return 14;

  }
  
}

float ttH_catIndex_2lss1tau_CP( float tth, float thq, float bkg, float cp)
{
  int cpIndx=0;
  if      ( cp < 0.139074) cpIndx=0;
  else if ( cp < 0.181274) cpIndx=1;
  else if ( cp < 0.243589) cpIndx=2;
  else                       cpIndx=3;

  if ((tth > thq)  && (tth > bkg)){
    if (tth < 0.49)       return 0 + cpIndx*6;
    else if (tth < 0.57)  return 1 + cpIndx*6;
    else if (tth < 0.64)  return 2 + cpIndx*6;
    else if (tth < 0.74)  return 3 + cpIndx*6;
    else if (tth < 0.85)  return 4 + cpIndx*6;
    else                  return 5 + cpIndx*6;
  }
  else if ((thq > tth) && (thq > bkg)){
    if      (thq < 0.49) return 24;
    else if (thq < 0.57) return 25;
    else if (thq < 0.70) return 26;
    else                 return 27;
  }
  else{
    if (bkg < 0.5)         return 28;
    else if ( bkg < 0.56 ) return 29;
    else if ( bkg < 0.62 ) return 30;
    else if ( bkg < 0.71 ) return 31;
    else                   return 32;

  }
  
}


TF1* fTauSFs[3][3];
TFile* fTauSFFiles[3];

TF1* fTauFRs[3][2][5]; // year, eta range, (nom, par1Down, par1Up, par2Down, par2Up)
TFile* fTauFRFiles[3];

bool isTauSFInit=false;
float tauSF( float taupt, float taueta, int year, int isMatch, int var=0, int varFRNorm=0, int varFRShape=0){  // var is -1,0,1

  assert( (abs(var)+abs(varFRShape)+abs(varFRNorm) != 0 && abs(var)+abs(varFRShape)+abs(varFRNorm) != 1) );

  // to add the fr uncertainty
  if (!isTauSFInit){
    isTauSFInit=true;
    fTauSFFiles[0]=TFile::Open("$CMSSW_BASE/src/CMGTools/TTHAnalysis/data/tauSF/TauID_SF_pt_DeepTau2017v2p1VSjet_2016Legacy.root");
    fTauSFFiles[1]=TFile::Open("$CMSSW_BASE/src/CMGTools/TTHAnalysis/data/tauSF/TauID_SF_pt_DeepTau2017v2p1VSjet_2017ReReco.root");
    fTauSFFiles[2]=TFile::Open("$CMSSW_BASE/src/CMGTools/TTHAnalysis/data/tauSF/TauID_SF_pt_DeepTau2017v2p1VSjet_2018ReReco.root");
    for (int i =0; i < 3; ++i){
      fTauSFs[i][0]=(TF1*) fTauSFFiles[i]->Get("VLoose_down");
      fTauSFs[i][1]=(TF1*) fTauSFFiles[i]->Get("VLoose_cent");
      fTauSFs[i][2]=(TF1*) fTauSFFiles[i]->Get("VLoose_up");
    }
    fTauFRFiles[0]=TFile::Open("$CMSSW_BASE/src/CMGTools/TTHAnalysis/data/tauSF/FR_deeptau_2016_v6.root");
    fTauFRFiles[1]=TFile::Open("$CMSSW_BASE/src/CMGTools/TTHAnalysis/data/tauSF/FR_deeptau_2017_v6.root");
    fTauFRFiles[2]=TFile::Open("$CMSSW_BASE/src/CMGTools/TTHAnalysis/data/tauSF/FR_deeptau_2018_v6.root");
    for (int i =0; i < 3; ++i){
      fTauFRs[i][0][0]=(TF1*) fTauFRFiles[i]->Get("jetToTauFakeRate_withoutTriggerMatching/deepVSjVLoose/absEtaLt1_5/fitFunction_data_div_mc_hadTaus_pt");
      fTauFRs[i][1][0]=(TF1*) fTauFRFiles[i]->Get("jetToTauFakeRate_withoutTriggerMatching/deepVSjVLoose/absEta1_5to9_9/fitFunction_data_div_mc_hadTaus_pt");
      fTauFRs[i][0][1]=(TF1*) fTauFRFiles[i]->Get("jetToTauFakeRate_withoutTriggerMatching/deepVSjVLoose/absEtaLt1_5/fitFunction_data_div_mc_hadTaus_pt_par1Down");
      fTauFRs[i][1][1]=(TF1*) fTauFRFiles[i]->Get("jetToTauFakeRate_withoutTriggerMatching/deepVSjVLoose/absEta1_5to9_9/fitFunction_data_div_mc_hadTaus_pt_par1Down");
      fTauFRs[i][0][2]=(TF1*) fTauFRFiles[i]->Get("jetToTauFakeRate_withoutTriggerMatching/deepVSjVLoose/absEtaLt1_5/fitFunction_data_div_mc_hadTaus_pt_par1Up");
      fTauFRs[i][1][2]=(TF1*) fTauFRFiles[i]->Get("jetToTauFakeRate_withoutTriggerMatching/deepVSjVLoose/absEta1_5to9_9/fitFunction_data_div_mc_hadTaus_pt_par1Up");
      fTauFRs[i][0][3]=(TF1*) fTauFRFiles[i]->Get("jetToTauFakeRate_withoutTriggerMatching/deepVSjVLoose/absEtaLt1_5/fitFunction_data_div_mc_hadTaus_pt_par2Down");
      fTauFRs[i][1][3]=(TF1*) fTauFRFiles[i]->Get("jetToTauFakeRate_withoutTriggerMatching/deepVSjVLoose/absEta1_5to9_9/fitFunction_data_div_mc_hadTaus_pt_par2Down");
      fTauFRs[i][0][4]=(TF1*) fTauFRFiles[i]->Get("jetToTauFakeRate_withoutTriggerMatching/deepVSjVLoose/absEtaLt1_5/fitFunction_data_div_mc_hadTaus_pt_par2Up");
      fTauFRs[i][1][4]=(TF1*) fTauFRFiles[i]->Get("jetToTauFakeRate_withoutTriggerMatching/deepVSjVLoose/absEta1_5to9_9/fitFunction_data_div_mc_hadTaus_pt_par2Up");
    }
  }
  


  if (isMatch){
    float varSF=fTauSFs[year-2016][var+1]->Eval(taupt);
    float nomSF=fTauSFs[year-2016][1]->Eval(taupt);
    return  (1 + var*std::sqrt( (varSF/nomSF-1)*(varSF/nomSF-1) + 0.03*0.03))*nomSF;
  }


  else{
    int etaindx = (abs(taueta)<1.5) ? 0 : 1;
    int varIdx  = 0;
    if (varFRNorm==1) varIdx=2;
    if (varFRNorm==-1) varIdx=1;
    if (varFRShape==1) varIdx=4;
    if (varFRShape==-1) varIdx=3;
    return fTauFRs[year-2016][etaindx][varIdx]->Eval(taupt);
  }
  

}


int ttH_catIndex_2lss_nosign(int LepGood1_pdgId, int LepGood2_pdgId, int nBJetMedium25){

  if (abs(LepGood1_pdgId)==11 && abs(LepGood2_pdgId)==11) return 1;
  if ((abs(LepGood1_pdgId) != abs(LepGood2_pdgId)) && nBJetMedium25 < 2) return 2;
  if ((abs(LepGood1_pdgId) != abs(LepGood2_pdgId)) && nBJetMedium25 >= 2) return 3;
  if (abs(LepGood1_pdgId)==13 && abs(LepGood2_pdgId)==13 && nBJetMedium25 < 2) return 4;
  if (abs(LepGood1_pdgId)==13 && abs(LepGood2_pdgId)==13 && nBJetMedium25 >= 2) return 5;

 return -1;

}

int ttH_catIndex_2lss_SVA(int LepGood1_pdgId, int LepGood2_pdgId, int LepGood1_charge, int nJet25){

  int res = -2;

  if (abs(LepGood1_pdgId)==11 && abs(LepGood2_pdgId)==11) res = 1;
  if ((abs(LepGood1_pdgId) != abs(LepGood2_pdgId)) && LepGood1_charge<0) res = 3;
  if ((abs(LepGood1_pdgId) != abs(LepGood2_pdgId)) && LepGood1_charge>0) res = 5;
  if (abs(LepGood1_pdgId)==13 && abs(LepGood2_pdgId)==13 && LepGood1_charge<0) res = 7;
  if (abs(LepGood1_pdgId)==13 && abs(LepGood2_pdgId)==13 && LepGood1_charge>0) res = 9;
  if (nJet25>=6) res+=1;

  return res; // 1-10
}


int ttH_catIndex_2lss_SVA_forPlots1(int LepGood1_pdgId, int LepGood2_pdgId, int nJet25){

  int res = -2;

  if (abs(LepGood1_pdgId)==11 && abs(LepGood2_pdgId)==11) res = 1;
  if ((abs(LepGood1_pdgId) != abs(LepGood2_pdgId))) res = 3;
  if (abs(LepGood1_pdgId)==13 && abs(LepGood2_pdgId)==13) res = 5;
  if (nJet25>=6) res+=1;

  return res; // 1-6
}

int ttH_catIndex_2lss_SVA_forPlots2(int nJet25){

  int res = 1;
  if (nJet25>=6) res+=1;
  return res; // 1-6
}

int ttH_catIndex_2lss_SVA_soft(int LepGood1_pdgId, int LepGood2_pdgId, int LepGood1_charge, int nJet25){

  int res = -2;

  if (abs(LepGood1_pdgId)==11 && abs(LepGood2_pdgId)==11) res = 1;
  if ((abs(LepGood1_pdgId) != abs(LepGood2_pdgId)) && LepGood1_charge<0) res = 3;
  if ((abs(LepGood1_pdgId) != abs(LepGood2_pdgId)) && LepGood1_charge>0) res = 5;
  if (abs(LepGood1_pdgId)==13 && abs(LepGood2_pdgId)==13 && LepGood1_charge<0) res = 7;
  if (abs(LepGood1_pdgId)==13 && abs(LepGood2_pdgId)==13 && LepGood1_charge>0) res = 9;
  if (nJet25>3) res+=1;

  return res; // 1-10
}


int ttH_catIndex_3l(float ttH, float tH, float rest, int lep1_pdgId, int lep2_pdgId, int lep3_pdgId, int nBMedium )
{

  int sumpdgId = abs(lep1_pdgId)+abs(lep2_pdgId)+abs(lep3_pdgId);
  
  if (ttH >= rest && ttH >= tH){
    if (nBMedium < 2)
      return 1; // ttH_bl
    else
      return 2; // ttH_bt
  }
  else if (tH >= ttH && tH >= rest){
    if (nBMedium < 2){
      return 3; // tH_bl
    }
    else{
      return 4; // tH_bt
    }
  }
  else if (rest >= ttH && rest >= tH){
    if ( sumpdgId == 33){ // rest_eee
      return 5;
    }
    else if (sumpdgId == 35){ 
      if (nBMedium < 2)
	return 6; // rest_eem_bl
      else
	return 7; // rest_eem_bt
    }
    else if (sumpdgId == 37){ // emm
      if (nBMedium < 2)
	return 8; // rest_emm_bl
      else
	return 9; // rest_emm_bt
    }
    else if (sumpdgId == 39){ // mmm
      if (nBMedium < 2)
	return 10; // rest_mmm_bl
      else
	return 11; // rest_mmm_bt
    }
  }

  
  cout << "[ttH_catIndex_3l]: It should not be here" << endl;
  return -1;

}


std::vector<TString> bin3llabels = {"ttH_bl",  "ttH_bt",  "tH_bl",  "tH_bt",  "rest_eee",  "rest_eem_bl",  "rest_eem_bt",  "rest_emm_bl",  "rest_emm_bt",  "rest_mmm_bl",  "rest_mmm_bt"};

std::map<TString, TH1F*> binHistos3l;
std::map<TString, int> bins3lcumul;
std::map<TString, int> bins3lcumul_cp;
TFile* f3lBins;



int ttH_catIndex_3l_MVA(float ttH, float tH, float rest, int lep1_pdgId, int lep2_pdgId, int lep3_pdgId, int nBMedium )
{

  if (!f3lBins){
    f3lBins=TFile::Open("../../data/kinMVA/binning_3l.root");
    int count=0;
    for (auto label : bin3llabels){
      binHistos3l[label] = (TH1F*) f3lBins->Get(label);
      bins3lcumul[label] = count;
      count += binHistos3l[label]->GetNbinsX();
    }
  }
  TString binLabel = bin3llabels[ttH_catIndex_3l(ttH,tH,rest,lep1_pdgId,lep2_pdgId,lep3_pdgId,nBMedium)-1];
  float mvas[] = { ttH, tH, rest };
  float mvavar = *std::max_element( mvas, mvas+3 );
  return binHistos3l[binLabel]->FindBin( mvavar ) + bins3lcumul[binLabel];

  
  cout << "[ttH_catIndex_3l_MVA]: It should not be here "<< ttH << " " << tH << " " << rest << endl;
  return -1;

}

int ttH_catIndex_3l_MVA_CP(float ttH, float tH, float rest, int lep1_pdgId, int lep2_pdgId, int lep3_pdgId, int nBMedium, float cp )
{

  if (!f3lBins){
    f3lBins=TFile::Open("../../data/kinMVA/binning_3l.root");
    int count=0;
    for (auto label : bin3llabels){
      binHistos3l[label] = (TH1F*) f3lBins->Get(label);
      bins3lcumul_cp[label] = count;
      int ncpbins=1;
      if (label.Contains("ttH")) ncpbins=4;
      count += binHistos3l[label]->GetNbinsX()*ncpbins;
    }
  }
  TString binLabel = bin3llabels[ttH_catIndex_3l(ttH,tH,rest,lep1_pdgId,lep2_pdgId,lep3_pdgId,nBMedium)-1];
  float mvas[] = { ttH, tH, rest };
  float mvavar = 0;
  int cpIdx=0;
  if (ttH > tH && ttH > rest){
    mvavar=ttH;
    if (cp < 0.44861784) cpIdx= 0;
    else if (cp < 0.51305674) cpIdx= 1;
    else if (cp < 0.59185324) cpIdx= 2;
    else                      cpIdx= 3;
  }
  else if (tH > rest && tH > ttH)
    mvavar=tH;
  else
    mvavar=rest;

  return binHistos3l[binLabel]->FindBin( mvavar ) + binHistos3l[binLabel]->GetNbinsX()*cpIdx + bins3lcumul_cp[binLabel];

  
  cout << "[ttH_catIndex_3l_MVA]: It should not be here "<< ttH << " " << tH << " " << rest << endl;
  return -1;

}

int ttH_catIndex_3l_node(float ttH, float tH, float rest){
  if (ttH >= tH && ttH >= rest){
    return 0;
  }
  else if (tH >= ttH && tH >= rest){
    return 1;
  }
  else if (rest >= ttH && rest >= tH){
    return 2;
  }
}


int ttH_catIndex_3l_plots(float ttH, float tH, float rest, int lep1_pdgId, int lep2_pdgId, int lep3_pdgId, int nBMedium )
{
  if (!f3lBins){
    f3lBins=TFile::Open("../../data/kinMVA/binning_3l.root");
    int count=0;
    for (auto label : bin3llabels){
      binHistos3l[label] = (TH1F*) f3lBins->Get(label);
      bins3lcumul[label] = count;
      count += binHistos3l[label]->GetNbinsX();
    }
  }

  int offset =0;
  int pdgSum = abs(lep1_pdgId) + abs(lep2_pdgId) + abs(lep3_pdgId);

  if (ttH_catIndex_3l_node(ttH,tH,rest) == 0){
    if (nBMedium >= 2) offset=5;
  }
  else if (ttH_catIndex_3l_node(ttH,tH,rest) == 1){
    if (nBMedium >= 2) offset=7;
  }
  else{
    if (nBMedium  < 2){
      if (pdgSum == 35) offset = 1;
      else if (pdgSum == 37) offset=1+4;
      else if (pdgSum == 39) offset=1+4+4;
    }
    else{
      if (pdgSum == 35) offset = 1+4+4+3;
      if (pdgSum == 37) offset = 1+4+4+3+1;
      if (pdgSum == 39) offset = 1+4+4+3+1+1;
    }
  }
  TString binLabel = bin3llabels[ttH_catIndex_3l(ttH,tH,rest,lep1_pdgId,lep2_pdgId,lep3_pdgId,nBMedium)-1];
  float mvas[] = { ttH, tH, rest };
  float mvavar = *std::max_element( mvas, mvas+3 );
  return binHistos3l[binLabel]->FindBin( mvavar ) + offset;

}

float ttH_mva_4l(float score)
{
  return 1. / (1. + std::sqrt((1. - score) / (1. + score)));

}

int ttH_catIndex_4l(float bdt, float cut=0.85)
{
  if (ttH_mva_4l(bdt) < cut) return 1;
  else return 2;
}

int ttH_catIndex_3l_SVA(int LepGood1_charge, int LepGood2_charge, int LepGood3_charge, int nJet25){

  if ((LepGood1_charge+LepGood2_charge+LepGood3_charge)<0 && nJet25 < 4) return 11;
  if ((LepGood1_charge+LepGood2_charge+LepGood3_charge)>0 && nJet25 < 4) return 12;
  if ((LepGood1_charge+LepGood2_charge+LepGood3_charge)<0 && nJet25 >= 4) return 13;
  if ((LepGood1_charge+LepGood2_charge+LepGood3_charge)>0 && nJet25 >= 4) return 14;

  return -1;

}

int ttH_catIndex_3l_SVAforPlots(int nJet25){

  if (nJet25 < 4) return 1;
  if (nJet25 >= 4) return 2;

  return -1;

}

int ttH_catIndex_3l_SVA_soft(int LepGood1_charge, int LepGood2_charge, int LepGood3_charge, int nJet25){

  if ((LepGood1_charge+LepGood2_charge+LepGood3_charge)<0 && nJet25 <= 3) return 11;
  if ((LepGood1_charge+LepGood2_charge+LepGood3_charge)>0 && nJet25 <= 3) return 12;
  if ((LepGood1_charge+LepGood2_charge+LepGood3_charge)<0 && nJet25 > 3) return 13;
  if ((LepGood1_charge+LepGood2_charge+LepGood3_charge)>0 && nJet25 > 3) return 14;

  return -1;

}




std::map<TString, TFile*> fRecoToLoose;
std::map<TString, TH1*> hRecoToLoose;

float _get_looseToTight_leptonSF_ttH(int pdgid, float pt, float eta, int nlep, int year, int suberaid){
  
  if (!fRecoToLoose.size()){
    for (auto& theyear : {"2016","2016APV", "2017", "2018"}){
      fRecoToLoose[TString::Format("%s_el_2lss",theyear)]=TFile::Open(TString::Format("../../data/leptonSF/elecNEWmva/egammaEffi%s_2lss_EGM2D.root",theyear));
      fRecoToLoose[TString::Format("%s_el_3l",theyear)]=TFile::Open(TString::Format("../../data/leptonSF/elecNEWmva/egammaEffi%s_3l_EGM2D.root",theyear));
      fRecoToLoose[TString::Format("%s_mu_3l",theyear)]=TFile::Open(TString::Format("../../data/leptonSF/muon/egammaEffi%s_EGM2D.root",theyear));
    }

    for (auto const & x : fRecoToLoose){
      hRecoToLoose[x.first]=(TH1*) x.second->Get("EGamma_SF2D");
    }

  }

  TString yearString= TString::Format("%d",year) + (( year == 2016 && suberaid == 0) ? "APV" : "");
  TString pdgstring  = (abs(pdgid) == 11) ? "el" : "mu";
  TString lepstring = (nlep == 2 && abs(pdgid) == 11 ) ? "2lss" : "3l";

  auto h = hRecoToLoose.at( yearString + "_" + pdgstring + "_" + lepstring);
  int bin = h->FindBin( std::abs(eta) ,std::min(std::max(pt,10.1f),119.f));

  return h->GetBinContent(bin);

}


float ttH_2lss_ifflav(int LepGood1_pdgId, int LepGood2_pdgId, float ret_ee, float ret_em, float ret_mm){
  if (abs(LepGood1_pdgId)==11 && abs(LepGood2_pdgId)==11) return ret_ee;
  if ((abs(LepGood1_pdgId) != abs(LepGood2_pdgId)))       return ret_em;
  if (abs(LepGood1_pdgId)==13 && abs(LepGood2_pdgId)==13) return ret_mm;
  std::cerr << "ERROR: invalid input " << abs(LepGood1_pdgId) << ", " << abs(LepGood1_pdgId) << std::endl;
  assert(0);
  return 0; // avoid warning
}
float ttH_2lss_ifflavnb(int LepGood1_pdgId, int LepGood2_pdgId, int nBJetMedium25, float ret_ee, float ret_em_bl, float ret_em_bt, float ret_mm_bl, float ret_mm_bt){
  if (abs(LepGood1_pdgId)==11 && abs(LepGood2_pdgId)==11) return ret_ee;
  if ((abs(LepGood1_pdgId) != abs(LepGood2_pdgId)) && nBJetMedium25 < 2) return ret_em_bl;
  if ((abs(LepGood1_pdgId) != abs(LepGood2_pdgId)) && nBJetMedium25 >= 2) return ret_em_bt;
  if (abs(LepGood1_pdgId)==13 && abs(LepGood2_pdgId)==13 && nBJetMedium25 < 2) return ret_mm_bl;
  if (abs(LepGood1_pdgId)==13 && abs(LepGood2_pdgId)==13 && nBJetMedium25 >= 2) return ret_mm_bt;
  std::cerr << "ERROR: invalid input " << abs(LepGood1_pdgId) << ", " << abs(LepGood1_pdgId) <<  ", " << nBJetMedium25 << std::endl;
  assert(0);
  return 0; // avoid warning
}

float ttH_3l_ifflav(int LepGood1_pdgId, int LepGood2_pdgId, int LepGood3_pdgId){
  if (abs(LepGood1_pdgId)==11 && abs(LepGood2_pdgId)==11 && abs(LepGood3_pdgId)==11) return 1;
  if ((abs(LepGood1_pdgId) + abs(LepGood2_pdgId) + abs(LepGood3_pdgId)) == 35)       return 2;
  if ((abs(LepGood1_pdgId) + abs(LepGood2_pdgId) + abs(LepGood3_pdgId)) == 37)       return 3;
  if (abs(LepGood1_pdgId)==13 && abs(LepGood2_pdgId)==13 && abs(LepGood3_pdgId)==13) return 4;
  return -1;
}

std::vector<int> boundaries_runPeriod2016 = {272007,275657,276315,276831,277772,278820,280919};
std::vector<int> boundaries_runPeriod2017 = {297020,299337,302030,303435,304911};
std::vector<int> boundaries_runPeriod2018 = {315252,316998,319313,320394};

std::vector<double> lumis_runPeriod2016 = {5.75, 2.573, 4.242, 4.025, 3.105, 7.576, 8.651};
std::vector<double> lumis_runPeriod2017 = {4.802,9.629,4.235,9.268,13.433};
std::vector<double> lumis_runPeriod2018 = {13.978 , 7.064 , 6.899 , 31.748};

bool cumul_lumis_isInit = false;
std::vector<float> cumul_lumis_runPeriod2016;
std::vector<float> cumul_lumis_runPeriod2017;
std::vector<float> cumul_lumis_runPeriod2018;

int runPeriod(int run, int year){
  std::vector<int> boundaries;
  if (year == 2016)
    boundaries = boundaries_runPeriod2016;
  else if (year == 2017)
    boundaries = boundaries_runPeriod2017;
  else if (year == 2018)
    boundaries = boundaries_runPeriod2018;
  else{
    std::cout << "Wrong year " << year << std::endl;
    return -99;
  }
  auto period = std::find_if(boundaries.begin(),boundaries.end(),[run](const int &y){return y>run;});
  return std::distance(boundaries.begin(),period)-1 + ( (year == 2017) ? 7 : 0 ) + ( (year == 2018) ? 12 : 0 ) ;
}

TRandom3 rand_generator_RunDependentMC(0);
int hashBasedRunPeriod2017(int isData, int run, int lumi, int event, int year){
  if (isData) return runPeriod(run,year);
  if (!cumul_lumis_isInit){
    cumul_lumis_runPeriod2016.push_back(0);
    cumul_lumis_runPeriod2017.push_back(0);
    cumul_lumis_runPeriod2018.push_back(0);
    float tot_lumi_2016 = std::accumulate(lumis_runPeriod2016.begin(),lumis_runPeriod2016.end(),float(0.0));
    float tot_lumi_2017 = std::accumulate(lumis_runPeriod2017.begin(),lumis_runPeriod2017.end(),float(0.0));
    float tot_lumi_2018 = std::accumulate(lumis_runPeriod2018.begin(),lumis_runPeriod2018.end(),float(0.0));

    for (uint i=0; i<lumis_runPeriod2016.size(); i++) cumul_lumis_runPeriod2016.push_back(cumul_lumis_runPeriod2016.back()+lumis_runPeriod2016[i]/tot_lumi_2016);
    for (uint i=0; i<lumis_runPeriod2017.size(); i++) cumul_lumis_runPeriod2017.push_back(cumul_lumis_runPeriod2017.back()+lumis_runPeriod2017[i]/tot_lumi_2017);
    for (uint i=0; i<lumis_runPeriod2018.size(); i++) cumul_lumis_runPeriod2018.push_back(cumul_lumis_runPeriod2018.back()+lumis_runPeriod2018[i]/tot_lumi_2018);
    cumul_lumis_isInit = true;
  }
  Int_t x = 161248*run+2136324*lumi+12781432*event;
  unsigned int hash = TString::Hash(&x,sizeof(Int_t));
  rand_generator_RunDependentMC.SetSeed(hash);
  float val = rand_generator_RunDependentMC.Uniform();
  
  vector<float> cumul;
  if (year == 2016) cumul = cumul_lumis_runPeriod2016;
  else if (year == 2017) cumul = cumul_lumis_runPeriod2017;
  else if (year == 2018) cumul = cumul_lumis_runPeriod2018;
  else{
    std::cout << "Wrong year " << year << std::endl;
    return -99;
  }
  auto period = std::find_if(cumul.begin(),cumul.end(),[val](const float &y){return y>val;});
  return std::distance(cumul.begin(),period)-1 + ( (year == 2017) ? 7 : 0 ) + ( (year == 2018) ? 12 : 0 );
}


float wploose[3][2]  = {{0.0508, 0.0480}, {0.0532,-99}, {0.0490,-99}};
float wpmedium[3][2] = {{0.2598,0.2489} , {0.3040,-99}, {0.2783,-99}};

float deepFlavB_WPLoose(int year, int subera) {
    return wploose[year-2016][subera];
}
float deepFlavB_WPMedium(int year, int subera) {
    return wpmedium[year-2016][subera];
}
// float deepFlavB_WPTight(int year, int subera) {
//     float wp[3]  = { 0.7221, 0.7489, 0.7264 };
//     return wp[year-2016];
// }

float smoothBFlav(float jetpt, float ptmin, float ptmax, int year, int subera, float scale_loose=1.0) {

  float the_wploose =wploose[year-2016][subera];
  float the_wpmedium=wpmedium[year-2016][subera];
  float x = std::min(std::max(0.f, jetpt - ptmin)/(ptmax-ptmin), 1.f); 
  return x*the_wploose*scale_loose + (1-x)*the_wpmedium;
}

float ttH_4l_clasifier(float nJet25,float nBJetMedium25,float mZ2){
 
  if ( abs(mZ2 -91.2)<10) return 1;
  if ((abs(mZ2-91.2) > 10) && nJet25==0) return 2;
  if ( (abs(mZ2-91.2) > 10) && nJet25>=0 && nBJetMedium25==1) return 3;
  if ( (abs(mZ2-91.2) > 10) && nJet25>=1 && nBJetMedium25>1) return 4;

  else return -1;
}

float ttH_3l_clasifier(float nJet25,float nBJetMedium25){

  if (nJet25 == 0) return 0;
  if ((nJet25 == 1)*(nBJetMedium25 == 0)) return 1;
  if ((nJet25 == 2)*(nBJetMedium25 == 0)) return 2;
  if ((nJet25 == 3)*(nBJetMedium25 == 0)) return 3;
  if ((nJet25>3)*(nBJetMedium25 == 0))    return 4;
  if ((nJet25 == 1)*(nBJetMedium25 == 1)) return 5;
  if ((nJet25 == 2)*(nBJetMedium25 == 1)) return 6;
  if ((nJet25 == 3)*(nBJetMedium25 == 1)) return 7;
  if ((nJet25 == 4)*(nBJetMedium25 == 1)) return 8;
  if ((nJet25>4)*(nBJetMedium25 == 1))    return 9;
  if ((nJet25 == 2)*(nBJetMedium25>1))    return 10;
  if ((nJet25 == 3)*(nBJetMedium25>1))    return 11;
  if ((nJet25 == 4)*(nBJetMedium25>1))    return 12;
  if ((nJet25>4)*(nBJetMedium25>1))       return 13;
  else return -1;
}

