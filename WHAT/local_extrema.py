# -*- coding: utf-8 -*-
"""
Created on Tue Dec  9 11:03:50 2014

@author: jsgosselin
"""
#----- THIRD PARTY IMPORTS -----

import numpy as np

def local_extrema(x, Deltan):

# LOCAL_EXTREMA Determines the local extrema of a given temporal scale
# n_j = The positions of the local extrema of a partition of scale Deltan
#       as defined at p. 82 in the book [ATE] C. Vamos and M. Craciun,
#       Automatic Trend Estimation, Springer 2012.
#       The positions of the maxima are positive and those of the minima
#       are negative.
# kadd= n_j(kadd) are the local extrema with time scale smaller than Deltan
#       which are added to the partitionsuch that an alternation of maxima
#       and minima is obtained.
# [n_j,kadd]=local_extrema(x,Deltan,ni,nf) determines the partition of
#       scale Deltan of the part x(ni:nf) of the time series x. The
#       algorithm is presented in Appendix E of [ATE].
# [n_j,kadd]=local_extrema(x,Deltan) determines the partition of
#       scale Deltan of the entire time series x
# [n_j,kadd]=local_extrema(x) determines the partition of scale Deltan=1
#       of the entire time series x which contains all the local extrema
    
    N = len(x)
    
    ni = 0
    nf = N-1
    
#----------------------------------------------------------------- PLATEAU -----
    # Recognize the plateaus of the time series x defined in [ATE] p. 85
    # [n1[n],n2[n]] is the interval with the constant value equal with x[n]
    # if x[n] is not contained in a plateau, then n1[n]=n2[n]=n
   
    n1 = np.arange(N)   
    n2 = np.arange(N)
    
    dx = np.hstack((1, np.diff(x)))
    k0 = np.where(dx == 0)[0]

    if len(k0) > 0:

        dk0 = np.diff(k0)
        k1 = np.hstack((np.where(dk0 > 1)[0], len(k0)-1))
        
        ind1 = 0
        for ind2 in k1:
            
            n01 = k0[ind1] - 1
            n02 = k0[ind2]
            n1[n01:n02+1] = n01
            n2[n01:n02+1] = n02
            ind1 = ind2 + 1
        
