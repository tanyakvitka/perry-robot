import cv2
import numpy as np
import pygame

from FunctionForProject import *

# Определение констант
WINDOW_NAME = 'Blur'
SETTINGS_WINDOW_NAME = 'Settings'
WINDOW_SIZE = (620, 480)
FPS_IN_VIDEO = 30

# Инициализация часов Pygame
clock = pygame.time.Clock()

# Создание окон OpenCV и трекбаров
cv2.namedWindow(WINDOW_NAME)
cv2.createTrackbar('Bl', WINDOW_NAME, 1, 100, lambda x: None)
cv2.createTrackbar('Grade', WINDOW_NAME, 0, 100, lambda x: None)

cv2.namedWindow(SETTINGS_WINDOW_NAME)
cv2.resizeWindow(SETTINGS_WINDOW_NAME, 400, 500)
cv2.createTrackbar('LMin', SETTINGS_WINDOW_NAME, 0, 255, lambda x: None)
cv2.createTrackbar('LMax', SETTINGS_WINDOW_NAME, 255, 255, lambda x: None)
cv2.createTrackbar('AMin', SETTINGS_WINDOW_NAME, 0, 255, lambda x: None)
cv2.createTrackbar('AMax', SETTINGS_WINDOW_NAME, 255, 255, lambda x: None)
cv2.createTrackbar('BMin', SETTINGS_WINDOW_NAME, 0, 255, lambda x: None)
cv2.createTrackbar('BMax', SETTINGS_WINDOW_NAME, 255, 255, lambda x: None)
cv2.createTrackbar('Erode', SETTINGS_WINDOW_NAME, 0, 100, lambda x: None)
cv2.createTrackbar('Dilate', SETTINGS_WINDOW_NAME, 0, 100, lambda x: None)
cv2.createTrackbar('Save', SETTINGS_WINDOW_NAME, 0, 1, lambda x: None)
cv2.createTrackbar('Stop', SETTINGS_WINDOW_NAME, 0, 1, lambda x: None)

# Инициализация захвата видео
url = r'http://192.168.61.136:4747/video'
cap = cv2.VideoCapture(0)


# Определение функций
def save_settings(mL, mA, mB, maL, maA, maB, erod, dil, gr, bl):
    """Сохранение текущих настроек в файл"""
    with open('ColorClassificatior.txt', 'a+') as f:
        s = 'Min color diapazone [ ' + str(mL) + ', ' + str(mA) + ', ' + str(mB) + ' ] Max color diapazone [ ' + str(
            maL) + ', ' + str(maA) + ', ' + str(maB) + ' ] Erode ' + str(erod) + ' Dilate ' + str(
            dil) + ' BlurIter ' + str(bl) + ' BlurGrade ' + str(gr) + ' ), \n'
        f.write(s)


# Главный цикл
while True:
    # Ограничение FPS
    clock.tick(FPS_IN_VIDEO)

    # Чтение кадра из захвата видео
    if cv2.getWindowProperty(SETTINGS_WINDOW_NAME, cv2.WND_PROP_VISIBLE) == 1:
        ret, frameMain = cap.read()
    else:
        ret = False

    # Обработка кадра, если он был успешно прочитан
    if ret:
        # Копирование и изменение размера кадра
        frame = frameMain.copy()
        frame = cv2.resize(frame, WINDOW_SIZE)

        # Получение позиций трекбаров
        Lmax = cv2.getTrackbarPos('LMax', SETTINGS_WINDOW_NAME)
        Lmin = cv2.getTrackbarPos('LMin', SETTINGS_WINDOW_NAME)
        Amin = cv2.getTrackbarPos('AMin', SETTINGS_WINDOW_NAME)
        Amax = cv2.getTrackbarPos('AMax', SETTINGS_WINDOW_NAME)
        Bmin = cv2.getTrackbarPos('BMin', SETTINGS_WINDOW_NAME)
        Bmax = cv2.getTrackbarPos('BMax', SETTINGS_WINDOW_NAME)
        IterErode = cv2.getTrackbarPos('Erode', SETTINGS_WINDOW_NAME)
        IterDilate = cv2.getTrackbarPos('Dilate', SETTINGS_WINDOW_NAME)
        SaveFlag = cv2.getTrackbarPos('Save', SETTINGS_WINDOW_NAME)
        BlurGrade = cv2.getTrackbarPos('Grade', WINDOW_NAME)
        BlurIter = cv2.getTrackbarPos('Bl', WINDOW_NAME)

        # Применение гауссового размытия
        Grade = BlurGrade if (BlurGrade % 2 == 1) else BlurGrade + 1
        frame = cv2.GaussianBlur(frame, (Grade, Grade), BlurIter)
        cv2.imshow(WINDOW_NAME, frame)

        # Сохранение настроек, если установлен флаг SaveFlag
        if SaveFlag == 1:
            save_settings(Lmin, Amin, Bmin, Lmax, Amax, Bmax, IterErode, IterDilate, BlurGrade, BlurIter)
            cv2.setTrackbarPos('Save', SETTINGS_WINDOW_NAME, 0)

            # Преобразование кадра в цветовое пространство Lab и применение пороговой обработки цвета
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2Lab)
        cv2.imshow('Lab', hsv)
        mask = cv2.inRange(hsv, np.array([Lmin, Amin, Bmin]), np.array([Lmax, Amax, Bmax]))
        mask = cv2.erode(mask, None, iterations=IterErode)
        mask = cv2.dilate(mask, None, iterations=IterDilate)

        # Применение маски к кадру
        mask = cv2.bitwise_and(frame, frame, mask=mask)

        # Если кадр не был успешно прочитан, сбросить захват видео
    else:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    # Отображение маскированного кадра
    cv2.imshow('stream', mask)

    # Выход при нажатии клавиши 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Освобождение захвата видео и уничтожение окон
cap.release()
cv2.destroyAllWindows()
