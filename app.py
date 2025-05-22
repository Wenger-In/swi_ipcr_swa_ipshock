# -*- coding: utf-8 -*-
"""
  @date    : 2021/3/18 9:43
  @author  : baizhaofeng
  @email   : zfengbai@gmail.com
  @file    : app.py
"""

import os
import sys
curr_dir=os.path.dirname(os.path.realpath(__file__))    # 当前文件目录
swpkg_path=curr_dir+"/../../"                           # swpkg目录
sys.path.append(swpkg_path)

import time
import json
import traceback
from swpy.base.api import ResultJson, FlowJson
from swpy.base import glo
from config import algName, keySteps, labels, statusDict
from src.main import main


def app(jsonpath):
    starttime = time.time()

    # 解析传入json文件
    with open(jsonpath, "rb") as fid:
        jsondict = json.load(fid)
    
    # 记录算法运行结果的json
    resultJsonFile=jsondict["output"]["resultJsonFile"]
    rjson = ResultJson(resultJsonFile)
    
    # 记录算法运行流程的json和日志
    resultLogFile=jsondict["output"]["resultLogFile"]
    resultFlowFile=jsondict["output"]["resultFlowFile"]
    fjson = FlowJson(algName, keySteps, resultFlowFile, resultLogFile)

    # 设置为全局变量，方便在其他模块调用
    glo._init()
    glo.set_value("rjson", rjson)
    glo.set_value("fjson", fjson)
    glo.set_value("statusDict", statusDict)

    try:
        args = [jsondict[label] for label in labels]
        # 调用主函数
        codeId=main(*args)
    except KeyError as ke:
        fjson.info(str(ke),'2')
        rjson.info('status', ['2', "参数传入异常!"])
        sys.exit()
    except Exception as ex:
        print(traceback.format_exc())
        fjson.info(str(ex),'1')
        rjson.info('status', ['1', "算法执行失败"])
    else:
        endtime = time.time()
        costtime = endtime - starttime
        if codeId=="0":
            # 将状态写入json文件,0表示成功
            fjson.log("算法执行成功，总用时：%.2f秒" % (costtime))
            rjson.info('status', ['0', '%s 执行成功 !' % algName])
        else:
            # 将状态写入json文件
            fjson.log("算法执行失败，总用时：%.2f秒" % (costtime))
            rjson.info('status', [codeId, '%s 执行失败 !' % algName])
    finally:
        rjson.write()

################################################################################
if __name__ == '__main__':
    # 传入json文件
    if len(sys.argv)>1:
        jsonPath = sys.argv[1]
    else:
        jsonPath=os.path.join(curr_dir,'args/app_args.json') 
    
    # 调用
    # print(jsonPath)
    sys.exit(app(jsonPath))
