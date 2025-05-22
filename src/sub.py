# coding=utf-8
# date: 2021-09-19
###############################################################################
import os, sys
import time
import datetime as dt
import json
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MultipleLocator, FormatStrFormatter, AutoMinorLocator
# import netCDF4 as nc
from scipy.stats import zscore
from matplotlib.dates import DateFormatter
import fnmatch

# matplotlib添加字体
curr_dir = os.path.dirname(os.path.realpath(__file__))  # 当前文件目录
swpkg_path = curr_dir + "/../../../"  # swpkg目录
import matplotlib.font_manager as font_manager

font_manager.fontManager.addfont(swpkg_path + '/swpy/static/font/msyh.ttc')

# matplotlib中文显示
matplotlib.rcParams['xtick.direction'] = 'in'
matplotlib.rcParams['ytick.direction'] = 'in'
plt.rcParams['font.sans-serif'] = ['Microsoft Yahei']  # 用来正常显示中文
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号


###############################################################################
def make_zscore_data(data):  # [B,n,V,T,Sp]
    # 功能：把数据转为zscore输入神经网络
    B = data[3]
    n = data[1]
    V = data[7]
    T = data[2] * 11605
    Sp = np.log(T ** 1.5 / n)
    return zscore(np.stack((B, n, V, T, Sp)), axis=1, ddof=1)


def find_shock_pos(B_tot, n_windows=3):
    # 功能：寻找激波位置在数组中的序号
    B_movmean = np.convolve(B_tot, np.ones(n_windows) / n_windows, mode='valid')
    B1_movmean = B_movmean[0:-3]
    B2_moveman = B_movmean[2:-1]
    dB = 2 * np.abs(B2_moveman - B1_movmean) / (B2_moveman + B1_movmean)
    max_index = dB.argmax()
    return max_index + n_windows - 2


def check_input_data(maData):
    err_num_arr = np.sum(maData.mask, axis=1)
    good_flag_vec = ~maData[1].mask
    data_len = good_flag_vec.__len__()
    for i in range(2, 8):
        good_flag_vec = good_flag_vec & (~maData[i].mask)
    check_flag = 1
    max_good_num_withoutVxyz = np.sum(good_flag_vec)
    if max_good_num_withoutVxyz < 0.7 * data_len:
        check_flag = 2  # missing data
    else:
        new_data = maData[:, good_flag_vec]
    new_data = new_data.filled()
    return check_flag, new_data


def read_data(magfile, pfile):
    if not os.path.exists(magfile):
        data = []
        codeId = "6"
        return codeId, data
    if not os.path.exists(pfile):
        data = []
        codeId = "6"
        return codeId, data
    check_flag = 1

    B_nc = nc.Dataset(magfile)
    B_epoch = B_nc.variables['time'][:]
    B_tot = B_nc.variables['bt'][:]
    B_x = B_nc.variables['bx_gse'][:]
    B_y = B_nc.variables['by_gse'][:]
    B_z = B_nc.variables['bz_gse'][:]

    p_nc = nc.Dataset(pfile)
    p_epoch = p_nc.variables['time'][:]
    p_vx = p_nc.variables['proton_vx_gse'][:]
    p_vy = p_nc.variables['proton_vy_gse'][:]
    p_vz = p_nc.variables['proton_vz_gse'][:]
    p_vtot = p_nc.variables['proton_speed'][:]
    p_n = p_nc.variables['proton_density'][:]
    p_T = p_nc.variables['proton_temperature'][:]

    Data = np.ma.stack((B_epoch / 1000, p_n, p_T / 11605,
                        B_tot, B_x, B_y, B_z,
                        p_vtot, p_vx, p_vy,
                        p_vz))  # Units: Time: timestamp, n:cm-3, T: eV, B: nT, V: km/s in GSE frame
    Data.set_fill_value(1e10)
    # Data = np.stack((B_epoch.filled() / 1000, p_n.filled(), p_T.filled() / 11605,
    #                  B_tot.filled(), B_x.filled(), B_y.filled(), B_z.filled(),
    #                  p_vtot.filled(), p_vx.filled(), p_vy.filled(),
    #                  p_vz.filled()))  # Units: Time: timestamp, n:cm-3, T: eV, B: nT, V: km/s in GSE frame

    check_flag, data = check_input_data(Data)
    if check_flag == 2:
        codeId = "5"
    else:
        codeId = "0"
    return codeId, Data


