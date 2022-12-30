# import libraries
from recognition.knn import classify_unlabelled_directory, mapChars
import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from os import listdir
import glob
import os
from os.path import isfile, join
from ocr import ocr


from skimage.feature import hog
from skimage.transform import resize
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
import pickle
import xlwt
from xlwt import Workbook
# from utils.commonfunctions import *
mpl.rcParams['image.cmap'] = 'gray'

mypath, intersections, verticalLines, horizontalLines, binaryImgs, Cells, EnglishName, Code, StudentName, Symbol_1, Symbol_2, Symbol_3 = "SingleInput", "Intersections/", "verticalLines/", "horizontalLines/", "binaryImgs/", "Cells/", "Cells/EnglishName/", "Cells/Code/", "Cells/StudentName/", "Cells/1", "Cells/2", "Cells/3"
checkMarksPath, boxesPath, emptyCellsPath, questionMarksPath = "data/marks", "data/boxes", "data/emptyCells", "data/questionMarks"


def getLines(img, binaryImg, x):
    # Kernel Length
    kernelLength = np.array(img).shape[1] // x

    # Vertical Kernel (1 x kernelLength)
    verticalKernel = cv.getStructuringElement(cv.MORPH_RECT, (1, kernelLength))

    # Horizontal Kernel (kernelLength x 1)
    horizontalKernel = cv.getStructuringElement(
        cv.MORPH_RECT, (kernelLength, 1))

    # Apply erosion then dilation to detect vertical lines using the vertical kernel
    erodedImg = cv.erode(binaryImg, verticalKernel, iterations=3)
    verticalLinesImg = cv.dilate(erodedImg, verticalKernel, iterations=3)

    # Apply erosion then dilation to detect horizontal lines using the horizontal kernel
    erodedImg = cv.erode(binaryImg, horizontalKernel, iterations=3)
    horizontalLinesImg = cv.dilate(erodedImg, horizontalKernel, iterations=3)

    return verticalLinesImg, horizontalLinesImg


def getIntersections(pixels):
    intersections = {}
    for i in range(pixels.shape[0]):
        for j in range(pixels.shape[1]):
            if pixels[i][j] != 0:
                if i in intersections:
                    intersections[i].append((i, j))
                else:
                    intersections[i] = []
                    intersections[i].append((i, j))

    keys = list(intersections.keys())
    uniqueKeys = []
    uniqueKeys.append(keys[0])
    for i in range(1, len(keys), 1):
        if (keys[i] - keys[i - 1] > 5):
            uniqueKeys.append(keys[i])

    rows = []
    for i in uniqueKeys:
        rows.append(intersections[i])

    finalIntersections = []
    index = 0
    for row in rows:
        finalIntersections.append([])
        finalIntersections[index].append(row[0])
        for i in range(1, len(row), 1):
            if (row[i][1] - row[i - 1][1] > 5):
                finalIntersections[index].append(row[i])
        index += 1

    return finalIntersections


def houghLines(img, type):
    lines = cv.HoughLinesP(img.astype(np.uint8), 0.5, np.pi/180, 100,
                           minLineLength=0.25*min(img.shape[0], img.shape[1]), maxLineGap=10)

    hough_lines_out = np.zeros(img.shape)
    for line in lines:
        x1, y1, x2, y2 = line[0]
        if (type == "vertical"):
            cv.line(hough_lines_out, (x1, 0),
                    (x2, img.shape[0]), (255, 255, 255), 1)
        else:
            cv.line(hough_lines_out, (0, y1),
                    (img.shape[1], y2), (255, 255, 255), 1)
    return hough_lines_out


def runGetIntersections(imgPath):
    img = cv.imread(imgPath, 0)

    # thresholding
    (thresh, binaryImg) = cv.threshold(
        img, 128, 255, cv.THRESH_BINARY | cv.THRESH_OTSU)
    binaryImg = 255 - binaryImg

    verticalLinesImg, horizontalLinesImg = getLines(img, binaryImg, x=10)

    verticalLinesImg = houghLines(verticalLinesImg, "vertical")
    horizontalLinesImg = houghLines(horizontalLinesImg, "horizontal")

    return binaryImg, verticalLinesImg, horizontalLinesImg, cv.bitwise_and(verticalLinesImg, horizontalLinesImg)


