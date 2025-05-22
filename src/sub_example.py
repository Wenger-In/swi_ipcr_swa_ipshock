# coding=utf-8
# date: 2021-09-19
###############################################################################
import os,sys
import time,datetime
import json
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MultipleLocator, FormatStrFormatter, AutoMinorLocator
    
# matplotlib添加字体
curr_dir=os.path.dirname(os.path.realpath(__file__))    # 当前文件目录
swpkg_path=curr_dir+"/../../../"                        # swpkg目录
import matplotlib.font_manager as font_manager
font_manager.fontManager.addfont(swpkg_path+'/swpy/static/font/msyh.ttc') 

# matplotlib中文显示
matplotlib.rcParams['xtick.direction'] = 'in' 
matplotlib.rcParams['ytick.direction'] = 'in'
plt.rcParams['font.sans-serif'] = ['Microsoft Yahei']   # 用来正常显示中文
plt.rcParams['axes.unicode_minus'] = False              # 用来正常显示负号
###############################################################################
        
def read_data(fullpath):
    # 功能: 读取数据
    
    if not os.path.exists(fullpath):
        data=[]
        codeId="6"
        return codeId,data
        
    fid=open(fullpath,'rb')
    json_data=json.load(fid)
    
    time_tags_long,fluxs_long=[],[]
    time_tags_short,fluxs_short=[],[]
    for id in range(len(json_data)):
        # {
            # "time_tag": "2021-09-19T21:42:00Z",
            # "satellite": 16,
            # "flux": 5.6853906471587834e-08,
            # "observed_flux": 8.174998100685116e-08,
            # "electron_correction": 2.4896074535263324e-08,
            # "electron_contaminaton": false,
            # "energy": "0.1-0.8nm"
        # }
        energy=json_data[id]['energy']
        time_tag=datetime.datetime.strptime(json_data[id]['time_tag'],'%Y-%m-%dT%H:%M:%SZ')
        flux=float(json_data[id]['flux'])
        if energy=="0.1-0.8nm":
            time_tags_long.append(time_tag)
            fluxs_long.append(flux)
        else:
            time_tags_short.append(time_tag)
            fluxs_short.append(flux)
            
    codeId="0"
    data = {
        'time_tags_long':time_tags_long,
        'fluxs_long':fluxs_long,
        'time_tags_short':time_tags_short,
        'fluxs_short':fluxs_short,
        }
        
    return codeId,data


def plot_fig(data,savepath):
    # 功能: 生成图像产品

    measures={'L1':1E-8,
            'L2':1E-7,
            'L3':1E-6,
            'L4':1E-5,
            'L5':1E-4,}
        
    levels={'L1':'A',
            'L2':'B',
            'L3':'C',
            'L4':'M',
            'L5':'X',}
            
    time_tags_long=data['time_tags_long']
    time_tags_short=data['time_tags_short']
    fluxs_long=np.array(data['fluxs_long'])
    fluxs_short=np.array(data['fluxs_short'])
    
    fig=plt.figure(figsize=(8,6), dpi=150) 
    ax1=plt.subplot(1,1,1)
        
    plt.semilogy(time_tags_long,fluxs_long)
    plt.semilogy(time_tags_short,fluxs_short)
        
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.xlim([time_tags_long[0],time_tags_long[-1]])
    plt.ylim([1E-9,1E-3])
    plt.xlabel(u'UTC',fontsize=10)
    plt.ylabel(u'Flux (W/$m^2$)',fontsize=10)
    plt.title('GOES卫星X射线通量',fontsize=12)
    ax1.xaxis.set_minor_locator(AutoMinorLocator(12))
    ax1.tick_params(which='major',length=6)
    ax1.tick_params(which='minor',length=3)
    legend=plt.legend(['long','short'],loc=2,framealpha=0.1)
    
    ax2=ax1.twinx()
    plt.semilogy(time_tags_long,fluxs_long*0+5E-5,'w',linewidth=1)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    plt.ylim([1E-9,1E-3])
    plt.grid()
    ax2.set_yticks([measures[key] for key in measures])
    ax2.set_yticklabels([levels[key] for key in levels])
    ax2.tick_params(which='major',length=6)
    ax2.tick_params(which='minor',length=3)
    
    plt.savefig(savepath, transparent = True)
    # plt.show()
    plt.close()
    
    return savepath

###############################################################################

if __name__ == '__main__':

    input_fullpath="../input/Z_SWGO_I_GOESP_20210919000000_O_XRS-_00_XRAY_L2_20210919000000_00006H_OTHER_WEBB_SWPC_V1A.json"
    codeId,data=read_data(input_fullpath)
    
    output_fullpath="../output/Z_SWGO_I_GOESP_20210919000000_O_XRS-_00_XRAY_L2_20210919000000_00006H_OTHER_WEBB_SWPC_V1A.PNG"
    plot_fig(data,output_fullpath)