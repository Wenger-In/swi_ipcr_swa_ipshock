# -*- coding: utf-8 -*-
"""
@date    : 2022-01-03 16:45
@file    : main.py
"""
###############################################################################
import os
from swpy.base import glo
from swpy.common.project_SWI import split_filename,get_savepath,get_productId
from src.sub import *
###############################################################################

def main(inputDic, outputDic):
    rjson = glo.get_value("rjson")
    fjson = glo.get_value("fjson")
    statusDict = glo.get_value("statusDict")
    
    #【1】读取输入数据
    fjson.log("开始读取输入数据...")
    xrayFile=inputDic['XRAY']['fullpaths'][0]
    field_dic_json=split_filename(xrayFile)
    codeId,data=read_data(xrayFile)
    if codeId!="0":
        return codeId
    fjson.info("完成读取输入数据!")
    
    #【2】绘制图像
    fjson.log("开始绘制图像...")
    outputDir=outputDic["outputDir"]
    
    field_dic_png = {
        "pflag"                 :"Z",
        "product_identifier"    :"SWGO",
        "oflag"                 :"C",
        "originator"            :"GOESP",
        "creat_time"            :datetime.datetime.utcnow().strftime('%Y%m%d000000'),
        "ftype"                 :"P",
        "device_name"           :field_dic_json["device_name"],
        "device_id"             :field_dic_json["device_id"],
        "product_name"          :"IPShock",
        "product_level"         :"L2",
        "observation_start"     :field_dic_json["observation_start"],
        "observation_duration"  :field_dic_json["observation_duration"],
        "Auxiliary"             :field_dic_json["Auxiliary"],
        "project"               :field_dic_json["project"],
        "construction_unit"     :field_dic_json["construction_unit"],
        "version_number"        :"V1A",
        "type"                  :"PNG",
        "field"                 :"IPCR",
        }
    
    savepath_png=get_savepath(outputDir,field_dic_png)
    productIdENG_png=get_productId(field_dic_png)
    
    savepath=plot_fig(data,savepath_png)
    resultInfo = {
        "filePath"      : savepath_png,
        "productIdENG"  : productIdENG_png,
        "productIdCHN"  : '行星际激波图像产品',
        "productLevel"  : field_dic_png["product_level"][0:2],
        "productFormat" : field_dic_png["type"],
        "IsParsing"     : False}
    rjson.info('result',resultInfo)
    
    fjson.info("完成绘制图像！")
    
    return codeId