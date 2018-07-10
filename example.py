from ROOT import *
from  Analyzer import *
from cut import *
import math
from optparse import OptionParser

def deltaR(eta1,phi1,eta2,phi2):
    dphi = phi1-phi2
    return ((eta1-eta2)**2 + (TMath.ATan2( TMath.Sin(dphi), TMath.Cos(dphi)))**2)**0.5

def N2DDT_transform(h_N2_map,rho,pT,N2):
    # N2DDT transformation
    rh_8,jpt_8  = rho,pT
    trans_h2ddt = h_N2_map
    cur_rho_index = trans_h2ddt.GetXaxis().FindBin(rh_8)
    cur_pt_index = trans_h2ddt.GetYaxis().FindBin(jpt_8)
    if rh_8 > trans_h2ddt.GetXaxis().GetBinUpEdge(
        trans_h2ddt.GetXaxis().GetNbins()): cur_rho_index = trans_h2ddt.GetXaxis().GetNbins()
    if rh_8 < trans_h2ddt.GetXaxis().GetBinLowEdge(1): cur_rho_index = 1
    if jpt_8 > trans_h2ddt.GetYaxis().GetBinUpEdge(
        trans_h2ddt.GetYaxis().GetNbins()): cur_pt_index = trans_h2ddt.GetYaxis().GetNbins()
    if jpt_8 < trans_h2ddt.GetYaxis().GetBinLowEdge(1): cur_pt_index = 1
    jtN2b1sdddt_8 = N2 - trans_h2ddt.GetBinContent(cur_rho_index, cur_pt_index)
    return jtN2b1sdddt_8

def PUPPIweight(puppipt=30., puppieta=0.):
    genCorr = 1.
    recoCorr = 1.
    totalWeight = 1.

    # based on https://github.com/thaarres/PuppiSoftdropMassCorr Summer16
    corrGEN = TF1("corrGEN", "[0]+[1]*pow(x*[2],-[3])", 200, 3500)
    corrGEN.SetParameters(1.00626,-1.06161,0.0799900,1.20454)

    corrRECO_cen = TF1("corrRECO_cen", "[0]+[1]*x+[2]*pow(x,2)+[3]*pow(x,3)+[4]*pow(x,4)+[5]*pow(x,5)",200, 3500)
    corrRECO_cen.SetParameters(1.09302, -0.000150068, 3.44866e-07, -2.68100e-10, 8.67440e-14, -1.00114e-17)

    corrRECO_for = TF1("corrRECO_for", "[0]+[1]*x+[2]*pow(x,2)+[3]*pow(x,3)+[4]*pow(x,4)+[5]*pow(x,5)",200, 3500)
    corrRECO_cen.SetParameters(1.27212, -0.000571640, 8.37289e-07, -5.20433e-10, 1.45375e-13, -1.50389e-17)

    genCorr = corrGEN.Eval(puppipt)
    if (abs(puppieta) < 1.3):
        recoCorr = corrRECO_cen.Eval(puppipt)
    else:
        recoCorr = corrRECO_for.Eval(puppipt)
    totalWeight = genCorr * recoCorr
    return totalWeight

def pickJet(event):
    data   = {"pT":[],"mSD":[],"eta":[],"phi":[],"N2":[],'maxPtIdx':0,'maxMassIdx':0,'minN2Idx':0}
    for j_idx in range(0,3):
        if j_idx+1 > event.nAK8Puppijets:continue
        pT  = getattr(event,"AK8Puppijet%i_pt"%j_idx)
        eta = getattr(event,"AK8Puppijet%i_eta"%j_idx)
        phi = getattr(event,"AK8Puppijet%i_phi"%j_idx)
        N2  = getattr(event,"AK8Puppijet%i_N2sdb1"%j_idx)
        if not getattr(event,"AK8Puppijet%i_msd"%j_idx)==0:
            mSD = getattr(event,"AK8Puppijet%i_msd"%j_idx) * PUPPIweight(pT, eta)
            if mSD <= 0: mSD = 0.01
            #mSD = getattr(event,"AK8Puppijet%i_msd"%j_idx) 
        else:
            mSD = 0
        data["pT" ].append(float("%.3f"%pT))
        data["eta"].append(float("%.3f"%eta))
        data["phi"].append(float("%.3f"%phi))
        data["N2" ].append(float("%.3f"%N2))
        data["mSD"].append(float("%.3f"%mSD))
    data['maxPtIdx']   = data['pT' ].index(max(data['pT' ]))
    data['maxMassIdx'] = data['mSD'].index(max(data['mSD']))
    data['minN2Idx']   = data['N2'].index(min(data['N2']))
    return data

