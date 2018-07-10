class cut:
    def __init__(self,name,varName,cutRangeMin=-999,cutRangeMax=999):
        self.name    = name
        self.passCut =False
        self.varName = varName                   # events variable name
        self.var     = 0                         # event var. float
        self.cutRangeMin = cutRangeMin
        self.cutRangeMax = cutRangeMax

    def runCut(self,event):
        result = False
        self.var = getattr(event,self.varName)
        if self.cutRangeMin == self.cutRangeMax:
            if self.var == self.cutRangeMin:    result=True
        elif self.cutRangeMin ==-999:          
            if self.var < self.cutRangeMax:     result=True     #invalid min value, do 1-sided cut
        elif self.cutRangeMax ==999:
            if self.var > self.cutRangeMin:     result=True     #invalid max value, do 1-sided cut
        elif self.cutRangeMin<self.cutRangeMax:
            if self.var > self.cutRangeMin and self.var < self.cutRangeMax:
                 result=True     #invalid max value, do 1-sided cut
        else:
            print "Invalid cut range = (%s,%s)"%(self.cutRangeMin,self.cutRangeMax) 
        self.passCut = result
        return result
