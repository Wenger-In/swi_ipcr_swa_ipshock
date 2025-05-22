# -*- coding: utf-8 -*-
"""
  @date    : 2022-01-01
  @author  : dduan
  @file    : gen_args.py
"""

import os
import sys
import json 
import datetime

def get_input_args(*args):
    # 功能：获取输入文件路径
    inputArgs={ 
        "MAG": {
            "fullpaths":["input\TestData\Z_MAG_C_DSCOVR_20170429000000_O_SNO_00_SNOBSERV_L0_17000101000000_00322Y_OTHER_TEST_TESTGROUP_V0.nc"],
            'labels':{},
            },
        "FARADAYCUP": {
            "fullpaths":["input\TestData\Z_FARADAYCUP_C_DSCOVR_20170429000000_O_SNO_00_SNOBSERV_L0_17000101000000_00322Y_OTHER_TEST_TESTGROUP_V0.nc"],
            'labels':{},
            },
        }
                
    return inputArgs
    
def get_output_args(*args):
    # 功能：获取输出文件路径
    outputDir       ="output/"
    resultJsonFile  ='log/result.json'
    resultLogFile   ='log/log.log'
    resultFlowFile  ='log/flow.json'
    
    outputArgs={
        "outputDir":outputDir,
        "resultJsonFile":resultJsonFile,
        "resultLogFile":resultLogFile,
        "resultFlowFile":resultFlowFile,
        }
    
    return outputArgs

def gen_args(args_json,*args):
    # 功能：生成app.py的json格式输入文件
    
    inputArgs =get_input_args(*args)
    outputArgs=get_output_args(*args)
    
    args_dic={"input":inputArgs,"output":outputArgs,}
    print(args_dic)
        
    with open(args_json,'w',encoding='utf-8') as f:
        json.dump(args_dic,f,ensure_ascii=False)
    
    return 

if __name__ == '__main__':
    # 获取当前文件上一级路径
    curr_dir=os.path.dirname(os.path.realpath(__file__))
    work_dir=os.path.join(curr_dir, "../")
    
    # 生成的输入参数json文件
    args_json=os.path.join(curr_dir,'app_args.json')
    gen_args(args_json)