#-------------------------------------------------------------------------------
    
    # the iterative algorithm presented in Appendix E of [ATE]
    nc = 0    # the time step up to which the time series has been acomplished ([ATE] p. 127)
    Jest = 0  # the number of the local extrema of the partition of scale DeltaN 
    iadd = 0  # number of the additional local extrema
    flagante = 0
    kadd = [] # order number of the additional local extrema between all the local extrema
    n_j = []  # positions of the local extrema of a partition of scale Deltan
    
    while nc < nf:
        
        # [nc+1,nlim] is the interval where the next extremum is searched
        nlim = min(nc + Deltan, nf)   
    
    #------------------------------------------------------- CHECK FOR MIN -----
    
        xmin = np.min(x[nc:nlim+1])
        nmin = np.where(x[nc:nlim+1] == xmin)[0][0] + nc
        
        nlim1 = max(n1[nmin] - Deltan, ni)
        nlim2 = min(n2[nmin] + Deltan, nf)
        
        xminn = np.min(x[nlim1:nlim2+1])
        nminn = np.where(x[nlim1:nlim2+1] == xminn)[0][0] + nlim1 - 1    
        
        # if flagmin = 1 then the minimum at nmin satisfies condition (6.1)
        if nminn == nmin:
            flagmin = 1
        else:
            flagmin = 0
            
    #------------------------------------------------------- CHECK FOR MAX -----
            
        xmax = np.max(x[nc:nlim+1])
        nmax = np.where(x[nc:nlim+1] == xmax)[0][0] + nc   

        nlim1 = max(n1[nmax] - Deltan, ni)        
        nlim2 = min(n2[nmax] + Deltan, nf)
        
        xmaxx = np.max(x[nlim1:nlim2+1])
        nmaxx = np.where(x[nlim1:nlim2+1] == xmaxx)[0] + nlim1 - 1  
        
        # If flagmax = 1 then the maximum at nmax satisfies condition (6.1)
        if nmaxx == nmax: 
            flagmax = 1
        else: 
            flagmax=0
            
    #---------------------------------------------------------- MIN or MAX -----
            
        # The extremum closest to nc is kept for analysis
        if flagmin == 1 and flagmax == 1:
            if nmin < nmax:
                flagmax = 0
            else:
                flagmin = 0

    #------------------------------------------------------------ FLAGANTE -----
                
        if flagante == 0: # No anterior extremum introduced in the partition
            
            if flagmax == 1:  # Current extremum is a maximum

                nc = n1[nmax]
                flagante = 1
                n_j = np.append(n_j, np.floor((n1[nmax] + n2[nmax]) / 2.))
                Jest += 1 
                
            elif flagmin == 1:  # Current extremum is a minimum

                nc = n1[nmin]
                flagante = -1
                n_j = np.append(n_j, -np.floor((n1[nmin] + n2[nmin]) / 2.))
                Jest += 1

            else: # no extremum

                nc = nc + Deltan
                
        elif flagante == -1: # the anterior extremum is an minimum

            if flagmax == 1: # the current extremum is a maximum
                
                tminante = np.abs(n_j[-1])
                xminante = x[tminante]

                if xminante < xmax:
                    nc = n1[nmax]
                    flagante = 1
                    n_j = np.append(n_j, np.floor((n1[nmax] + n2[nmax]) / 2.))
                    Jest += 1
                    
                else: # the current maximum is smaller than the anterior minimum
                      # an additional maximum is added ([ATE] p. 82 and 83)
                    
                    xmaxx = np.max(x[tminante:nmax+1])
                    nmaxx = np.where(x[tminante:nmax+1] == xmaxx)[0]                
                    nmaxx += tminante - 1
                    
                    nc = n1[nmaxx]
                    flagante = 1
                    n_j = np.append(n_j, np.floor((n1[nmaxx] + n2[nmaxx]) / 2.))
                    Jest += 1
                    
                    kadd = np.append(kadd, Jest-1)
                    iadd += 1
                
            elif flagmin == 1: # the current extremum is also a minimum
                               # an additional maximum is added ([ATE] p. 82)
            
                nc = n1[nmin] - 1
                flagante = 1
                tminante = np.abs(n_j[-1])
                    
                xmax = np.max(x[tminante:nc+1])
                nmax = np.where(x[tminante:nc+1] == xmax)[0]                    
                nmax += tminante - 1
                
                n_j = np.append(n_j, np.floor((n1[nmax] + n2[nmax]) / 2.))                               
                Jest += 1
                
                kadd = np.append(kadd, Jest-1)
                iadd += 1
                
            else:
                nc = nc + Deltan
                
        else: # the anterior extremum is a maximum
        
            if flagmin == 1: # the current extremum is a minimum
                tmaxante = np.abs(n_j[-1])
                xmaxante = x[tmaxante]
                if xmaxante > xmin:
                    nc = n1[nmin]
                    flagante = -1
                    
                    n_j = np.append(n_j, -np.floor((n1[nmin] + n2[nmin]) / 2.))
                    Jest += 1
                    
                else: # the current minimum is larger than the anterior maximum
                      # an additional minimum is added ([ATE] p. 82 and 83)
                    xminn = np.min(x[tmaxante:nmin+1])  
                    nminn = np.where(x[tmaxante:nmin+1] == xminn)[0]
                    nminn += tmaxante - 1
                    nc = n1[nminn]
                    flagante = -1
                    
                    n_j = np.append(n_j, -np.floor((n1[nminn] + n2[nminn]) / 2.))                
                    Jest = Jest + 1

                    kadd = np.append(kadd, Jest-1)                
                    iadd += 1
                    
            elif flagmax == 1: # the current extremum is also an maximum
                               # an additional minimum is added ([ATE] p. 82)
                nc = n1[nmax] - 1
                flagante = -1
                tmaxante = np.abs(n_j[-1])
                
                xmin = np.min(x[tmaxante:nc+1])
                nmin = np.where(x[tmaxante:nc+1] == xmin)[0]            
                nmin += tmaxante - 1
                
                n_j = np.append(n_j, -np.floor((n1[nmin] + n2[nmin]) / 2.))
                Jest += 1
                
                kadd = np.append(kadd, Jest-1)
                iadd += 1
                
            else:
                nc = nc + Deltan
            
    # x(ni) is not included in the partition of scale Deltan 
    nj1 = np.abs(n_j[0])
    if nj1 > ni:
        if n1[nj1] > ni: # the boundary ni is not included in the plateau
                         # containing the first local extremum at n_j[1] and it
                         # is added as an additional local extremum ([ATE] p. 83)
            n_j = np.hstack((-np.sign(n_j[0]) * ni, n_j))
            Jest += 1
            
            kadd = np.hstack((0, kadd + 1))
            iadd += 1

        else: # the boundary ni is included in the plateau containing
              # the first local extremum at n_j(1) and then the first local
              # extremum is moved at the boundary of the plateau
            n_j[0] = np.sign(n_j[0]) * ni
   
   
#    # the same situation as before but for the other boundary nf
#    njJ = np.abs(n_j[Jest])
#    if njJ < nf:
#        if n2[njJ] < nf:
#            n_j = np.append(n_j, -np.sign(n_j[Jest]) * nf)
#            Jest += 1
#
#            kadd = np.append(kadd, Jest)
#            iadd += 1
#        else:
#            n_j[Jest] = np.sign(n_j[Jest]) * nf
   
    return n_j, kadd
    
if __name__ == '__main__':
    
    from matplotlib import pyplot as plt
    import xlrd
    
    plt.close('all')

    fname = 'PO16A.xls'
    DATA1 = xlrd.open_workbook(fname)

    TIME1 = DATA1.sheet_by_index(0).col_values(0, start_rowx=11, end_rowx=None) 
    TIME1 = np.array(TIME1)

    water_lvl = DATA1.sheet_by_index(0).col_values(1, start_rowx=11, end_rowx=None) 
    water_lvl = np.array(water_lvl).astype('float')
    
    nonanindx = np.where(~np.isnan(water_lvl))
    water_lvl = np.interp(TIME1, TIME1[nonanindx], water_lvl[nonanindx])
   
    Deltan = 4
    n_j, kadd = local_extrema(-water_lvl, Deltan)
    
    plt.figure()
    plt.plot(TIME1, -water_lvl, '-')
    
    n_j = np.abs(n_j).astype(int)
    kadd = np.abs(kadd).astype(int)
    
    print n_j
    
    plt.plot(TIME1[n_j], -water_lvl[n_j], 'or')
    plt.plot(TIME1[kadd], -water_lvl[kadd], 'og')  
    
    
    