def make_shock_plot(shock_time, data, savepath,
                    half_minute_width=30, up_minute=2, down_minute=9):
    # 功能：生成图像产品

    plot_beg = shock_time - half_minute_width * 60
    plot_end = shock_time + half_minute_width * 60
    temp_dt = data[0].filled().astype('datetime64[s]')
    mask = (temp_dt >= plot_beg) & (temp_dt <= plot_end)
    temp_data = data[:, mask].filled()
    sub_date = temp_data[0].astype('datetime64[s]')
    # determine upstream and downstream
    up_beg = shock_time - down_minute * 60
    up_end = shock_time - up_minute * 60
    down_beg = shock_time + up_minute * 60
    down_end = shock_time + down_minute * 60
    up_mask = (sub_date >= up_beg) & (sub_date <= up_end)
    down_mask = (sub_date >= down_beg) & (sub_date <= down_end)
    up_data = temp_data[:, up_mask]
    up_arr = up_data.mean(axis=1)
    up_arr = up_arr[1:]
    down_data = temp_data[:, down_mask]
    down_arr = down_data.mean(axis=1)
    down_arr = down_arr[1:]  # [0:n,1:T,2:B,3:Bx,4:By,5:Bz,6:V,7:Vx,8:Vy,9:Vz]
    # calc shock parameters
    if up_arr[0] > down_arr[0]:
        temp = up_arr
        up_arr = down_arr
        down_arr = temp
    if up_arr[6] > down_arr[6]:
        shock_type = 'FR'
    else:
        shock_type = 'FF'
    shock_flag = 1
    vxyz_flag = 1
    if ((down_arr[0] / up_arr[0]) < 1.2) | ((down_arr[2] / up_arr[2]) < 1.2) | (
            (down_arr[1] / up_arr[1]) < (1 / 1.2)) | (np.abs(up_arr[6] - down_arr[6]) < 10):
        shock_flag = -1  # Not shock
    if (up_arr[7] >10000) | (up_arr[8] >10000) | (up_arr[9] >10000) | (down_arr[7] >10000) | (
            down_arr[8] >10000) | (down_arr[9] >10000):
        vxyz_flag = 0  # No Vxyz measurement
    # determine shock normal
    dB_vec = down_arr[3:6] - up_arr[3:6]
    if vxyz_flag == 1:
        dv_vec = down_arr[7:] - up_arr[7:]
        n0 = np.cross(dB_vec, np.cross(dB_vec, dv_vec))
    else:
        n0 = np.cross(dB_vec, np.cross(down_arr[3:6], up_arr[3:6]))
    shock_n = n0 / np.linalg.norm(n0)
    thetaBn = np.arccos(np.abs(np.dot(up_arr[3:6], shock_n)) / np.linalg.norm(up_arr[3:6])) * 180 / np.pi
    shock_para = {'shock_time': shock_time, 'up': up_arr, 'down': down_arr, 'ratio': down_arr / up_arr,
                  'shock_n':shock_n, 'thetaBn': thetaBn,
                  'shock_type': shock_type, 'shock_flag': shock_flag, 'vxyz_flag': vxyz_flag}
    # plot shock and upstream regions
    if shock_flag == 1:
        plt.rcParams['text.usetex'] = True
        fig, axs = plt.subplots(2, 1, sharex=True)
        ax20 = axs[0].twinx()
        axs[0].plot(sub_date, temp_data[3], 'g-')
        ax20.plot(sub_date, temp_data[7], 'b-')
        axs[0].set_ylabel(r'B (nT)', color='g')
        ax20.set_ylabel(r'V (km/s)', color='b')
        plt.title(shock_time.item().strftime('%Y%m%d'))
        ylim = ax20.get_ylim()
        plt.axvline(x=shock_time, color='red', linestyle='dashed')
        plt.axvline(x=up_beg, color='black', linestyle='dashed')
        plt.axvline(x=down_beg, color='black', linestyle='dashed')
        plt.axvline(x=up_end, color='black', linestyle='dashed')
        plt.axvline(x=down_end, color='black', linestyle='dashed')

        ax21 = axs[1].twinx()
        axs[1].plot(sub_date, temp_data[1], 'g-')
        ax21.plot(sub_date, temp_data[2], 'b-')
        axs[1].set_ylabel(r'$N_p$ ($\textrm{cm}^{-3}$)', color='g')
        ax21.set_ylabel(r'$T_p$ (eV)', color='b')
        # fig.tight_layout()
        date_form = DateFormatter("%H:%M")
        ax21.xaxis.set_major_formatter(date_form)
        plt.axvline(x=shock_time, color='red', linestyle='dashed')
        plt.axvline(x=up_beg, color='black', linestyle='dashed')
        plt.axvline(x=down_beg, color='black', linestyle='dashed')
        plt.axvline(x=up_end, color='black', linestyle='dashed')
        plt.axvline(x=down_end, color='black', linestyle='dashed')
        # filename_str = 'shock_' + shock_time.item().strftime('%Y%m%dT%H%M%S') + '.png'
        plt.savefig(savepath, dpi=300)
        plt.close()
    return shock_para


