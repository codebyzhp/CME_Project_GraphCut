'''
Author       : ZHP
Date         : 2020-12-04 16:18:13
LastEditors  : ZHP
LastEditTime : 2020-12-08 19:37:39
FilePath     : /Earlier_Project/data/data_process.py
Description  : 从源数据(.dat)生成图片
Copyright 2020 ZHP
'''
import struct
import numpy as np
import string
from PIL import Image, ImageFilter
import os
import cv2
import sys
import time


RESOLUTION = (1024, 1024)


def alog(fig):
    for i in range(RESOLUTION[0]):
        for j in range(RESOLUTION[1]):
            if fig[i, j] > 0:
                fig[i, j] = min(1, (max(0, np.log10(fig[i, j]) + 13)) / 6.0)
            elif fig[i, j] < 0:
                fig[i, j] = 0.0
    return fig


def cal_time(total_time):
    h = total_time // 3600
    minute = (total_time % 3600) // 60
    sec = int(total_time % 60)
    print(f'本次总时长为： {h} hours {minute} minutes {sec} seconds...')


def get_mask_data(x_center, y_center, r_max, out_size=512):
    # print(x_center, y_center, r_max)
    mask_image = np.zeros((RESOLUTION[0], RESOLUTION[1]))
    minr, maxr = 0, out_size
    for x in range(RESOLUTION[0]):
        for y in range(RESOLUTION[1]):
            px = x - x_center
            py = y - y_center
            r, theta = cv2.cartToPolar(px, py, angleInDegrees=True)
            if r[0, 0] <= r_max:
                mask_image[x, y] = 0
            else:
                mask_image[x, y] = 255
    return mask_image


def generate_image(folder, out_folder, out_size=(512, 512), out_mode=0):
    '''
    description: 将一个月的cme数据通过源数据.dat文件生成图片
    param {
        floder : .dat文件所在文件夹
        out_folder : 生成图片文件夹
        out_size : 生成图片分辨率大小
        out_mode : 1 means median,0 means running diff
    }/disk/dataset/cme/预处理与网络
    '''
    if not os.path.exists(out_folder):
        os.makedirs(out_folder)

    date_list = []
    for name in os.listdir(folder):
        if name[:8] in date_list:
            continue
        else:
            date_list.append(name[:8])
    date_list.sort()
    final_img = np.zeros((RESOLUTION[0], RESOLUTION[1]))
    count = 0
    start = time.time()
    for date in date_list:
        yy = date[0:4]
        mm = date[4:6]
        dd = date[6:]
        print(f'year : {yy}  month : {mm}, day : {dd}')
        try:
            data_file = open(os.path.join(folder, date + '_lev1_little.dat'), 'rb')                       # little.dat
            with open(os.path.join(folder, date + '_lev1_info.dat'), 'r') as f:
                info = f.read().split('\n')
            f.close()
            # info = open(folder + date + '_lev1_info.dat', 'r').read().split('\n')     # 记录每天每12分钟的图片信息
            # for idx in range(1, len(info)):
            #     list_file.write(info[idx][:19] + '\n')  # 记录时间和日期
        except:
            print('expect open _lev1_little.dat/_lev1_info.dat file')
            continue
        mask_info = info[1].split()
        mask = get_mask_data(float(mask_info[1]), float(mask_info[2]), float(mask_info[3]))
        img_num = int(info[0].split()[-1])
        data = np.zeros((img_num + 1, RESOLUTION[0], RESOLUTION[1]))
        for i in range(1, img_num):
            for j in range(RESOLUTION[0]):
                for k in range(RESOLUTION[1]):
                    d = struct.unpack('d', data_file.read(8))[0]
                    if d <= 0:
                        d = 255
                    data[i, 1023 - j, k] = d
        data[0, ...] = final_img
        
        if out_mode == 1:
            median = np.median(data, axis=0)
            data = data - median
        
        for i in range(2, img_num + 1):  # 索引1为上月最后一张
            img_name = str(info[i][:19])
            img_name = img_name.replace(':', '_')
            if out_mode == 1:
                picture = data[i]
            else:
                # 差分图像
                last_median = np.median(data[i - 1])
                now_median = np.median(data[i])
                picture = data[i] - data[i -1]
            picture = alog(picture.reshape(RESOLUTION[0], RESOLUTION[1]))
            img = Image.fromarray(np.uint8(mask * picture))
            img = img.resize((out_size[0], out_size[1]))
            # img = img.filter(ImageFilter.SMOOTH)
            img.save(os.path.join(out_folder , img_name + '.png'))
            count += 1
            if count == 1:
                print('start generate..')
        final_img = data[-1]
        data_file.close()
        # info.close()
    print("Successfully generated {0} image".format(count))
    cal_time(time.time() - start)


def get_img_singel_year(folder, out_folder):
    '''
    description: 生成一年的图片
    param {
        folder : 一年数据的文件夹，如../2013
        out_folder : 转换成的图片保存位置
    }
    '''
    month_list = ['January', 'February', 'March', 'April', 'May', 'June',\
        'July', 'August', 'September', 'October', 'November', 'December']
    for month in os.listdir(folder):
        out_dir = os.path.join(out_folder, month)
        print('Converting {0} data into pictures...'.format(month_list[int(month)-1]))
        generate_image(os.path.join(folder, month), out_dir)
        print('Complete image generation in {0}..'.format(month_list[int(month)-1]))
        print('-' * 40)


if __name__ == "__main__":
    print(sys.argv[0])
    folder = '/disk/dataset/cme_dataset/2013/'
    out_folder = '/disk/dataset/cme_dataset/Images/2013/'
    # generate_image(folder, out_folder)
    get_img_singel_year(folder, out_folder)