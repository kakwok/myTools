from ROOT import *
import os
import glob

class Analyzer:
    def __init__(self,name,tag=""):
        self.name   = name          # Analyzer name
        self.tag    = tag           # Tag
        self.fList  = []            # list of files
        self.chain  = TChain()      # TChain containing all files
        self.histograms = []        # List of dictionarys [{h1,h2,h3,..},{h1',h2',...}]
        self.outpath = ""           # Default output path is the current directory
        self.treeName = ""

    def PrintInfo(self):
        print "-------------------------------------------------------"
        print "| Analyzer = "+ self.name
        print "| tag      = "+ self.tag
        print "| Tree     = "+ self.treeName
        print "| Output   = "+ self.outpath + self.outName
        print "--------------------------------------------------------"
    def SetOutpath(self,outpath=""):
        self.outpath = outpath
        
    def SetOutputTag(self,outputTag):
        self.tag = outputTag

    def AddFiles(self,csvFlist):
        if len(csvFlist.split(","))>0:
            self.fList = csvFlist.split(",")
            for f in self.fList:
                if "*" in f:
                    self.fList.extend(glob.glob(f))
                    self.fList.remove(f)
            for f in self.fList:
                if not os.path.exists(f):   print "ERROR! Cannot find file = ",f
        else:
            print "input file string not splittable by ','",csvFlist
        self.inputPreFix = self.fList[0].split("/")[-1].replace(".root","")
        if not self.tag=="":
            self.outName     = self.name + "_"+ self.tag +"_"+ self.inputPreFix  +".root"
        else:                                                   
            self.outName     = self.name +"_"+ self.inputPreFix +".root"
        self.outFile     = TFile(self.outpath +self.outName,"RECREATE")


    def GetTree(self,treeNames=["otree","Events"]):
        print "Trying to get tree with file=",self.fList[0]
        exampleFile = TFile(self.fList[0])
        for tName in treeNames:
            if exampleFile.Get(tName):
                print "Found tree=",tName
                self.treeName= tName
                break
        if self.treeName=="":
            print "Error! Cannot find any tress with names= ",treeNames
        self.chain = TChain(self.treeName)
        for f in self.fList:
            print "Adding File = ",f
            self.chain.Add(f)
        return self.chain

    def WriteHists(self):
        self.outFile.cd()
        for hDict in self.histograms:
            for hName in hDict:
                print "Writing ",hName 
                hDict[hName].Write()
        self.outFile.Close()