def make_shock_plot_with_load_data(shock_time, half_minute_width=30, up_minute=2, down_minute=9):
    # 功能：生成图像产品
    # load data
    temp_time = shock_time.astype(dt.datetime)
    temp_time = dt.datetime(temp_time.year, temp_time.month, temp_time.day, temp_time.hour, temp_time.minute,
                            temp_time.second, tzinfo=dt.timezone.utc)
    plot_beg = temp_time - dt.timedelta(minutes=half_minute_width)
    plot_end = temp_time + dt.timedelta(minutes=half_minute_width)
    temp_data = load_data(plot_beg, plot_end)
    temp_data_flag, temp_data = check_input_data(temp_data)
    sub_date = temp_data[0].astype('datetime64[s]')
    # determine upstream and downstream
    up_beg = shock_time - down_minute * 60
    up_end = shock_time - up_minute * 60
    down_beg = shock_time + up_minute * 60
    down_end = shock_time + down_minute * 60
    up_mask = (sub_date >= up_beg) & (sub_date <= up_end)
    down_mask = (sub_date >= down_beg) & (sub_date <= down_end)
    up_data = temp_data[:, up_mask]
    up_arr = up_data.mean(axis=1)
    up_arr = up_arr[1:]
    down_data = temp_data[:, down_mask]
    down_arr = down_data.mean(axis=1)
    down_arr = down_arr[1:]  # [0:n,1:T,2:B,3:Bx,4:By,5:Bz,6:V,7:Vx,8:Vy,9:Vz]
    # calc shock parameters
    if up_arr[0] > down_arr[0]:
        temp = up_arr
        up_arr = down_arr
        down_arr = temp
    if up_arr[6] > down_arr[6]:
        shock_type = 'FR'
    else:
        shock_type = 'FF'
    shock_flag = 1
    vxyz_flag = 1
    if ((down_arr[0] / up_arr[0]) < 1.2) | ((down_arr[2] / up_arr[2]) < 1.2) | (
            (down_arr[1] / up_arr[1]) < (1 / 1.2)) | (np.abs(up_arr[6] - down_arr[6]) < 10):
        shock_flag = -1  # Not shock
    if (up_arr[7] >10000) | (up_arr[8] >10000) | (up_arr[9] >10000) | (down_arr[7] >10000) | (
            down_arr[8] >10000) | (down_arr[9] >10000):
        vxyz_flag = 0  # No Vxyz measurement
    # determine shock normal
    dB_vec = down_arr[3:6] - up_arr[3:6]
    if vxyz_flag == 1:
        dv_vec = down_arr[7:] - up_arr[7:]
        n0 = np.cross(dB_vec, np.cross(dB_vec, dv_vec))
    else:
        n0 = np.cross(dB_vec, np.cross(down_arr[3:6], up_arr[3:6]))

    shock_n = n0 / np.linalg.norm(n0)
    thetaBn = np.arccos(np.abs(np.dot(up_arr[3:6], shock_n)) / np.linalg.norm(up_arr[3:6])) * 180 / np.pi
    shock_para = {'shock_time': shock_time, 'up': up_arr, 'down': down_arr, 'ratio': down_arr / up_arr,
                  'shock_n':shock_n,'thetaBn': thetaBn,
                  'shock_type': shock_type, 'shock_flag': shock_flag, 'vxyz_flag': vxyz_flag}
    # plot shock and upstream regions
    if shock_flag == 1:
        plt.rcParams['text.usetex'] = True
        fig, axs = plt.subplots(2, 1, sharex=True)
        ax20 = axs[0].twinx()
        axs[0].plot(sub_date, temp_data[3], 'g-')
        ax20.plot(sub_date, temp_data[7], 'b-')
        axs[0].set_ylabel(r'B (nT)', color='g')
        ax20.set_ylabel(r'V (km/s)', color='b')
        plt.title('Interplanetary Shock-' + shock_time.item().strftime('%Y%m%d'))
        ylim = ax20.get_ylim()
        plt.axvline(x=shock_time, color='red', linestyle='dashed')
        plt.axvline(x=up_beg, color='black', linestyle='dashed')
        plt.axvline(x=down_beg, color='black', linestyle='dashed')
        plt.axvline(x=up_end, color='black', linestyle='dashed')
        plt.axvline(x=down_end, color='black', linestyle='dashed')

        ax21 = axs[1].twinx()
        axs[1].plot(sub_date, temp_data[1], 'g-')
        ax21.plot(sub_date, temp_data[2], 'b-')
        axs[1].set_ylabel(r'$N_p$ ($\textrm{cm}^{-3}$)', color='g')
        ax21.set_ylabel(r'$T_p$ (eV)', color='b')
        # fig.tight_layout()
        date_form = DateFormatter("%H:%M")
        ax21.xaxis.set_major_formatter(date_form)
        plt.axvline(x=shock_time, color='red', linestyle='dashed')
        plt.axvline(x=up_beg, color='black', linestyle='dashed')
        plt.axvline(x=down_beg, color='black', linestyle='dashed')
        plt.axvline(x=up_end, color='black', linestyle='dashed')
        plt.axvline(x=down_end, color='black', linestyle='dashed')
        filename_str = 'shock_' + shock_time.item().strftime('%Y%m%dT%H%M%S') + '.png'
        plt.xlabel(u'UTC', fontsize=10)
        plt.savefig(filename_str, dpi=300)
        plt.close()
    return shock_para