def runGetCells(img, intersections):
    cells = {}
    intersections = np.array(intersections)
    height = img.shape[0]
    width = img.shape[1]
    for col in range(intersections.shape[1] - 1):
        cells[col] = []
        for row in range(intersections.shape[0] - 1):
            x_min = intersections[row][col][0]
            x_max = intersections[row + 1][col][0]
            y_min = intersections[row][col][1]
            y_max = intersections[row][col + 1][1]
            cell = img[x_min:x_max, y_min:y_max]
            cell[0:10, 0:width] = 0
            cell[-10:height, 0:width] = 0
            cell[0:height, 0:12] = 0
            cell[0:height, -5:width] = 0
            cells[col].append(cell)

    labels = ["Cells/Code/", "Cells/StudentName/",
              "Cells/EnglishName/", "Cells/1/", "Cells/2/", "Cells/3/"]
    for key in range(len(labels)):
        for i in range(len(cells[key])):
            img = cells[key][i]
            if(labels[key] == "Cells/1/"):
                img = cv.resize(cells[key][i], (200, 100))
                img = cv.resize(img, None, fx=3, fy=3,
                                interpolation=cv.INTER_CUBIC)
            cv.imwrite(labels[key] + chr(i+97) + ".jpg", img)


def detectHorizontalLines(symbol):
    width = symbol.shape[1] // 11
    horizontalSE = cv.getStructuringElement(cv.MORPH_RECT, (width, 1))
    morphResult = cv.erode(symbol, horizontalSE, iterations=3)
    contours, hierarchy = cv.findContours(
        morphResult, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    horizontalLinesCnt = len(contours)
    return horizontalLinesCnt


def detectVerticalLines(symbol):
    height = symbol.shape[0] // 11
    verticalSE = cv.getStructuringElement(cv.MORPH_RECT, (1, height))
    morphResult = cv.erode(symbol, verticalSE, iterations=3)
    contours, hierarchy = cv.findContours(
        morphResult, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    verticalLinesCnt = len(contours)
    return verticalLinesCnt


############################# HOG ############################

def prepareData(dataPath, files, label):
    x = []
    for fileName in files:
        img = cv.imread(dataPath + "/" + fileName, 0)
        x.append(img)
    y = [label] * len(x)
    return x, y


def train(x_train, y_train):
    list_hog_fd = []
    for img in x_train:
        fd = hog(resize(img, (128*4, 64*4)), orientations=9, pixels_per_cell=(14, 14),
                 cells_per_block=(1, 1), visualize=False)
        list_hog_fd.append(fd)

    x_train = np.array(list_hog_fd)

    knn = KNeighborsClassifier()
    knn.fit(x_train, y_train)

    # save the model to disk
    filename = 'model.sav'
    pickle.dump(knn, open(filename, 'wb'))


def knnScore(x_test, y_test):
    filename = 'model.sav'
    # load the model from disk
    knn = pickle.load(open(filename, 'rb'))
    list_hog_fd = []
    for img in x_test:
        fd = hog(resize(img, (128*4, 64*4)), orientations=9, pixels_per_cell=(14, 14),
                 cells_per_block=(1, 1), visualize=False)
        list_hog_fd.append(fd)

    x_test = np.array(list_hog_fd)

    score = knn.score(x_test, y_test)
    percentage = np.round(score * 100, 2)

    return percentage


def knnPredict(img):
    filename = 'model.sav'
    # load the model from disk
    knn = pickle.load(open(filename, 'rb'))
    fd = hog(resize(img, (128*4, 64*4)), orientations=9, pixels_per_cell=(14, 14),
             cells_per_block=(1, 1), visualize=False)
    expected = knn.predict(fd.reshape(1, -1))
    return expected[0]


def getData():
    checkMarksLabel, boxesLabel, questionMarksLabel, emptyCellsLabel = "C", "B", "Q", "E"

    checkMarksFiles = [f for f in listdir(
        checkMarksPath) if isfile(join(checkMarksPath, f))]
    boxesFiles = [f for f in listdir(boxesPath) if isfile(join(boxesPath, f))]
    questionMarksFiles = [f for f in listdir(
        questionMarksPath) if isfile(join(questionMarksPath, f))]
    emptyCellsFiles = [f for f in listdir(
        emptyCellsPath) if isfile(join(emptyCellsPath, f))]

    x_checkMarks, y_checkMarks = prepareData(
        checkMarksPath, checkMarksFiles, checkMarksLabel)
    x_boxes, y_boxes = prepareData(boxesPath, boxesFiles, boxesLabel)
    x_questionMarks, y_questionMarks = prepareData(
        questionMarksPath, questionMarksFiles, questionMarksLabel)
    x_emptyCells, y_emptyCells = prepareData(
        emptyCellsPath, emptyCellsFiles, emptyCellsLabel)

    x = x_checkMarks + x_boxes + x_questionMarks + x_emptyCells
    y = y_checkMarks + y_boxes + y_questionMarks + y_emptyCells

    return x, y


def runHog():
    x, y = getData()
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.33, random_state=42)

    train(x_train, y_train)
    score = knnScore(x_test, y_test)

    print(score, '%')


def mapPrediction(symbol):
    if (symbol == "C"):
        return "5"
    elif (symbol == "Q"):
        return "🟥"
    elif (symbol == "E"):
        return " "
    elif (symbol == "B"):
        return "0"


def runDetectCells():
    files = []
    results = [[], []]

    files.append([f for f in listdir(Symbol_2) if isfile(join(Symbol_2, f))])
    files.append([f for f in listdir(Symbol_3) if isfile(join(Symbol_3, f))])
    for i in range(len(files)):
        for filename in files[i]:
            img = []
            if (i == 0):
                img = cv.imread(Symbol_2 + "/" + filename, 0)
            else:
                img = cv.imread(Symbol_3 + "/" + filename, 0)
            numOfHorizontalLines = detectHorizontalLines(img)
            numOfVerticalLines = detectVerticalLines(img)
            prediction = knnPredict(img)
            if (numOfHorizontalLines > 0 and numOfVerticalLines == 0):
                results[i].append(5 - numOfHorizontalLines)
            elif (numOfHorizontalLines == 0 and numOfVerticalLines > 0):
                if (prediction == 'Q' or prediction == 'C'):
                    results[i].append(mapPrediction(prediction))
                else:
                    results[i].append(numOfVerticalLines)
            else:
                results[i].append(mapPrediction(prediction))
    return results


def createDirs():
    if(not os.path.exists(Cells)):
        os.makedirs(Cells)
    if(not os.path.exists(EnglishName)):
        os.makedirs(EnglishName)
    if(not os.path.exists(Code)):
        os.makedirs(Code)
    if(not os.path.exists(StudentName)):
        os.makedirs(StudentName)
    if(not os.path.exists(Symbol_1)):
        os.makedirs(Symbol_1)
    if(not os.path.exists(Symbol_2)):
        os.makedirs(Symbol_2)
    if(not os.path.exists(Symbol_3)):
        os.makedirs(Symbol_3)
    # if(not os.path.exists(verticalLines)):
    #     os.makedirs(verticalLines)
    # if(not os.path.exists(horizontalLines)):
    #     os.makedirs(horizontalLines)
    # if(not os.path.exists(intersections)):
    #     os.makedirs(intersections)
    # if(not os.path.exists(binaryImgs)):
    #     os.makedirs(binaryImgs)


def runExtractCells():
    createDirs()
    files = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    for fileName in files:
        img, vertical, horizontal, result_image = runGetIntersections(
            mypath + "/" + fileName)
        positions = getIntersections(result_image)
        runGetCells(img, positions)
        # cv.imwrite(verticalLines + fileName, vertical)
        # cv.imwrite(horizontalLines + fileName, horizontal)
        # cv.imwrite(intersections + fileName, result_image)
        # cv.imwrite(binaryImgs + fileName, img)


# extract cells from table
runExtractCells()
#  test code
codes = ocr(Code, 'eng')
# test EnglishName
englishNames = ocr(EnglishName, 'eng')
# test Arabic Name
arabicNames = ocr(StudentName, 'Arabic')
# test digits Number
numericalNumbers = classify_unlabelled_directory('./Cells/1/')
numericalNumbers = mapChars(numericalNumbers)
# detect symbols
symbols = runDetectCells()

# create excel sheet
wb = Workbook()
AutoFiller = wb.add_sheet('AutoFiller')
AutoFiller.write(0, 0, 'Code')
AutoFiller.write(0, 1, 'StudentName')
AutoFiller.write(0, 2, 'EnglishName')
AutoFiller.write(0, 3, '1')
AutoFiller.write(0, 4, '2')
AutoFiller.write(0, 5, '3')

for index in range(1, len(codes)):
    AutoFiller.write(index, 0, codes[index])

for index in range(1, len(arabicNames)):
    AutoFiller.write(index, 1, arabicNames[index])

for index in range(1, len(englishNames)):
    AutoFiller.write(index, 2, englishNames[index])

for index in range(1, len(numericalNumbers)):
    AutoFiller.write(index, 3, numericalNumbers[index])

for index in range(1, len(symbols[0])):
    AutoFiller.write(index, 4, symbols[0][index])

for index in range(1, len(symbols[1])):
    AutoFiller.write(index, 5, symbols[1][index])

wb.save('autoFiller.xls')
