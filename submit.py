import os,glob
import sys, commands, os, fnmatch
from optparse import OptionParser

def exec_me(command, dryRun=False):
    print command
    if not dryRun:
        os.system(command)

def write_condor(exe='runjob.sh', arguments = [], files = [],dryRun=True):
    job_name = exe.replace('.sh','.jdl')
    out = 'universe = vanilla\n'
    out += 'Executable = %s\n'%exe
    out += 'Should_Transfer_Files = YES\n'
    out += 'WhenToTransferOutput = ON_EXIT_OR_EVICT\n'
    out += 'Transfer_Input_Files = %s,%s\n'%(exe,','.join(files))
    out += 'Output = job_%s.stdout\n'%job_name
    out += 'Error  = job_%s.stderr\n'%job_name
    out += 'Log    = job_%s.log\n'   %job_name
    #out += 'notify_user = jduarte1@FNAL.GOV\n'
    #out += 'x509userproxy = /tmp/x509up_u42518\n'
    out += 'Arguments = %s\n'%(' '.join(arguments))
    out += 'Queue 1\n'
    with open(job_name, 'w') as f:
        f.write(out)
    if not dryRun:
        os.system("condor_submit %s"%job_name)

def write_bash(temp = 'runjob.sh', command = ''):
    out = '#!/bin/bash\n'
    out += 'date\n'
    out += 'MAINDIR=`pwd`\n'
    out += 'ls\n'
    out += '#CMSSW from scratch (only need for root)\n'
    out += 'export CWD=${PWD}\n'
    out += 'export PATH=${PATH}:/cvmfs/cms.cern.ch/common\n'
    out += 'export CMS_PATH=/cvmfs/cms.cern.ch\n'
    out += 'export SCRAM_ARCH=slc6_amd64_gcc491\n'
    out += 'scramv1 project CMSSW CMSSW_7_4_7\n'
    out += 'cd CMSSW_7_4_7/src\n'
    out += 'eval `scramv1 runtime -sh` # cmsenv\n'
    out += 'git clone -b phibb git://github.com/DAZSLE/ZPrimePlusJet.git\n'
    out += 'cd ZPrimePlusJet\n'
    out += 'source setup.sh\n'
    #out += 'scramv1 build -j 4\n'
    out += command + '\n'
    out += 'echo "Inside $MAINDIR:"\n'
    out += 'ls\n'
    out += 'echo "DELETING..."\n'
    out += 'rm -rf CMSSW_7_4_7\n'
    out += 'ls\n'
    out += 'date\n'
    with open(temp, 'w') as f:
        f.write(out)

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in xrange(0, len(l), n):
        yield l[i:i + n]

if __name__ == '__main__':
    basePath = "/uscms/home/kkwok/eos/baconbits/zprimebits-v12.08/"
    sampleFolders = os.listdir(basePath)
    
    outputBase = "output"
    dryRun  = False 
    subdir  = os.path.expandvars("$PWD")
    sample  = ['GluGluHToBB_M125_13TeV_powheg_pythia8']
    group   = 10

    for sampleFolder in sampleFolders:
        if not sampleFolder in sample: continue
        fileList = glob.glob(basePath+"/"+sampleFolder+"/*.root")
        outpath  = "%s/%s/"%(outputBase,sampleFolder)
        if not os.path.exists(outpath):
            exec_me("mkdir -p %s"%(outpath), False)
        os.chdir(os.path.join(subdir,outpath))
        print  os.getcwd()
        # stplie files in to n(group) of chunks
        fChunks= list(chunks(fileList,group))
        print  "writing %s jobs for %s"%(len(fChunks),sampleFolder)
        for ifile, fChunk in enumerate(fChunks):
            #Extract the names of each file
            fChunkNames = []
            for f in fChunk:
                fChunkNames.append("${MAINDIR}/%s"%f.split("/")[-1])
            cmd = "python ${MAINDIR}/fillTrigger.py --inputFiles %s --outpath ${MAINDIR}/"%(",".join(fChunkNames))
            args =  []
            files = [",".join(fChunk), os.path.join(subdir,"cut.py"), os.path.join(subdir,"Analyzer.py") ,os.path.join(subdir,"fillTrigger.py") ]
            f_sh = "runjob_%s.sh"%ifile
            cwd    = os.getcwd()
            write_bash(f_sh, cmd)
            write_condor(f_sh ,args, files,dryRun)
        os.chdir(subdir)
