import cv2
import numpy as np
import serial
import re

def ConvLight(img):
    # конвертация в оттенки серого
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # вычисление среднего значения яркости
    avg_gray = int(gray.mean())

    # вычисление коэффициента компенсации
    compensation_coeff = 128 / avg_gray

    # корректировка цветовых масок
    img[:, :, 0] = cv2.multiply(img[:, :, 0], compensation_coeff)
    img[:, :, 1] = cv2.multiply(img[:, :, 1], compensation_coeff)
    img[:, :, 2] = cv2.multiply(img[:, :, 2], compensation_coeff)

    return img

def DownloadSettings(Path):
    f = open(Path, 'r+')
    lines = f.readlines() 
    Settings = []
    for line in lines:
        LineData = []
        for s in re.findall(r'\d+', line):
            LineData.append(int(s))
        Settings.append(LineData)
    return(Settings)

def UpdateSettings(Settings, ind):
    ListSet = Settings[ind]
    return ([ListSet[0],ListSet[1],ListSet[2]],[ListSet[3],ListSet[4],ListSet[5]],ListSet[6],ListSet[7],ListSet[8],ListSet[9])

def Blur(frame, BlurGrade, Iter):
    Grade = BlurGrade if (BlurGrade % 2 == 1) else BlurGrade + 1
    frame = cv2.GaussianBlur(frame, (Grade, Grade), Iter)
    return frame

def Move(Direction, SerCoundation):
    if SerCoundation is not None:
        SerCoundation.write(format(ord(Direction), 'b')) 