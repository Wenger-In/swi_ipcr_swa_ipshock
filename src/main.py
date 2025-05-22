# -*- coding: utf-8 -*-
"""
@date    : 2022-01-03 16:45
@file    : main.py
"""
###############################################################################
import os
from swpy.base import glo
from swpy.common.project_SWI import split_filename, get_savepath, get_productId
from src.sub import *
import onnxruntime as ort


###############################################################################

def main(inputDic, outputDic):
    rjson = glo.get_value("rjson")
    fjson = glo.get_value("fjson")
    statusDict = glo.get_value("statusDict")

    # 【1】读取输入数据
    fjson.log("开始读取输入数据...")
    magFile = inputDic['MAG']['fullpaths'][0]
    fcupFile = inputDic['FARADAYCUP']['fullpaths'][0]
    field_dic_json = split_filename(magFile)
    codeId, data = read_data(magFile, fcupFile)
    if codeId != "0":
        return codeId
    fjson.info("完成读取输入数据!")

    # 【2】绘制图像
    fjson.log("开始绘制图像...")
    outputDir = outputDic["outputDir"]
    time_stamp_arr = data[0].filled().astype('datetime64[s]')
    time_beg = time_stamp_arr[0]
    time_end = time_stamp_arr[-1]
    temp_time_beg = time_beg
    temp_time_end = temp_time_beg + 20 * 60
    shock_time_list = []
    shock_para_list = []
    last_shock_time = np.datetime64('1970-01-01T00:00:00+0000')
    while True:
        # Load 20 minute data
        mask = (time_stamp_arr >= temp_time_beg) & (time_stamp_arr <= temp_time_end)
        temp_data0 = data[:, mask]
        # Make zscore data
        temp_data_flag, temp_data = check_input_data(temp_data0)
        if temp_data_flag == 1:  # no missing data
            zs_data = make_zscore_data(temp_data)
            input_net_data = np.transpose(zs_data.astype(np.float32))
            input_net_data = np.expand_dims(input_net_data, 1)
            # load NN and check shock
            ort_sess = ort.InferenceSession('input\shock_checking.onnx')
            ort_inputs = {ort_sess.get_inputs()[0].name: input_net_data}
            output_name = ort_sess.get_outputs()[0].name
            outputs = ort_sess.run([output_name], ort_inputs)
            # find shock time if have shock
            if outputs[0][0][0] < outputs[0][0][1]:
                shock_pos = find_shock_pos(temp_data[3], n_windows=3)  # temp_data[3]: Btot
                sub_datetime = np.array(temp_data[0], dtype='datetime64[s]')
                shock_time = (sub_datetime[shock_pos] - sub_datetime[shock_pos - 1]) / 2 + sub_datetime[shock_pos]
                if last_shock_time < shock_time:
                    field_dic_png = {
                        "pflag": "Z",
                        "product_identifier": "SWGO",
                        "oflag": "C",
                        "originator": "DSCOVR",
                        "creat_time": dt.datetime.utcnow().strftime('%Y%m%d000000'),
                        "ftype": "P",
                        "device_name": field_dic_json["device_name"],
                        "device_id": field_dic_json["device_id"],
                        "product_name": "IPShock",
                        "product_level": "L2",
                        "observation_start": (shock_time - 30 * 60).item().strftime('%Y%m%d%H%M%S'),
                        "observation_duration": "1H",
                        "Auxiliary": field_dic_json["Auxiliary"],
                        "project": field_dic_json["project"],
                        "construction_unit": field_dic_json["construction_unit"],
                        "version_number": "V1A",
                        "type": "PNG",
                        "field": "IPCR",
                    }

                    savepath_png = get_savepath(outputDir, field_dic_png)
                    productIdENG_png = get_productId(field_dic_png)

                    temp_shock_para = make_shock_plot(shock_time, data, savepath_png)

                    if temp_shock_para['shock_flag'] == 1:
                        shock_time_list.append(shock_time)
                        shock_para_list.append(temp_shock_para)
                        last_shock_time = shock_time
                        resultInfo = {
                            "filePath": savepath_png,
                            "productIdENG": productIdENG_png,
                            "productIdCHN": '行星际激波图像产品',
                            "productLevel": field_dic_png["product_level"][0:2],
                            "productFormat": field_dic_png["type"],
                            "IsParsing": False}
                        rjson.info('result', resultInfo)

        # move to next time interval (5 minute)
        temp_time_beg = temp_time_beg + 5 * 60
        temp_time_end = temp_time_beg + 20 * 60
        if temp_time_end > time_end:
            break


    # field_dic_png = {
    #     "pflag": "Z",
    #     "product_identifier": "SWGO",
    #     "oflag": "C",
    #     "originator": "DSCOVR",
    #     "creat_time": dt.datetime.utcnow().strftime('%Y%m%d000000'),
    #     "ftype": "P",
    #     "device_name": field_dic_json["device_name"],
    #     "device_id": field_dic_json["device_id"],
    #     "product_name": "IPShock",
    #     "product_level": "L2",
    #     "observation_start": field_dic_json["observation_start"],
    #     "observation_duration": field_dic_json["observation_duration"],
    #     "Auxiliary": field_dic_json["Auxiliary"],
    #     "project": field_dic_json["project"],
    #     "construction_unit": field_dic_json["construction_unit"],
    #     "version_number": "V1A",
    #     "type": "PNG",
    #     "field": "IPCR",
    # }
    #
    # savepath_png = get_savepath(outputDir, field_dic_png)
    # productIdENG_png = get_productId(field_dic_png)

    #    savepath = plot_fig(data, savepath_png)
    resultInfo = {
        "filePath": savepath_png,
        "productIdENG": productIdENG_png,
        "productIdCHN": '行星际激波图像产品',
        "productLevel": field_dic_png["product_level"][0:2],
        "productFormat": field_dic_png["type"],
        "IsParsing": False}
    rjson.info('result', resultInfo)

    fjson.log("完成绘制图像！")
    fjson.log("开始生成事件列表...")
    if shock_time_list == []:
        fjson.log("该时间范围内无激波事件！")
        fjson.info("该时间范围内无激波事件！")
    else:
        field_dic_json = {
            "pflag": "Z",
            "product_identifier": "SWGO",
            "oflag": "C",
            "originator": "DSCOVR",
            "creat_time": dt.datetime.utcnow().strftime('%Y%m%d000000'),
            "ftype": "P",
            "device_name": field_dic_json["device_name"],
            "device_id": field_dic_json["device_id"],
            "product_name": "IPShock_EVENT_LIST",
            "product_level": "L2",
            "observation_start": (shock_time - 30 * 60).item().strftime('%Y%m%d000000'),
            "observation_duration": "1d",
            "Auxiliary": field_dic_json["Auxiliary"],
            "project": field_dic_json["project"],
            "construction_unit": field_dic_json["construction_unit"],
            "version_number": "V1A",
            "type": "JSON",
            "field": "IPCR",
        }

        savepath_json = get_savepath(outputDir, field_dic_json)
        productIdENG_json = get_productId(field_dic_json)
        result_dict = make_event_dict(shock_time_list, shock_para_list)
        jtext = json.dumps(result_dict)
        with open(savepath_json,'w',encoding='utf8') as f_json:
            json.dump(jtext,f_json,indent=2)
        resultInfo = {
            "filePath": savepath_json,
            "productIdENG": productIdENG_json,
            "productIdCHN": '行星际激波事件列表产品',
            "productLevel": field_dic_png["product_level"][0:2],
            "productFormat": field_dic_png["type"],
            "IsParsing": False}
        fjson.log("完成生成事件列表！")
        rjson.info('result', resultInfo)
        fjson.info("完成图像绘制与生成事件列表！")

    return codeId
