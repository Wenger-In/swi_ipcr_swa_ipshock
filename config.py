# -*- coding: utf-8 -*-
"""
  @date    : 2021/5/12 11:10
  @author  : baizhaofeng
  @email   : zfengbai@gmail.com
  @file    : config.py
"""

# 算法名称
algName = "swi_ipcr_swa_ipshock"

# 算法关键步骤
keySteps = [
    "数据读取",
    "绘制图像"
    "输出参数",
    ]

# 入口json标签
labels = [
    "input",
    "output",
    ]
    
# 算法返回状态码
statusDict = {
    "0":"算法执行成功",
    "1":"算法执行失败",
    "2":"参数传入异常",
    "3":"时间异常",
    "4":"区域异常",
    "5":"输入数据不足",
    "6":"输入数据不存在",
    "7":"静态数据异常",
    "8":"数据损坏异常",
    "9":"无效数据异常",
    }