def make_event_dict(shock_time_list, shock_para_list):
    event_arr = []
    for i in range(0,shock_time_list.__len__()):
        event_dict = {}
        event_dict['Event No.']=i+1
        event_dict['Shock Time']=shock_para_list[i]['shock_time'].item().strftime('%Y%m%dT%H%M%S')
        event_dict['Shock Type']=shock_para_list[i]['shock_type']
        event_dict['n_u']=shock_para_list[i]['up'][0]
        event_dict['T_u']=shock_para_list[i]['up'][1]
        event_dict['B_u'] = shock_para_list[i]['up'][2]
        event_dict['V_u'] = shock_para_list[i]['up'][6]
        event_dict['n_d'] = shock_para_list[i]['down'][0]
        event_dict['T_d'] = shock_para_list[i]['down'][1]
        event_dict['B_d'] = shock_para_list[i]['down'][2]
        event_dict['V_d'] = shock_para_list[i]['down'][6]
        event_dict['thetaBn'] = shock_para_list[i]['thetaBn']
        event_dict['Shock nx'] = shock_para_list[i]['shock_n'][0]
        event_dict['Shock ny'] = shock_para_list[i]['shock_n'][1]
        event_dict['Shock nz'] = shock_para_list[i]['shock_n'][2]
        event_arr.append(event_dict)
    return event_arr