def FillCutFlow(cuts,hlist):
    if not 'h_cutflow' in hlist.keys():
        hlist['h_cutflow'] = TH1F("h_cutflow","h_cutflow",len(cuts)+1,0,len(cuts)+1)
    else:
        hlist['h_cutflow'].Fill("All",1)
    passAllpreviousCuts = True
    for icut in cuts:
        if passAllpreviousCuts and icut.passCut:
            hlist['h_cutflow'].Fill(icut.name,1)
            #print "Pass this cut =",icut.name
            passAllpreviousCuts= passAllpreviousCuts and icut.passCut
        elif not icut.passCut:
            passAllpreviousCuts = False

def main(options,args,tag):

    inputFiles = options.inputFiles
    outpath    = options.outpath

    ana = Analyzer("TriggerAna",tag)
    ana.SetOutpath(outpath)
    ana.AddFiles(inputFiles)
    t   = ana.GetTree()
    f_h2ddt = TFile.Open("$ZPRIMEPLUSJET_BASE/analysis/ZqqJet/h3_n2ddt_26eff_36binrho11pt_Spring16.root","read")
    trans_h2ddt = f_h2ddt.Get("h2ddt")
    
    hlist={}
    
    hlist["h_nProcessedEvents"            ] = TH1D("h_nProcessedEvents"       ,"h_nProcessedEvents",1,0,1)
    hlist["h_passBit_Mu50"                ] = TH2D("h_pass_Mu50"       ,"h_pass_Mu50       ;m_{SD}^{PUPPI} [GeV];p_{T} [GeV]",15,0,300,20,0.,1000.0)
    hlist["h_passBit_AK8trimMass"         ] = TH2D("h_pass_AK8trimMass","h_pass_AK8trimMass;m_{SD}^{PUPPI} [GeV];p_{T} [GeV]",15,0,300,20,0.,1000.0)
    hlist["h_passBit_AK4Btag"             ] = TH2D("h_pass_AK4Btag"    ,"h_pass_AK4Btag    ;m_{SD}^{PUPPI} [GeV];p_{T} [GeV]",15,0,300,20,0.,1000.0)
    hlist["h_passBit_AK4BtagOrAK8trimMass"] = TH2D("h_pass_AK4BtagOrAK8trimMass"    ,"h_pass_AK4BtagOrAK8trimMass    ;m_{SD}^{PUPPI} [GeV];p_{T} [GeV]",15,0,300,20,0.,1000.0)
    hlist["h_passCuts"                    ] = TH2D("h_passCuts"                 ,"h_passCuts                   ;m_{SD}^{PUPPI} [GeV];p_{T} [GeV]",15,0,300,20,0.,1000.0)
    hlist["h_passCuts_MSSM"               ] = TH2D("h_passCuts_MSSM"            ,"h_passCuts_MSSM              ;m_{SD}^{PUPPI} [GeV];p_{T} [GeV]",15,0,300,20,0.,1000.0)
    hlist["h_passCuts_AK8trimMass"        ] = TH2D("h_passCuts_AK8trimMass"     ,"h_passCuts_AK8trimMass       ;m_{SD}^{PUPPI} [GeV];p_{T} [GeV]",15,0,300,20,0.,1000.0)
    hlist["h_passCuts_AK8trimMass_MSSM"   ] = TH2D("h_passCuts_AK8trimMass_MSSM","h_passCuts_AK8trimMass_MSSM  ;m_{SD}^{PUPPI} [GeV];p_{T} [GeV]",15,0,300,20,0.,1000.0)
    
    hlist["h_dR_ak80"                 ] = TH1D("h_dR_ak80"          ,"h_dR_ak80                  ; dR(H,ak80)",500,0,10)
    hlist["h_dR_ak80_ptcut"           ] = TH1D("h_dR_ak80_ptcut"    ,"h_dR_ak80,pT>450 GeV       ; dR(H,ak80)",500,0,10)
    hlist["h_dR_minN2"                ] = TH1D("h_dR_minN2"         ,"h_dR_minN2                 ; dR(H,jet(minN2))",500,0,10)
    hlist["h_dR_minN2_ptcut"          ] = TH1D("h_dR_minN2_ptcut"   ,"h_dR_minN2,pT>450 GeV      ; dR(H,jet(minN2))",500,0,10)
    hlist["h_N2_minN2"                ] = TH1D("h_N2_minN2"         ,"h_N2_minN2      ; AK8 N_{2}^{1}",40,0,1)
    hlist["h_N2_maxPT"                ] = TH1D("h_N2_maxPT"         ,"h_N2_maxPT      ; AK8 N_{2}^{1}",40,0,1)

    hlist["h_fBosonEta"                ] = TH1D("h_fBosonEta"         ,"h_fBosonEta      ; #eta",60,-6,6)
    hlist["h_fBosonPhi"                ] = TH1D("h_fBosonPhi"         ,"h_fBosonPhi      ; #phi",70,-3.5,3.5)


    hlist["h_minN2_maxPT"                 ] = TH2D("h_minN2_maxPT"          ,"h_minN2_maxPT           ;minN2 AK8 jet index   ;maxPT AK8 jet index",3,0,3,3,0.,3)
    hlist["h_minN2_maxPT_matchedpT"         ] = TH2D("h_minN2_maxPT_matchedpT"  ,"h_minN2_maxPT_matchedpT   ;minN2 AK8 jet index   ;maxPT AK8 jet index",3,0,3,3,0.,3)
    hlist["h_minN2_maxPT_matchedN2"         ] = TH2D("h_minN2_maxPT_matchedN2"  ,"h_minN2_maxPT_matchedN2   ;minN2 AK8 jet index   ;maxPT AK8 jet index",3,0,3,3,0.,3)
    hlist["h_maxMass_maxPT"              ] = TH2D("h_maxMass_maxPT","h_maxMass_maxPT  ;maxMass AK8 jet index ;maxPT AK8 jet index",3,0,3,3,0.,3)
    hlist["h_ak80_pt_ak80_genpt"         ] = TH2D("h_ak80_pt_ak80_genpt","h_ak80_pt_ak80_genpt  ;AK8_0 p_{T} [GeV];AK8_0 gen p_{T}[GeV]",50,0.,1000.0,50,0.,1000.0)
    hlist["h_ak81_pt_ak81_genpt"         ] = TH2D("h_ak81_pt_ak81_genpt","h_ak81_pt_ak81_genpt  ;AK8_1 p_{T} [GeV];AK8_1 gen p_{T}[GeV]",50,0.,1000.0,50,0.,1000.0)
    
    allcuts=[]
    allcuts.append(cut('pT>450'         ,'pT'   ,450   ,999 ))
    allcuts.append(cut('mSD>40'         ,'mSD'  ,40    ,999 ))
    allcuts.append(cut('-6.0<rho<-2.1'  ,'rho'  ,-6.0  ,-2.1 ))
    allcuts.append(cut('N2ddt<0'        ,'N2ddt',-999  , 0   ))
    allcuts.append(cut('dR(H,jet)<0.3'  ,'dR'   ,-999  , 0.3 ))
    allcuts.append(cut('met<140'        ,'met'  ,-999  , 140 ))
    allcuts.append(cut('nlep=0'         ,'nlep' ,0     , 0  ))
    
    print "Processing %s events..."%t.GetEntries()
    hlist['h_nProcessedEvents'].Fill(0,t.GetEntries())
    
    ana.histograms.append(hlist)
    for i,event in enumerate(t):
        #if i%int(t.GetEntries()*0.1)==0: print "processed %i events"%i
        triggerBits = t.triggerBits
        pT          = t.AK8Puppijet0_pt
        eta         = t.AK8Puppijet0_eta
        phi         = t.AK8Puppijet0_phi
        mSD         = t.AK8Puppijet0_msd * PUPPIweight(pT, eta) 
        N2          = t.AK8Puppijet0_N2sdb1
   
        hlist["h_fBosonEta"].Fill(t.fBosonEta) 
        hlist["h_fBosonPhi"].Fill(t.fBosonPhi) 
            
        pickedJets    = pickJet(event)
        maxMassIdx   = pickedJets['maxMassIdx']
        maxPtIdx     = pickedJets['maxPtIdx']
        minN2Idx     = pickedJets['minN2Idx']
        hlist["h_minN2_maxPT"].Fill(minN2Idx,maxPtIdx)
        hlist["h_maxMass_maxPT"].Fill(maxMassIdx,maxPtIdx)
        hlist["h_ak80_pt_ak80_genpt"].Fill(t.AK8Puppijet0_pt,t.AK8Puppijet0_genpt)
        hlist["h_ak81_pt_ak81_genpt"].Fill(t.AK8Puppijet1_pt,t.AK8Puppijet1_genpt)

        dRminN2jet          = deltaR(pickedJets['eta'][minN2Idx],pickedJets['phi'][minN2Idx],t.fBosonEta,t.fBosonPhi)
        dRmaxPtjet          = deltaR(pickedJets['eta'][maxPtIdx],pickedJets['phi'][maxPtIdx],t.fBosonEta,t.fBosonPhi)
        hlist["h_dR_minN2"].Fill(dRminN2jet)
        if pickedJets['pT'][minN2Idx]>450:
            hlist["h_dR_minN2_ptcut"].Fill(dRminN2jet)
            hlist["h_N2_minN2"].Fill(pickedJets['N2'][minN2Idx])
        hlist["h_N2_maxPT"].Fill(pickedJets['N2'][maxPtIdx])
        hlist["h_dR_ak80"].Fill(dRmaxPtjet)
        if pickedJets['pT'][maxPtIdx]>450:
            hlist["h_dR_ak80_ptcut"].Fill(dRmaxPtjet)
    
        if (dRmaxPtjet<0.3):
            hlist["h_minN2_maxPT_matchedpT"].Fill(minN2Idx,maxPtIdx)
        if (dRminN2jet<0.3):
            hlist["h_minN2_maxPT_matchedN2"].Fill(minN2Idx,maxPtIdx)
        

        if tag=="maxPt":
            (pT,eta,phi,mSD,N2) = (pickedJets['pT'][maxPtIdx],pickedJets['eta'][maxPtIdx],pickedJets['phi'][maxPtIdx],pickedJets['mSD'][maxPtIdx],pickedJets['N2'][maxPtIdx])
        if tag=="minN2":
            (pT,eta,phi,mSD,N2) = (pickedJets['pT'][minN2Idx],pickedJets['eta'][minN2Idx],pickedJets['phi'][minN2Idx],pickedJets['mSD'][minN2Idx],pickedJets['N2'][minN2Idx])

         
        if mSD <= 0: mSD = 0.01
        if pT==0:
            print pickedJets
            print (pT,eta,mSD,N2)
        rho         = math.log(mSD*mSD/pT/pT) 
        N2ddt       = N2DDT_transform(trans_h2ddt,rho,pT,N2)    
        met         = t.pfmet
        nlep        = t.neleLoose + t.ntau + t.nmuLoose
    
        event.pT   = pT
        event.mSD  = mSD
        event.nlep = nlep
        event.nlep = nlep
        event.met  = met
        event.rho  = rho
        event.N2ddt= N2ddt
        event.dR   = deltaR(eta,phi,t.fBosonEta,t.fBosonPhi)
            
        for icut in allcuts:
            icut.runCut(event)
        FillCutFlow(allcuts,hlist)
            
    
        passEvent=True
        if ( triggerBits & 4)                                             : hlist['h_passBit_Mu50'                ].Fill(mSD, pT)
        if ((triggerBits & 4) and (triggerBits & 2)                      ): hlist['h_passBit_AK8trimMass'         ].Fill(mSD, pT)
        if ((triggerBits & 4) and (triggerBits & 16)                     ): hlist['h_passBit_AK4Btag'             ].Fill(mSD, pT)
        if ((triggerBits & 4) and ((triggerBits & 16)or(triggerBits & 2))): hlist['h_passBit_AK4BtagOrAK8trimMass'].Fill(mSD, pT)
        if ( passEvent)                                                   : hlist["h_passCuts"                    ].Fill(mSD,pT)
        if ((passEvent) and (triggerBits & 2)                      )      : hlist["h_passCuts_AK8trimMass"        ].Fill(mSD,pT)
        if ((passEvent) and (triggerBits & 16)                     )      : hlist["h_passCuts_MSSM"               ].Fill(mSD,pT)
        if ((passEvent) and ((triggerBits & 16)or(triggerBits & 2)))      : hlist["h_passCuts_AK8trimMass_MSSM"   ].Fill(mSD,pT)
    
    ana.PrintInfo()
    ana.WriteHists()

##----##----##----##----##----##----##
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-i'  ,'--inputFiles' , dest='inputFiles' , default = '' ,help='directory inputfiles')
    parser.add_option('-o'  ,'--outpath'    , dest='outpath'    , default = '' ,help='directory to write outpath')

    (options, args) = parser.parse_args()
    main(options,args,tag="maxPt") 
    main(options,args,tag="minN2") 

##----##----##----##----##----##----##

