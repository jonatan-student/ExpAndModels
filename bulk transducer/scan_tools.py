import scipy.io as sio
import os
import glob
import numpy as np
import copy
import pandas as pd

def set_path(path):
    global _globalpath
    _globalpath=path
    

# %%
def scan_load(num, *vararg, filename="datfile",path="",top_function="",reorganize_ts_data=True,reorganize_clock=False):
    global globalpath 

    # use vallue from globalpath or set to currentfolder if no path is set
    if path=="" and "_globalpath" in globals():
        path=_globalpath
    elif path=="":
        path="."
    
    # check for start, end syntax
    if isinstance(num,int) and len(vararg)==0:
        num=[num] # one file is loaded
    elif isinstance(num,int) and len(vararg)==1:
        num=range(num,vararg[0]+1) #start ->  end is loaded
    # default is that num is a list (or range)
    #print(num)

    res=[]     
    for n in num:             
        file=os.path.join(path, filename+"_"+f"{n:06d}"+".mat")
        if os.path.isfile(file):
            d=sio.loadmat(file, struct_as_record=False, squeeze_me=True)        
            if top_function == '' or d['res'].top_function == top_function:
                res.append(d['res'])            
                print("File: " + file + " loaded. top_function: "+ d['res'].top_function)
        else:
            file_search=os.path.join(path, "*_"+f"{n:06d}"+".mat")                    
            files=glob.glob(file_search)
            if len(files)==1:                
                d=sio.loadmat(files[0], struct_as_record=False, squeeze_me=True)        
                if top_function == '' or d['res'].top_function == top_function:
                    res.append(d['res'])                
                    print("File: " + files[0] + " loaded . top_function: "+ d['res'].top_function + " (name identified from number)")
            else:
                print("No or multiple file(s) with numer: " + str(num))
        
#    if len(res)==1:
#        res=res[0] # if only one file is loaded retur is and not a list

    if reorganize_ts_data :
        for r in res:
            if r.top_function == 'measure_timeseries':
                r.data=ts_data_reorganize(r.data)
            if r.top_function == 'measure_MR_AH_fast' or r.top_function == 'measure_MR_AH_fast_jump' :
                if not hasattr(r,'data'):
                    fast_data_load(r,path) 
                else:
                    r.data=ts_data_reorganize(r.data)
    if reorganize_clock :
        for r in res: 
            if hasattr(r,'time_before'):
                r.time_before=convert_matlab_clock(r.time_before)
            if hasattr(r,'time_after'):
                r.time_after=convert_matlab_clock(r.time_after)
            if r.top_function == 'measure_timeseries' and hasattr(r.data,'t'):
                r.data.t=convert_matlab_clock(r.data.t)
    
    return res

# %%
def ts_to_array(data, field):    
    # works on single numbers and ndarrays (e.g. from date)
    #if isinstance((getattr(data[0],field)), (float, int)):
        tmp=np.array([getattr(d, field) for d in data])
        return tmp
        
# %% 
def ts_data_reorganize(data):
    tmp=copy.copy(data[0])
    for field in tmp._fieldnames :
        setattr(tmp, field, ts_to_array(data,field))
    return tmp

# %% 
def fast_data_load(data,path):
    if not hasattr(data,'data'):
        textname=os.path.basename(data.FileName)[0:-4] + '.txt' 
        textfile=os.path.join(path, textname)
        if os.path.isfile(textfile):
            pd_data=pd.read_csv(textfile , sep=';' , header=None)
            print("File:" + textfile + " loaded")
            #fast_data = {
            #"c" : pd.Series.to_numpy(pd_data[0])+1j*pd.Series.to_numpy(pd_data[1]),
            #"cur" : pd.Series.to_numpy(pd_data[3]) ,
            #"cnt" : pd.Series.to_numpy(pd_data[4]) , 
            #"PV"  : pd.Series.to_numpy(pd_data[5]) , 
            #    }
            fast_data=sio.matlab.mio5_params.mat_struct()
            fast_data._fieldnames=[]
            fast_data.c=  pd.Series.to_numpy(pd_data[0])+1j*pd.Series.to_numpy(pd_data[1])
            fast_data._fieldnames.append('c')
            fast_data.cur = pd.Series.to_numpy(pd_data[3]) 
            fast_data._fieldnames.append('cur')
            fast_data.cnt = pd.Series.to_numpy(pd_data[4])  
            fast_data._fieldnames.append('cnt')
            fast_data.PV = pd.Series.to_numpy(pd_data[5])             
            fast_data._fieldnames.append('PV')
            fast_data.SP = pd.Series.to_numpy(pd_data[6])             
            fast_data._fieldnames.append('SP')
            fast_data.etime=(fast_data.cnt-fast_data.cnt[0])/10
            fast_data._fieldnames.append('etime')
            data.data=fast_data
            data._fieldnames.append('data')
        else:
            print("File:" + textfile + " does not exits")
            
        return fast_data , pd_data
        
# %%
def convert_matlab_clock(mcl):
    if mcl.ndim == 1:
        a=mcl
        time_array=np.array([f'{int(a[0])}-{int(a[1]):02d}-{int(a[2]):02d}T{int(a[3]):02d}:{int(a[4]):02d}:{int(np.floor(a[5])):02d}.{str(a[5]-int(a[5]))[2:8]}'],dtype='datetime64')    
    else:
        time_array=np.array([f'{int(a[0])}-{int(a[1]):02d}-{int(a[2]):02d}T{int(a[3]):02d}:{int(a[4]):02d}:{int(np.floor(a[5])):02d}.{str(a[5]-int(a[5]))[2:8]}' for a in mcl],dtype='datetime64')    
    return time_array

def etime(T0,T):
    DT=(T-T0)/np.timedelta64(1, 's')
    return DT