# def read_data(fullpath):
#     # 功能: 读取数据
#
#     if not os.path.exists(fullpath):
#         data = []
#         codeId = "6"
#         return codeId, data
#
#     fid = open(fullpath, 'rb')
#     json_data = json.load(fid)
#
#     time_tags_long, fluxs_long = [], []
#     time_tags_short, fluxs_short = [], []
#     for id in range(len(json_data)):
#         # {
#         # "time_tag": "2021-09-19T21:42:00Z",
#         # "satellite": 16,
#         # "flux": 5.6853906471587834e-08,
#         # "observed_flux": 8.174998100685116e-08,
#         # "electron_correction": 2.4896074535263324e-08,
#         # "electron_contaminaton": false,
#         # "energy": "0.1-0.8nm"
#         # }
#         energy = json_data[id]['energy']
#         time_tag = datetime.datetime.strptime(json_data[id]['time_tag'], '%Y-%m-%dT%H:%M:%SZ')
#         flux = float(json_data[id]['flux'])
#         if energy == "0.1-0.8nm":
#             time_tags_long.append(time_tag)
#             fluxs_long.append(flux)
#         else:
#             time_tags_short.append(time_tag)
#             fluxs_short.append(flux)
#
#     codeId = "0"
#     data = {
#         'time_tags_long': time_tags_long,
#         'fluxs_long': fluxs_long,
#         'time_tags_short': time_tags_short,
#         'fluxs_short': fluxs_short,
#     }
#
#     return codeId, data


# def plot_fig(data, savepath):
#     # 功能: 生成图像产品
#
#     measures = {'L1': 1E-8,
#                 'L2': 1E-7,
#                 'L3': 1E-6,
#                 'L4': 1E-5,
#                 'L5': 1E-4, }
#
#     levels = {'L1': 'A',
#               'L2': 'B',
#               'L3': 'C',
#               'L4': 'M',
#               'L5': 'X', }
#
#     time_tags_long = data['time_tags_long']
#     time_tags_short = data['time_tags_short']
#     fluxs_long = np.array(data['fluxs_long'])
#     fluxs_short = np.array(data['fluxs_short'])
#
#     fig = plt.figure(figsize=(8, 6), dpi=150)
#     ax1 = plt.subplot(1, 1, 1)
#
#     plt.semilogy(time_tags_long, fluxs_long)
#     plt.semilogy(time_tags_short, fluxs_short)
#
#     plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
#     plt.xlim([time_tags_long[0], time_tags_long[-1]])
#     plt.ylim([1E-9, 1E-3])
#     plt.xlabel(u'UTC', fontsize=10)
#     plt.ylabel(u'Flux (W/$m^2$)', fontsize=10)
#     plt.title('GOES卫星X射线通量', fontsize=12)
#     ax1.xaxis.set_minor_locator(AutoMinorLocator(12))
#     ax1.tick_params(which='major', length=6)
#     ax1.tick_params(which='minor', length=3)
#     legend = plt.legend(['long', 'short'], loc=2, framealpha=0.1)
#
#     ax2 = ax1.twinx()
#     plt.semilogy(time_tags_long, fluxs_long * 0 + 5E-5, 'w', linewidth=1)
#     plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
#     plt.ylim([1E-9, 1E-3])
#     plt.grid()
#     ax2.set_yticks([measures[key] for key in measures])
#     ax2.set_yticklabels([levels[key] for key in levels])
#     ax2.tick_params(which='major', length=6)
#     ax2.tick_params(which='minor', length=3)
#
#     plt.savefig(savepath, transparent=True)
#     # plt.show()
#     plt.close()
#
#     return savepath


###############################################################################
