# Joshua Korn + jkorn + Section F

from Tkinter import *
import sys, os, string, math
from PIL import Image, ImageDraw, ImageTk
import cv2
import json, colorsys
import tkFileDialog
import shutil
import numpy as np
# NOTE TO USER: Change this filepath to be the location of your Leap SDK lib
# folder. Example is given below.
curPath = os.getcwd()
# Currently works with Windows machines only; if you want to use this on Mac 
# OS X, please install the Mac SDK, move it to this folder, and change the path 
# as appropriate.
"""RENAME THIS TO THE NAME OF YOUR CURRENT SDK FOLDER"""
sdkFolder = "LeapDeveloperKit_2.1.5+22699_win"
sdkFilePath = curPath + os.sep + sdkFolder + os.sep + "LeapSDK\lib"
sys.path.insert(1, sdkFilePath)
import Leap, thread, time
from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture
from eventBasedAnimationClass import EventBasedAnimationClass
# You must have PIL installed if you do not already.
pytesserFilePath = curPath + os.sep + "pytesser"
sys.path.insert(1, pytesserFilePath)
from pytesserremix import *

class Listener(Leap.Listener):
    finger_names = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
    bone_names = ['Metacarpal', 'Proximal', 'Intermediate', 'Distal']
    state_names = ['STATE_INVALID', 'STATE_START', 'STATE_UPDATE', 'STATE_END']

    def on_init(self, controller):
        print "Initialized"
        self.gestureCooldown = 1
        self.lastGesture = 0
        self.lastDrawn = 0
        self.drawing = self.next = self.previous = self.justDrew = False
        self.clear = False
        self.width = 1000
        self.height = 800
        self.pos = None
        self.touchDist = 0
        self.motionDist = self.touchDist
        self.drawWidth = self.drawHeight = 600
        self.currentPos = (0, 0, 0, 0)

    def on_connect(self, controller):
        print "Connected"
        # Enable gestures
        controller.enable_gesture(Leap.Gesture.TYPE_CIRCLE);
        controller.enable_gesture(Leap.Gesture.TYPE_KEY_TAP);
        controller.enable_gesture(Leap.Gesture.TYPE_SCREEN_TAP);
        controller.enable_gesture(Leap.Gesture.TYPE_SWIPE);

    def on_disconnect(self, controller):
        print "Disconnected"

    def on_exit(self, controller):
        print "Exited"

    def drawLocation(self, interactionBox, finger, pointable):
        normalizedPosition = (interactionBox.normalize_point(
                              finger.tip_position))
        if (pointable.touch_distance <= self.touchDist):
            self.lastDrawn = time.time()
            self.justDrew = True
            color = "black"
            circRad = 25
            xPos = normalizedPosition.x * self.width
            yPos = self.height - normalizedPosition.y * self.height
            drawXStart = (self.width - self.drawWidth)/2
            drawXEnd = drawXStart + self.drawWidth
            drawYStart = (self.height - self.drawHeight)/2
            drawYEnd = drawYStart + self.drawHeight
            if (xPos >= drawXStart and xPos + circRad <= drawXEnd and
                yPos >= drawYStart and yPos + circRad <= drawYEnd):  
                self.create(xPos, yPos, circRad, circRad, color) # for TK
                self.drawPIL(xPos-drawXStart, yPos-drawYStart, circRad, 
                             circRad, color) # for PIL

    def swipeControl(self, controller, swipe):
        direction = swipe.direction
        (x, y, z) = (direction[0], direction[1], direction[2])
        (smallChange, bigChange) = (0.25, 0.4)
        self.lastGesture = time.time()
        if x > bigChange and abs(y) < smallChange: # right swipe
            self.next = True
        elif x < -bigChange and abs(y) < smallChange: # left swipe
            self.previous = True
        elif y < -bigChange and abs(x) < smallChange: # down swipe
            self.clear = True

    def currPosUpdate(self, interactionBox, finger, pointable):
        normalizedPosition = (interactionBox.normalize_point(
                              finger.tip_position))
        xPos = normalizedPosition.x * self.width
        yPos = self.height - normalizedPosition.y * self.height
        z = normalizedPosition.z
        distance = pointable.touch_distance
        self.currentPos = (xPos, yPos, distance, z)

    def on_frame(self, controller):
        # Get the most recent frame
        frame = controller.frame()
        interactionBox = frame.interaction_box

        for gesture in frame.gestures():
            curTime = time.time()
            if (gesture.type == Leap.Gesture.TYPE_SWIPE and 
                curTime-self.lastGesture > self.gestureCooldown): # so doesn't
                swipe = SwipeGesture(gesture) # read one gesture as multiple
                fastSwipe = 75 # speed in mm/s
                zStart = swipe.pointable.touch_distance
                if swipe.speed >= fastSwipe and zStart > self.motionDist:
                   self.swipeControl(controller, swipe)
        for hand in frame.hands:
            for finger in hand.fingers:
                for pointable in frame.pointables:
                    finger = Leap.Finger(pointable)
                    if self.finger_names[finger.type()] == "Index":
                        self.currPosUpdate(interactionBox, finger, pointable)
                        if self.drawing:
                            self.drawLocation(interactionBox,finger,pointable)

    def create(self, x, y, width, height, color):
        self.canvas.create_oval(x, y, x + width, 
                                y + height, fill=color, width=0)

    def drawPIL(self, x, y, width, height, color):
        self.draw.ellipse((x, y, x + width, y + height), fill="black")

    def set_canvas(self, canvas):
        self.canvas = canvas

    def set_draw(self, draw):
        self.draw = draw

class Painter(EventBasedAnimationClass):

    def __init__(self):
        self.leap = Leap.Controller()
        self.painter = Listener()
        self.leap.add_listener(self.painter)
        self.width = 1000
        self.height = 800
        self.drawWidth = self.drawHeight = 600
        self.gameLaunched = False
        super(Painter, self).__init__(self.width, self.height)

    def compareDiff(self, item):
        (curR, curG) = (self.currentRGB[0], self.currentRGB[1])
        curB = self.currentRGB[2]
        (testR, testG, testB) = (item[0], item[1], item[2])
        distance = ((curR-testR)**2 + (curG-testG)**2 + (curB-testB)**2)**0.5
        return distance

    def getAverage(self, rgbList):
        rSum = gSum = bSum = 0
        for pix in rgbList:
            rSum += pix[0]
            gSum += pix[1]
            bSum += pix[2]
        divBy = len(rgbList)
        rSum /= divBy
        gSum /= divBy
        bSum /= divBy
        return [rSum, gSum, bSum]

    def findMatch(self): # finds produce item using distance formula
        self.currentRGB = self.getAverage(self.currentRGB)
        firstTwoLetters = self.mainString
        total = []
        for key in self.mainDict.iterkeys():
            if key[:2] == firstTwoLetters: # see if same starting letters
                for itemIndex in xrange(len(self.mainDict[key])):
                    item = self.mainDict[key][itemIndex]
                    compareDiff = self.compareDiff(item)
                    total.append((compareDiff, key, itemIndex))
        finalCompareList = sorted(total) # since first item in each tuple
        # is the difference, will return them sorted by closest
        self.resultList = finalCompareList

    def mergeDicts(self):
        finalPath = "ItemDict.json"
        tempPath = "TempItemDict.json"
        with open(finalPath) as f:
            oldDict = json.load(f)
        with open(tempPath) as f:
            newDict = json.load(f)
        for key in newDict:
            if key not in oldDict:
                oldDict[key] = newDict[key]
            else:
                oldVal = oldDict[key]
                newVal = newDict[key]
                if oldVal != newVal:
                    for item in newVal:
                        if item not in oldVal:
                            oldVal += [item]
                oldDict[key] = oldVal
        with open(finalPath, 'w') as f:
            json.dump(oldDict, f)
        self.loadDict()

    def saveDict(self, tempDict):
        path = "ItemDict.json"
        if not os.path.exists(path):       
            with open(path, 'w') as f:
                json.dump(tempDict, f)
        else: 
            if self.mainDict == {}: self.loadDict()
            newPath = "TempItemDict.json"
            with open(newPath, 'w') as f:
                json.dump(tempDict, f)
            self.mergeDicts()

    def loadDict(self):
        path = "ItemDict.json"
        with open(path) as f:
            self.mainDict = json.load(f)

    def trainNewImages(self, filePath, title, spec=""):
        tempDict = {}
        img = Image.open(filePath)
        extensionIndex = -3
        xPixels, yPixels = img.size
        centerX = xPixels / 2
        centerY = yPixels / 2
        pixel = img.load()
        pixelGap = 5
        pixRGBList = []
        yPixStart, xPixStart = centerY - pixelGap, centerX - pixelGap
        yPixEnd, xPixEnd = centerY + pixelGap, centerX + pixelGap
        for yPix in xrange(yPixStart, yPixEnd + 1): # since inclusive
            for xPix in xrange(xPixStart, xPixEnd + 1):
                if filePath[extensionIndex:] == "gif": # due to nature of gif
                    rgbImage = img.convert('RGB')    # pixel data
                    (R, G, B) = rgbImage.getpixel((xPix, yPix))
                else:
                    pixRGB = pixel[xPix, yPix]
                    (R, G, B) = (pixRGB[0], pixRGB[1], pixRGB[2])
                pixRGBList.append([R, G, B])
        (R, G, B) = self.getAverage(pixRGBList)
        if title not in tempDict:
            tempDict[title] = [[R, G, B, spec, filePath]]
        else:
            tempDict[title] += [[R, G, B, spec, filePath]]
        self.saveDict(tempDict)

    # Train images with format: "Produce subclass" as image title, where
    # subclass is specific color, such as Apple red vs Apple green
    def trainSetup(self):
        path = os.getcwd() + os.sep + "TrainingImgs"
        for filename in os.listdir(path):
            filePath = path + os.sep + filename
            extensionIndex = -4
            if filename[extensionIndex:] == "jpeg":
                extensionIndex = -5
            title = filename[:extensionIndex] # removes extension
            spaces = False
            for char in title:
                if char.isspace():
                    spaces = True
            if spaces:
                newTitle = spec = ""
                spaceIndex = title.find(" ")
                newTitle = title[:spaceIndex]
                spec = title[spaceIndex+1:]
                allDigits = True
                for char in spec:
                    if char not in string.digits:
                        allDigits = False
                        break
                if allDigits: spec = ""
                title = newTitle
                self.trainNewImages(filePath, title, spec)
            else: self.trainNewImages(filePath, title)

    def rgbString(self, red, green, blue): # from course notes
        return "#%02x%02x%02x" % (red, green, blue)

    def initAnimation2(self):
        (H, S, V) = (0.5, 0.45, 0.8) # light cyan
        (R, G, B) = colorsys.hsv_to_rgb(H, S, V)
        R = int(R*255) # since colorsys gives amount divided by 255
        G = int(G*255)
        B = int(B*255)
        self.bgColor = self.rgbString(R, G, B)
        self.resultIndex = 0
        self.addString = self.specAddString = self.loadPath = ""
        self.browseStr = self.browseSpecStr = ""
        self.clickAddString = self.clickSpecString = self.fileLoaded = False
        self.loadConfirm = self.confirmPic = self.takingPic2 = False
        self.browseScreen = self.clickBrowseStr = self.clickBrowseSpec = False
        self.browseList = []
        self.itemsPerPage = 5
        self.curPage = self.pages = 0

    def initAnimation(self):
        self.painter.set_canvas(self.canvas)
        self.image=Image.new("RGB", (self.drawWidth, self.drawHeight), "white")
        self.draw = ImageDraw.Draw(self.image)
        self.painter.set_draw(self.draw)
        self.mainDict = {}
        self.mainString = ""
        self.currentRGB = []
        self.timerDelay = 1
        self.resultList = []
        self.trainSetup()
        self.loadDict()
        self.possibleDrawing = self.takingPic = self.resultScreen = False
        if not self.gameLaunched:
            self.inTut = True
            self.inMenu = False
        else:
            self.inTut = False
            self.inMenu = True
        self.inTrain = False
        self.inScan = self.inAdd = self.inBrowse = self.inQuit = False
        self.painter.drawing = self.addItem = False
        self.painter.justDrew = self.painter.menu = self.painter.clear = False
        self.initAnimation2()

    def fontColor(self, R, G, B):
        relativeLum = (0.2126*R + 0.7152*G + 0.0722*B) # rel. luminance formula
        maxRGB = 255
        midpt = maxRGB/2
        if relativeLum > midpt: # bright
            return "black" # black font for bright background
        else: return "white"

    # captures the center pixel from the camera and obtains the color in RGB
    def camCapture(self):
        capture, start = cv2.VideoCapture(0), time.time()
        while(capture.isOpened()):
            correct, frame = capture.read()
            yPixels, xPixels = frame.shape[0], frame.shape[1] # def. 480, 640
            centerY, centerX = yPixels / 2, xPixels / 2 
            cv2.imshow('cv2', frame) # shows frame
            waitTime = 5
            timeDiff = time.time() - start
            if timeDiff > waitTime:
                capture.release()
                pixelGap = 5
                yPixStart, xPixStart = centerY - pixelGap, centerX - pixelGap
                yPixEnd, xPixEnd = centerY + pixelGap, centerX + pixelGap
                for yPix in xrange(yPixStart, yPixEnd + 1): # since inclusive
                    for xPix in xrange(xPixStart, xPixEnd + 1):
                        RValue = frame[yPix, xPix, 2]
                        GValue = frame[yPix, xPix, 1]
                        BValue = frame[yPix, xPix, 0]
                        self.currentRGB.append([RValue, GValue, BValue])
                cv2.destroyAllWindows()
            if cv2.waitKey(1): pass
        self.findMatch()
        self.takingPic = False
        self.resultScreen = True

    def letterRecognize(self):
        filename = "testPIL.jpg"
        self.image.save(filename)
        testString = image_file_to_string(filename)
        testString = testString.strip()
        if testString in string.ascii_letters and testString != "":
            if len(self.mainString) == 0:
                testString = testString.upper()
            else:
                testString = testString.lower()
            self.mainString += testString
            if len(self.mainString) == 1: self.redraw()
            self.painter.drawing = False
            self.possibleDrawing = True
        else: 
            self.redraw()
            self.painter.justDrew = False

    def menuControl(self):
        dist = self.painter.currentPos[2]
        if dist <= -0.8:
            if self.inScan:
                self.canvas.delete(ALL)
                self.painter.drawing = True
                self.inScan = self.inMenu = False
            elif self.inAdd:
                self.canvas.delete(ALL)
                self.addItem = True
                self.inAdd = self.inMenu = False
            elif self.inBrowse:
                self.browseControl()
                self.canvas.delete(ALL)
                self.browseScreen = True
                self.inBrowse = self.inMenu = False
            elif self.inQuit:
                self.quit()

    def menuCheck(self, curX, curY):
        if (self.scanStartX <= curX and curX < self.scanEndX and
            self.scanStartY <= curY and curY < self.scanEndY):
            self.inScan = True
            self.inAdd = self.inBrowse = self.inQuit = False
        elif (self.addStartX <= curX and curX < self.addEndX and
              self.addStartY <= curY and curY < self.addEndY):
            self.inAdd = True
            self.inScan = self.inBrowse = self.inQuit = False
        elif (self.browseStartX <= curX and curX < self.browseEndX and
              self.browseStartY <= curY and curY < self.browseEndY):
            self.inBrowse = True
            self.inScan = self.inAdd = self.inQuit = False
        elif (self.quitStartX <= curX and curX < self.quitEndX and
              self.quitStartY <= curY and curY < self.quitEndY):
            self.inQuit = True
            self.inScan = self.inBrowse = self.inAdd = False

    def getColorsCont(self, dist, baseColor):
        (baseH, baseS, baseV) = (0.5, 0.45, 1)
        if self.inBrowse:
            browseV = 1 - 0.6 * dist
            (R, G, B) = colorsys.hsv_to_rgb(baseH, baseS, browseV)
            R = int(R*255)
            G = int(G*255)
            B = int(B*255)
            browseColor = self.rgbString(R, G, B)
            addColor = scanColor = quitColor = baseColor
            return (scanColor, addColor, browseColor, quitColor)
        elif self.inQuit:
            quitV = 1 - 0.6 * dist
            (R, G, B) = colorsys.hsv_to_rgb(baseH, baseS, quitV)
            R = int(R*255)
            G = int(G*255)
            B = int(B*255)
            quitColor = self.rgbString(R, G, B)
            addColor = scanColor = browseColor = baseColor
            return (scanColor, addColor, browseColor, quitColor)
        else: 
            quitColor = addColor = scanColor = browseColor = baseColor
            return (scanColor, addColor, browseColor, quitColor)

    def getColors(self, dist):
        (baseH, baseS, baseV) = (0.5, 0.45, 1) # light cyan!
        (baseR, baseG, baseB) = colorsys.hsv_to_rgb(baseH, baseS, baseV)
        baseR = int(baseR*255) # since colorsys gives amount divided by 255
        baseG = int(baseG*255)
        baseB = int(baseB*255)
        baseColor = self.rgbString(baseR, baseG, baseB)
        if self.inScan:
            scanV = 1 - 0.6 * dist # darker up to 0.5 if full dist
            (R, G, B) = colorsys.hsv_to_rgb(baseH, baseS, scanV)
            R = int(R*255)
            G = int(G*255)
            B = int(B*255)
            scanColor = self.rgbString(R, G, B)
            addColor = browseColor = quitColor = baseColor
            return (scanColor, addColor, browseColor, quitColor)
        elif self.inAdd:
            addV = 1 - 0.6 * dist
            (R, G, B) = colorsys.hsv_to_rgb(baseH, baseS, addV)
            R = int(R*255)
            G = int(G*255)
            B = int(B*255)
            addColor = self.rgbString(R, G, B)
            scanColor = browseColor = quitColor = baseColor
            return (scanColor, addColor, browseColor, quitColor)
        else: return self.getColorsCont(dist, baseColor)

    def drawMenuText(self):
        centerX, centerY = self.width/2, self.height/2
        title = "Perfect Produce Picker!"
        scanX = (self.scanEndX - self.scanStartX)/2
        scanY = (self.scanEndY - self.scanStartY)/2
        addX = (self.addEndX - self.addStartX)/2 + self.width/2
        addY = (self.addEndY - self.addStartY)/2
        browseX = (self.browseEndX - self.browseStartX)/2
        browseY = (self.browseEndY - self.browseStartY)/2 + self.height/2
        quitX = (self.quitEndX - self.quitStartX)/2 + self.width/2
        quitY = (self.quitEndY - self.quitStartY)/2 + self.height/2
        self.canvas.create_text(centerX, centerY, text=title, 
                            font="Impact 18", fill="white")
        self.canvas.create_text(scanX, scanY, text="SCAN", 
                            font="Impact 25", fill="black")
        self.canvas.create_text(addX, addY, text="ADD", 
                            font="Impact 25",
                            fill="black")
        self.canvas.create_text(browseX, browseY, text="BROWSE", 
                            font="Impact 25", fill="black")
        self.canvas.create_text(quitX, quitY, text="QUIT", 
                            font="Impact 25", fill="black")

    def drawMenuCont(self, dist):
        centerX, centerY = self.width/2, self.height/2
        titleHeight = 50
        titleWidth = 150
        titleStartX = centerX - titleWidth
        titleEndX = centerX + titleWidth
        titleStartY = centerY - titleHeight
        titleEndY = centerY + titleHeight
        (scanColor, addColor, browseColor, quitColor) = self.getColors(dist)
        self.canvas.create_rectangle(self.scanStartX, self.scanStartY,
                        self.scanEndX, self.scanEndY, fill=scanColor)
        self.canvas.create_rectangle(self.addStartX, self.addStartY,
                        self.addEndX, self.addEndY, fill=addColor)
        self.canvas.create_rectangle(self.browseStartX, self.browseStartY,
                        self.browseEndX, self.browseEndY, fill=browseColor)
        self.canvas.create_rectangle(self.quitStartX, self.quitStartY,
                        self.quitEndX, self.quitEndY, fill=quitColor)
        self.canvas.create_rectangle(titleStartX, titleStartY,
                        titleEndX, titleEndY, fill="black")
        self.drawMenuText()

    def drawMenu(self):
        (curX, curY, curDist, z) = self.painter.currentPos
        # right now, distance from 1 to -1, where 1 is farthest and -1 closest
        #however want to change to simulate 0 to 1, where 1 is closest
        halfway = 0.5
        if curDist >= 0: # far away
            dist = (1 - curDist)/2.0 # makes range from 0 to 0.5
        elif curDist < 0:
            dist = -curDist/2.0 + halfway # makes positive, from 0.5 to 1
        self.scanStartX = self.scanStartY = self.addStartY = 0
        self.browseStartX = 0
        self.scanEndX = self.addStartX = self.browseEndX = self.width/2
        self.quitStartX = self.width/2
        self.scanEndY = self.addEndY = self.browseStartY = self.height/2
        self.quitStartY = self.height/2
        self.addEndX = self.quitEndX = self.width
        self.browseEndY = self.quitEndY = self.height
        self.menuCheck(curX, curY)
        self.drawMenuCont(dist)

    def nextControl(self):
        if len(self.mainString) == 1:
            self.painter.drawing = True
            self.possibleDrawing = False
            self.painter.justDrew = False
            self.canvas.delete(ALL)
        elif len(self.mainString) == 2: # change this for training
            self.takingPic = True
            self.possibleDrawing = False

    def onTimerFired(self): # make 2nd timer fired
        lastDrawn = self.painter.lastDrawn
        curTime, restSec = time.time(), 1.5
        if self.painter.drawing:
            self.painter.motionDist = self.painter.touchDist
            self.timerDelay = 150 # reduce lag for leap input
        else:
            self.painter.motionDist = -1 # max range of motion
            self.timerDelay = 1 # go back to normal timer checks for animations
        if self.inMenu:
            self.menuControl()
        elif (self.inTut and self.painter.next and 
             self.painter.currentPos[2] > 0):
            self.painter.next = False
            self.inTut = False
            self.inMenu = True
        elif self.painter.clear and self.painter.drawing:
            self.redraw()
            self.painter.clear = False
            self.painter.justDrew = False
        elif (self.mainString != "" and self.painter.previous and
              self.possibleDrawing):
            self.mainString = self.mainString[:-1]
            self.redraw()
            self.painter.previous = False
            self.possibleDrawing = False
            self.painter.drawing = True
            self.painter.justDrew = False
        elif self.painter.next and self.possibleDrawing:
            self.nextControl()
        elif self.browseScreen and self.painter.clear:
            self.initAnimation()
        elif self.browseScreen:
                if (self.painter.next and self.pages > 0 and 
                    self.curPage < self.pages):
                    self.painter.next = False
                    self.curPage += 1
                elif (self.painter.previous and self.pages > 0 
                      and self.curPage > 0):
                    self.painter.previous = False
                    self.curPage -= 1
                self.browseControl()
        elif self.painter.next and self.addItem and self.addString != "":
            self.addItem = False
            if self.fileLoaded:
                self.moveAndRenameFile()
                self.loadConfirm = True
                self.fileLoaded = False
            else:
                self.takingPic2 = True
            self.painter.next = False
        elif self.takingPic2:
            self.takeAddPic()
        elif self.confirmPic and self.painter.previous:
            self.confirmPic = False
            self.painter.previous = False
            self.takingPic2 = True
        elif self.confirmPic and self.painter.next:
            self.confirmPic = False
            self.painter.previous = False
            self.loadTakenPic()
            self.loadConfirm = True
        elif self.loadConfirm and self.painter.clear:
            self.initAnimation()
        elif self.resultScreen:
            if self.painter.clear:
                self.initAnimation()
            elif self.painter.next and len(self.resultList) > 1:
                resultLen = len(self.resultList)
                self.resultIndex = (self.resultIndex + 1) % resultLen
                self.painter.next = False
            elif self.painter.previous and len(self.resultList) > 2: # don't
                resultIndex = self.resultIndex - 1      # need back swap for 2
                maxReverseIndex = - len(self.resultList)               # items
                if resultIndex < maxReverseIndex:
                    self.resultIndex = -1
                else: self.resultIndex = resultIndex
                self.painter.previous = False
        elif self.painter.clear or self.painter.previous or self.painter.next:
            self.painter.clear = self.painter.previous = False
            self.painter.next = False # resets fake swipes
        elif self.takingPic:
            self.camCapture()
        elif (curTime - lastDrawn > restSec and self.painter.drawing 
             and self.painter.justDrew):
            self.letterRecognize()

    def drawPaintText(self):
        if len(self.mainString) == 0:
            letterNum = "first"
        elif len(self.mainString) == 1:
            letterNum = "second"
        topText = ("Draw the %s letter slowly in the white box!"
        " Press inwards to begin!") % (letterNum)
        botText = "Swipe down out of drawing range to clear canvas."
        topMargin = (self.height - self.drawHeight)/4
        centerX = self.width/2
        botMargin = self.height - topMargin
        self.canvas.create_text(centerX, topMargin, text=topText,
                                font="Impact 25")
        self.canvas.create_text(centerX, botMargin,
                                text=botText, font="Impact 18")

    def drawPaint(self):
        leftXStart = topYStart = 0
        leftXEnd = (self.width - self.drawWidth)/2
        topYEnd = (self.height - self.drawHeight)/2
        rightXStart = leftXEnd + self.drawWidth
        botYStart = topYEnd + self.drawHeight
        self.canvas.create_rectangle(leftXStart, topYStart, self.width,
                                     topYEnd, fill=self.bgColor, width=0)
        self.canvas.create_rectangle(leftXStart, topYEnd, leftXEnd,
                                     botYStart, fill=self.bgColor, width=0)
        self.canvas.create_rectangle(rightXStart, topYEnd, self.width,
                                     botYStart, fill=self.bgColor, width=0)
        self.canvas.create_rectangle(leftXStart, botYStart, self.width,
                                     self.height, fill=self.bgColor, width=0)
        self.drawPaintText()

    def createArrows(self, botMargin, leftMargin, rightMargin):
        leftRectCX = leftMargin
        rectWidth, rectHeight, triangleGap = 150, 35, 25
        trianglePoint = 60
        rtRectCX = rightMargin
        leftStartX = leftRectCX - rectWidth
        leftEndX = leftRectCX + rectWidth
        botStartY = botMargin - rectHeight
        botEndY = botMargin + rectHeight
        rightStartX = rtRectCX - rectWidth
        rightEndX = rtRectCX + rectWidth
        self.canvas.create_rectangle(leftStartX, botStartY, leftEndX, botEndY,
                                     fill="firebrick1", width=0)
        self.canvas.create_rectangle(rightStartX,botStartY,rightEndX,botEndY,
                                     fill="green", width=0)
        self.canvas.create_polygon(leftStartX, botEndY + triangleGap,
            leftStartX - trianglePoint, botEndY - rectHeight, leftStartX,
            botStartY - triangleGap, fill="firebrick1", width=0)
        self.canvas.create_polygon(rightEndX, botEndY + triangleGap,
            rightEndX + trianglePoint, botEndY - rectHeight, rightEndX,
            botStartY - triangleGap, fill="green", width=0)

    def drawConfirm(self):
        if len(self.mainString) == 1:
            letter = self.mainString
        elif len(self.mainString) == 2:
            letter = self.mainString[1].upper()
        topTxt = "Did you write:"
        rightTxt = "Swipe right to continue."
        leftTxt = "Swipe left to redo."
        centerX = self.width/2
        centerY = self.height/2
        topMargin = (self.height - self.drawHeight)/4
        botMargin = self.height - topMargin*2
        leftMargin = 250
        rightMargin = self.width - leftMargin
        self.canvas.create_rectangle(0, 0, self.width, self.height, 
                                     fill=self.bgColor)
        self.createArrows(botMargin, leftMargin, rightMargin)
        self.canvas.create_text(centerX, topMargin, text=topTxt, 
                                font="Impact 40")
        self.canvas.create_text(centerX, centerY, text=letter,
                                font="Impact 300")
        self.canvas.create_text(leftMargin, botMargin, text=leftTxt,
                                font="Impact 20")
        self.canvas.create_text(rightMargin, botMargin, text=rightTxt,
                                font="Impact 20")

    def drawNoResult(self):
        firstTxt = "Oops! No result found! You might have to add this item."
        secondTxt = "Swipe down to get back to main menu!"
        centerX, centerY = self.width/2, self.height/2
        txtGap = 30
        firstY = centerY - txtGap
        secondY = centerY + txtGap
        self.canvas.create_rectangle(0, 0, self.width, self.height, 
                                     fill=self.bgColor)
        self.canvas.create_text(centerX, firstY, text=firstTxt, 
                                font="Impact 25")
        self.canvas.create_text(centerX, secondY, text=secondTxt, 
                                font="Impact 25")

    def backSwapText(self, result, spec, fontColor):
        leftMargin = 160
        vowels = "AEIOUaeiou"
        if spec != "":
            itemString = spec + " " + result[0].lower() + result[1:]
        else:
            itemString = result[0].lower() + result[1:]
        topString = "Go back to"
        textGap = 20
        centerY = self.height/2
        firstLineY = centerY - textGap
        secLineY = centerY + textGap
        self.canvas.create_text(leftMargin, firstLineY, text=topString,
                           font="Impact 18", fill=fontColor)
        self.canvas.create_text(leftMargin, secLineY, text=itemString,
                           font="Impact 18", fill=fontColor)

    def swapText(self, result, spec, fontColor):
        leftMargin = 160
        rightMargin = self.width - leftMargin
        vowels = "AEIOUaeiou"
        if spec != "":
            if spec[0] in vowels: article = "an"
            else: article = "a"
            itemString = spec + " " + result[0].lower() + result[1:]
        else:
            if result[0] in vowels: article = "an"
            else: article = "a"
            itemString = result[0].lower() + result[1:]
        itemString = itemString + "?"
        topString = "No? What about" + " " + article
        textGap = 20
        centerY = self.height/2
        firstLineY = centerY - textGap
        secLineY = centerY + textGap
        self.canvas.create_text(rightMargin, firstLineY, text=topString,
                           font="Impact 18", fill=fontColor)
        self.canvas.create_text(rightMargin, secLineY, text=itemString,
                           font="Impact 18", fill=fontColor)

    def createSwapOption(self, result, spec, keyIndex):
        bgR = self.mainDict[result][keyIndex][0]
        bgG = self.mainDict[result][keyIndex][1]
        bgB = self.mainDict[result][keyIndex][2]
        bgColor = self.rgbString(bgR, bgG, bgB)
        fontColor = self.fontColor(bgR, bgG, bgB)
        leftMargin = 180
        rtRectCX = self.width - leftMargin
        botMargin = self.height/2
        rectWidth, rectHeight, triangleGap = 90, 80, 30
        trianglePoint = 70
        botStartY = botMargin - rectHeight
        botEndY = botMargin + rectHeight
        rightStartX = rtRectCX - rectWidth
        rightEndX = rtRectCX + rectWidth
        self.canvas.create_rectangle(rightStartX,botStartY,rightEndX,botEndY,
                                     fill=bgColor, width=0)
        self.canvas.create_polygon(rightEndX, botEndY + triangleGap,
            rightEndX + trianglePoint, botEndY - rectHeight, rightEndX,
            botStartY - triangleGap, fill=bgColor, width=0)
        self.swapText(result, spec, fontColor)

    def createBackSwapOption(self, result, spec, keyIndex):
        bgR = self.mainDict[result][keyIndex][0]
        bgG = self.mainDict[result][keyIndex][1]
        bgB = self.mainDict[result][keyIndex][2]
        bgColor = self.rgbString(bgR, bgG, bgB)
        fontColor = self.fontColor(bgR, bgG, bgB)
        leftRectCX = 180
        rectWidth, rectHeight, triangleGap = 90, 80, 30
        trianglePoint = 70
        botMargin = self.height/2
        leftStartX = leftRectCX - rectWidth
        leftEndX = leftRectCX + rectWidth
        botStartY = botMargin - rectHeight
        botEndY = botMargin + rectHeight
        self.canvas.create_rectangle(leftStartX, botStartY, leftEndX, botEndY,
                                     fill=bgColor, width=0)
        self.canvas.create_polygon(leftStartX, botEndY + triangleGap,
            leftStartX - trianglePoint, botEndY - rectHeight, leftStartX,
            botStartY - triangleGap, fill=bgColor, width=0)
        self.backSwapText(result, spec, fontColor)

    def arrowControl(self):
        if len(self.resultList) > 1:
            resultIndex = (self.resultIndex + 1) % len(self.resultList)
            specIndex = 3
            newResult = self.resultList[resultIndex][1]
            keyIndex = self.resultList[resultIndex][2]
            spec = self.mainDict[newResult][keyIndex][specIndex]
            self.createSwapOption(newResult, spec, keyIndex)
        if len(self.resultList) > 2 and self.resultIndex != 0:
            resultIndex = self.resultIndex - 1
            maxReverseIndex = - len(self.resultList)
            if resultIndex < maxReverseIndex:
                    resultIndex = -1
            specIndex = 3
            newResult = self.resultList[resultIndex][1]
            keyIndex = self.resultList[resultIndex][2]
            spec = self.mainDict[newResult][keyIndex][specIndex]
            self.createBackSwapOption(newResult, spec, keyIndex)

    def resultText(self, result, spec, fontColor):
        vowels = "AEIOUaeiou"
        if spec != "":
            if spec[0] in vowels: article = "an"
            else: article = "a"
            while spec[-1] in string.digits:
                spec = spec[:-1]
            itemString = spec + " " + result[0].lower() + result[1:]
        else:
            if result[0] in vowels: article = "an"
            else: article = "a"
            itemString = result[0].lower() + result[1:]
        mainString = "Do you have" + " " + article + " " + itemString + "?"
        self.arrowControl()
        centerX = self.width/2
        topGap = 100
        botGap = self.height - 100
        botText = "Swipe down to get back to the main menu!"
        self.canvas.create_text(centerX, topGap, text=mainString,
                                font="Impact 50", fill=fontColor)
        self.canvas.create_text(centerX, botGap, text=botText,
                                font="Impact 30", fill=fontColor)

    def newImagePath(self, imgPath):
        extensionIndex = -3
        if imgPath[extensionIndex-1:] == "jpeg":
                extensionIndex = -4
        if imgPath[extensionIndex:] != "gif":
            newImgPath = imgPath[:extensionIndex] + "gif"
        else: newImgPath = imgPath
        return newImgPath

    def drawResultScreen(self, result, keyIndex, spec):
        if result == None: self.drawNoResult()
        else:
            bgR = self.mainDict[result][keyIndex][0]
            bgG = self.mainDict[result][keyIndex][1]
            bgB = self.mainDict[result][keyIndex][2]
            bgColor = self.rgbString(bgR, bgG, bgB)
            self.canvas.create_rectangle(0, 0, self.width, self.height, 
                                     fill=bgColor)
            fontColor = self.fontColor(bgR, bgG, bgB)
            fileIndex = 4
            imgPath = self.mainDict[result][keyIndex][fileIndex]
            madeGif = False
            newImgPath = self.newImagePath(imgPath)
            if newImgPath != imgPath: madeGif = True
            self.resultImage = Image.open(imgPath)
            self.resultImage.save(newImgPath)
            self.resultImage = PhotoImage(file=newImgPath)
            imageWidth = imageHeight = 300
            scaleWidth = self.resultImage.width()/imageWidth
            scaleHeight = self.resultImage.height()/imageHeight
            self.newImage = self.resultImage.subsample(scaleWidth, scaleHeight)
            self.canvas.create_image(self.width/2, self.height/2, 
                                     image=self.newImage)
            if madeGif:
                os.remove(newImgPath)
            self.resultText(result, spec, fontColor)

    def drawResult(self):
        if self.resultList != []:
            specIndex = 3
            result = self.resultList[self.resultIndex][1]
            keyIndex = self.resultList[self.resultIndex][2]
            spec = self.mainDict[result][keyIndex][specIndex]
        else: 
            result = keyIndex = None
            spec = ""
        self.drawResultScreen(result, keyIndex, spec)

    def createPicText(self, botMargin, leftMargin, rightMargin):
        leftTxt = "Swipe left to retake picture."
        rtTxt = "Swipe right to use this picture!"
        topTxt = "Your item picture:"
        centerX = self.width/2
        topMargin = 80
        self.canvas.create_text(centerX, topMargin, text=topTxt,
                                font="Impact 50")
        self.canvas.create_text(leftMargin, botMargin, text=leftTxt,
                                font="Impact 15")
        self.canvas.create_text(rightMargin, botMargin, text=rtTxt,
                                font="Impact 15")

    def drawConfirmPic(self):
        self.canvas.create_rectangle(0, 0, self.width, self.height, 
                                     fill=self.bgColor)
        imgPath = "tempItem.jpg"
        newImgPath = "tempItem.gif"
        self.confirmImage = Image.open(imgPath)
        self.confirmImage.save(newImgPath)
        self.confirmImage = PhotoImage(file=newImgPath)
        imageWidth = imageHeight = 400
        scaleWidth = self.confirmImage.width()/imageWidth
        scaleHeight = self.confirmImage.height()/imageHeight
        self.newConfImage = self.confirmImage.subsample(scaleWidth,scaleHeight)
        self.canvas.create_image(self.width/2, self.height/2, 
                                 image=self.newConfImage)
        os.remove(newImgPath)
        botMargin = self.height - 80
        leftMargin = 250
        rightMargin = self.width - leftMargin
        self.createArrows(botMargin, leftMargin, rightMargin)
        self.createPicText(botMargin, leftMargin, rightMargin)

    def drawCamInfo(self):
        firstText = "Hold the item as close to your camera as you can!"
        secondTxt = "Make sure it is in the center!"
        thirdTxt = "For optimal results, operate in a lit room."
        centerX, centerY = self.width/2, self.height/2
        lineGap = 60
        firstLineY = centerY - lineGap
        thirdLineY = centerY + lineGap
        self.canvas.create_rectangle(0, 0, self.width, self.height, 
                                     fill=self.bgColor, width=0)
        self.canvas.create_text(centerX, firstLineY, text=firstText,
                                font="Impact 25")
        self.canvas.create_text(centerX, centerY, text=secondTxt,
                                font="Impact 25")
        self.canvas.create_text(centerX, thirdLineY, text=thirdTxt,
                                font="Impact 25")

    def onKeyPressed(self, event):
        if self.addItem:
            if event.char in string.ascii_letters:
                if self.clickAddString:
                    self.addString += event.char
                elif self.clickSpecString:
                    self.specAddString += event.char
            elif event.keysym == "BackSpace":
                if self.clickAddString:
                    self.addString = self.addString[:-1]
                elif self.clickSpecString:
                    self.specAddString = self.specAddString[:-1]
        elif self.browseScreen:
            if event.char in string.ascii_letters:
                if self.clickBrowseStr:
                    self.curPage = self.pages = 0
                    self.browseStr += event.char
                elif self.clickBrowseSpec:
                    self.curPage = self.pages = 0
                    self.browseSpecStr += event.char
            elif event.keysym == "BackSpace":
                if self.clickBrowseStr:
                    self.curPage = self.pages = 0
                    self.browseStr = self.browseStr[:-1]
                elif self.clickBrowseSpec:
                    self.curPage = self.pages = 0
                    self.browseSpecStr = self.browseSpecStr[:-1]

    def drawAddConfirm(self):
        self.canvas.create_rectangle(0, 0, self.width, self.height,
                                     fill=self.bgColor, width=0)
        topText = "Item added!"
        botText = "Swipe down to return to the main menu!"
        centerX, centerY = self.width/2, self.height/2
        textGap = 50
        textOneY = centerY - textGap
        textTwoY = centerY + textGap
        self.canvas.create_text(centerX, textOneY, text=topText,
                                font="Impact 25")
        self.canvas.create_text(centerX, textTwoY, text=botText,
                                font="Impact 25")

    def loadTakenPic(self):
        self.loadPath = os.getcwd() + os.sep + "tempItem.jpg"
        self.moveAndRenameFile()

    def moveAndRenameFile(self):
        newPath = os.getcwd() + os.sep + "TrainingImgs"
        if self.specAddString != "":
            newName = self.addString + " " + self.specAddString
        else: newName = self.addString
        tempPath = newPath + os.sep + newName
        endCounter = 0
        newTempPath = tempPath
        extensionTempPath = newTempPath
        collision = False
        while not collision:
            fileExtensions = [".jpg", ".png", ".gif", ".jpeg"]
            for extension in fileExtensions:
                extensionTempPath = newTempPath + extension
                if os.path.exists(extensionTempPath):
                    collision = True
            break
        if collision:
            if newName == self.addString:
                    tempPath += " "
            extensionIndex = -4
            if self.loadPath[extensionIndex:] == "jpeg":
                extensionIndex = -5
            newTempPath = newTempPath + self.loadPath[extensionIndex:]
            while os.path.exists(newTempPath):
                endCounter += 1
                newTempPath = tempPath + str(endCounter) 
                newTempPath = newTempPath + self.loadPath[extensionIndex:]
            realPath = newTempPath
        else: 
            extensionIndex = -4
            if self.loadPath[extensionIndex:] == "jpeg":
                extensionIndex = -5
            realPath = tempPath + self.loadPath[extensionIndex:]
        shutil.copy(self.loadPath, realPath)
        self.loadPath = ""

    def loadFile(self):
        fileTypeList = [("Images", "*.jpg;*.jpeg;*.png;*.gif")]
        path = tkFileDialog.askopenfilename(initialdir=os.getcwd(), 
                                            filetypes=fileTypeList)
        if path != None and path != "":
            self.fileLoaded = True
            self.loadPath = path

    def mousePressBrowse(self, x, y):
        self.clickBrowseStr = self.clickBrowseSpec = False
        centerX, centerY, firstBoxY = self.width/2, self.height/2, 150
        boxGap = 100
        secondBoxY = firstBoxY + boxGap
        boxHeight, boxWidth = 30, self.width/4
        boxXStart = centerX - boxWidth
        boxXEnd = centerX + boxWidth
        firstBoxYStart = firstBoxY - boxHeight
        firstBoxYEnd = firstBoxY + boxHeight
        secBoxYStart = secondBoxY - boxHeight
        secBoxYEnd = secondBoxY + boxHeight
        if boxXStart <= x and x <= boxXEnd:
            if firstBoxYStart <= y and y <= firstBoxYEnd:
                self.clickBrowseStr = True
            elif secBoxYStart <= y and y <= secBoxYEnd:
                self.clickBrowseSpec = True

    def onMousePressed(self, event):
        (x, y) = (event.x, event.y)
        if self.addItem:
            self.clickAddString = self.clickSpecString = False
            centerX, centerY, firstBoxY = self.width/2, self.height/2, 150
            boxGap = 150
            secondBoxY = firstBoxY + boxGap
            boxHeight, boxWidth = 30, self.width/4
            boxXStart = centerX - boxWidth
            boxXEnd = centerX + boxWidth
            firstBoxYStart = firstBoxY - boxHeight
            firstBoxYEnd = firstBoxY + boxHeight
            secBoxYStart = secondBoxY - boxHeight
            secBoxYEnd = secondBoxY + boxHeight
            centerGap = 30
            loadWidth, loadHeight, loadY = 120, 50, centerY + centerGap
            loadXStart, loadXEnd = centerX - loadWidth, centerX + loadWidth
            loadYStart, loadYEnd = loadY - loadHeight, loadY + loadHeight
            if boxXStart <= x and x <= boxXEnd:
                if firstBoxYStart <= y and y <= firstBoxYEnd:
                    self.clickAddString = True
                elif secBoxYStart <= y and y <= secBoxYEnd:
                    self.clickSpecString = True
                elif (loadXStart <= x and x <= loadXEnd and loadYStart <= y
                    and y <= loadYEnd):
                    self.loadFile()
        elif self.browseScreen:
            self.mousePressBrowse(x, y)

    def takeAddPic(self):
        capture, start = cv2.VideoCapture(0), time.time()
        while(capture.isOpened()):
            correct, frame = capture.read()
            cv2.imshow('cv2', frame)
            waitTime = 5
            timeDiff = time.time() - start
            if timeDiff > waitTime:
                capture.release()
                cv2.imwrite("tempItem.jpg", frame)
                cv2.destroyAllWindows()
            if cv2.waitKey(1): pass
        self.takingPic2 = False
        self.confirmPic = True

    def drawAddArrows(self):
        arrowText = "Continue!"
        trianglePoint = 100
        midMargin = 25
        rtRectCX = self.width/2 - midMargin
        botGap = 150
        botMargin = self.height - botGap
        rectWidth, rectHeight, triangleGap = 100, 50, 50
        botStartY = botMargin - rectHeight
        botEndY = botMargin + rectHeight
        rightStartX = rtRectCX - rectWidth
        rightEndX = rtRectCX + rectWidth
        self.canvas.create_rectangle(rightStartX,botStartY,rightEndX,botEndY,
                                     fill="green", width=0)
        self.canvas.create_polygon(rightEndX, botEndY + triangleGap,
            rightEndX + trianglePoint, botEndY - rectHeight, rightEndX,
            botStartY - triangleGap, fill="green", width=0)
        self.canvas.create_text(self.width/2, botMargin, text=arrowText,
                                font="Impact 25", fill="white")

    def drawAddCont(self):
        centerX, centerY = self.width/2, self.height/2
        loadText = "Load Image (Optional)"
        noteText = "Note: Make sure item is centered!"
        centerGap = 30
        loadWidth, loadHeight, loadY = 120, 50, centerY + centerGap
        textGap = 20
        self.canvas.create_rectangle(centerX - loadWidth, loadY - loadHeight,
                        centerX + loadWidth, loadY + loadHeight,
                        fill="dark green")
        self.canvas.create_text(centerX, loadY - textGap, text=loadText,
                                font="Impact 15", fill="white")
        self.canvas.create_text(centerX, loadY + textGap, text=noteText,
                                font="Impact 12", fill="white")
        self.drawAddArrows()

    def drawAdd(self):
        addText = "Type in your general item name (i.e. Apple)."
        specTxt="If your item belongs to a subclass, enter it here (i.e. red)."
        centerX, firstBoxY = self.width/2, 150
        boxGap = 125
        secondBoxY = firstBoxY + boxGap
        boxHeight, boxWidth = 30, self.width/4
        self.canvas.create_rectangle(0, 0, self.width, self.height,
                                     fill=self.bgColor, width=0)
        self.canvas.create_rectangle(centerX - boxWidth, firstBoxY - boxHeight,
                        centerX + boxWidth, firstBoxY + boxHeight,
                        fill="white", width=1)
        self.canvas.create_rectangle(centerX - boxWidth, secondBoxY-boxHeight,
                        centerX + boxWidth, secondBoxY + boxHeight, 
                        fill="white", width=1)
        if self.addString == "":
            self.canvas.create_text(centerX, firstBoxY, text=addText,
                                    font="Impact 16")
        else:
            self.addString=self.addString[0].upper()+self.addString[1:].lower()
            self.canvas.create_text(centerX, firstBoxY, text=self.addString,
                                    font="Impact 18")
        if self.specAddString == "":
            self.canvas.create_text(centerX, secondBoxY, text=specTxt,
                                    font="Impact 16")
        else:
            self.specAddString = self.specAddString.lower()
            self.canvas.create_text(centerX, secondBoxY,
                                    text=self.specAddString, font="Impact 18")
        self.drawAddCont()

    def browseControl(self):
        nameStr = self.browseStr
        specStr = self.browseSpecStr
        tempList = []
        specIndex = 3
        if nameStr != "" and specStr == "":
            for key in self.mainDict.iterkeys():
                if len(key) >= len(nameStr) and key[:len(nameStr)] == nameStr:
                    for itemIndex in xrange(len(self.mainDict[key])):
                        spec = self.mainDict[key][itemIndex][specIndex]
                        R = self.mainDict[key][itemIndex][0]
                        G = self.mainDict[key][itemIndex][1]
                        B = self.mainDict[key][itemIndex][2]
                        color = self.rgbString(R, G, B)
                        tempList.append([key, spec, color])
        elif nameStr == "" and specStr != "":
            for key in self.mainDict.iterkeys():
                for itemIndex in xrange(len(self.mainDict[key])):
                    spec = self.mainDict[key][itemIndex][specIndex]
                    if (len(spec) >= len(specStr) and 
                        spec[:len(specStr)] == specStr):
                        R = self.mainDict[key][itemIndex][0]
                        G = self.mainDict[key][itemIndex][1]
                        B = self.mainDict[key][itemIndex][2]
                        color = self.rgbString(R, G, B)
                        tempList.append([key, spec, color])
        elif nameStr != "" and specStr != "":
            for key in self.mainDict.iterkeys():
                if len(key) >= len(nameStr) and key[:len(nameStr)] == nameStr:
                    for itemIndex in xrange(len(self.mainDict[key])):
                        spec = self.mainDict[key][itemIndex][specIndex]
                        if (len(spec) >= len(specStr) and 
                        spec[:len(specStr)] == specStr):
                            R = self.mainDict[key][itemIndex][0]
                            G = self.mainDict[key][itemIndex][1]
                            B = self.mainDict[key][itemIndex][2]
                            color = self.rgbString(R, G, B)
                            tempList.append([key, spec, color])
        elif nameStr == "" and specStr == "":
            for key in self.mainDict.iterkeys():
                for itemIndex in xrange(len(self.mainDict[key])):
                    spec = self.mainDict[key][itemIndex][specIndex]
                    R = self.mainDict[key][itemIndex][0]
                    G = self.mainDict[key][itemIndex][1]
                    B = self.mainDict[key][itemIndex][2]
                    color = self.rgbString(R, G, B)
                    tempList.append([key, spec, color])
        self.browseList = sorted(tempList)

    def drawItemsCont(self, items):
        startY, botGap, centerX = 350, 75, self.width/2
        endY = self.height - botGap
        ySpace = endY - startY
        yPerItem = ySpace / self.itemsPerPage
        oneY = startY
        twoY = oneY + yPerItem
        threeY = twoY + yPerItem
        fourY = threeY + yPerItem
        fiveY = fourY + yPerItem
        yVals = [oneY, twoY, threeY, fourY, fiveY]
        for itemListIndex in xrange(len(items)):
            itemList = items[itemListIndex]
            item = itemList[0]
            spec = itemList[1]
            color = itemList[2]
            if spec != "":
                string = "%s %s" % (spec, item)
            else:
                string = "%s" % (item)
            self.canvas.create_text(centerX, yVals[itemListIndex], text=string,
                                font="Impact 30", fill=color)

    def drawItems(self):
        self.pages = len(self.browseList) / self.itemsPerPage
        if len(self.browseList) % self.itemsPerPage == 0:
            self.pages -= 1 # this operates assuming 0 pages is actually 1
        indexOne = 0 + (self.curPage * self.itemsPerPage)
        indexTwo = 1 + (self.curPage * self.itemsPerPage)
        indexThree = 2 + (self.curPage * self.itemsPerPage)
        indexFour = 3 + (self.curPage * self.itemsPerPage)
        indexFive = 4 + (self.curPage * self.itemsPerPage)
        indexes = [indexOne, indexTwo, indexThree, indexFour, indexFive]
        items = []
        if self.curPage == self.pages:
            for item in xrange((len(self.browseList) % self.itemsPerPage)):
                browseIndex = indexes[item]
                curItem = self.browseList[browseIndex]
                items.append(curItem)
        else:
            for item in xrange(self.itemsPerPage):
                browseIndex = indexes[item]
                curItem = self.browseList[browseIndex]
                items.append(curItem)
        self.drawItemsCont(items)

    def drawBackArrow(self, backArrowTxt):
        leftRectCX = 180
        rectWidth, rectHeight, triangleGap = 90, 50, 30
        trianglePoint = 40
        midGap = 100
        textShift = 15
        textX = leftRectCX - textShift
        botMargin = self.height/2 + midGap
        leftStartX = leftRectCX - rectWidth
        leftEndX = leftRectCX + rectWidth
        botStartY = botMargin - rectHeight
        botEndY = botMargin + rectHeight
        self.canvas.create_rectangle(leftStartX, botStartY, leftEndX, botEndY,
                                     fill="firebrick1", width=0)
        self.canvas.create_polygon(leftStartX, botEndY + triangleGap,
            leftStartX - trianglePoint, botEndY - rectHeight, leftStartX,
            botStartY - triangleGap, fill="firebrick1", width=0)
        self.canvas.create_text(textX, botMargin, text=backArrowTxt,
                                font="Impact 20")

    def drawNextArrow(self, rtArrowTxt):
        leftMargin = 180
        rtRectCX = self.width - leftMargin
        textShift = 15
        textX = rtRectCX + textShift
        midGap = 100
        botMargin = self.height/2 + midGap
        rectWidth, rectHeight, triangleGap = 90, 50, 30
        trianglePoint = 40
        botStartY = botMargin - rectHeight
        botEndY = botMargin + rectHeight
        rightStartX = rtRectCX - rectWidth
        rightEndX = rtRectCX + rectWidth
        self.canvas.create_rectangle(rightStartX,botStartY,rightEndX,botEndY,
                                     fill="green", width=0)
        self.canvas.create_polygon(rightEndX, botEndY + triangleGap,
            rightEndX + trianglePoint, botEndY - rectHeight, rightEndX,
            botStartY - triangleGap, fill="green", width=0)
        self.canvas.create_text(textX, botMargin, text=rtArrowTxt,
                                font="Impact 20")

    def drawBrowseCont(self):
        if len(self.browseList) == 0: pass
        else:
            self.drawItems()
            if self.curPage != self.pages - 1:
                nextMatches = self.itemsPerPage
            else:
                nextMatches = len(self.browseList) % self.itemsPerPage
            rtArrowTxt = "Next %d matches" % (nextMatches)
            backArrowTxt = "Go back"
            if self.curPage != 0:
                self.drawBackArrow(backArrowTxt)
            if self.curPage != self.pages:
                self.drawNextArrow(rtArrowTxt)
        botTextGap = 65
        botMargin = self.height - botTextGap
        centerX = self.width/2
        botText = "Swipe down to return to main menu!"
        self.canvas.create_text(centerX, botMargin, text=botText,
                                font="Impact 20")

    def drawBrowse(self):
        mainText = "Type in your general item name here (i.e. Apple)."
        specTxt = "Search for subclasses here (i.e. red)."
        centerX, firstBoxY = self.width/2, 150
        boxGap = 100
        secondBoxY = firstBoxY + boxGap
        boxHeight, boxWidth = 30, self.width/4
        self.canvas.create_rectangle(0, 0, self.width, self.height,
                                     fill=self.bgColor, width=0)
        self.canvas.create_rectangle(centerX - boxWidth, firstBoxY - boxHeight,
                        centerX + boxWidth, firstBoxY + boxHeight, 
                        fill="white", width=1)
        self.canvas.create_rectangle(centerX - boxWidth, secondBoxY-boxHeight,
                        centerX + boxWidth, secondBoxY + boxHeight, 
                        fill="white", width=1)
        if self.browseStr == "":
            self.canvas.create_text(centerX, firstBoxY, text=mainText,
                                    font="Impact 16")
        else:
            self.browseStr=self.browseStr[0].upper()+self.browseStr[1:].lower()
            self.canvas.create_text(centerX, firstBoxY, text=self.browseStr,
                                    font="Impact 18")
        if self.browseSpecStr == "":
            self.canvas.create_text(centerX, secondBoxY, text=specTxt,
                                    font="Impact 16")
        else:
            self.browseSpecStr = self.browseSpecStr.lower()
            self.canvas.create_text(centerX, secondBoxY,
                                    text=self.browseSpecStr, font="Impact 18")
        self.drawBrowseCont()

    def drawTutCont(self, regionTxt, color):
        topText = "Use your index finger only! Try to stay in greenest region!"
        topTxt2 = ("Move your finger in the direction of the arrows to hit the"
                    " sweet spot!")
        midText = regionTxt
        botText = "While in gesture region, swipe right to enter main menu!"
        centerX, centerY = self.width/2, self.height/2
        topTextMargin = 100
        topTextGap = 50
        topTxt2Margin = topTextMargin + topTextGap
        botTextMargin = self.height - topTextMargin
        self.canvas.create_rectangle(0, 0, self.width, self.height,
                                    fill=color)
        self.canvas.create_text(centerX, topTextMargin, text=topText,
                                font="Impact 25")
        self.canvas.create_text(centerX, centerY, text=midText,
                                font="Impact 25")
        self.canvas.create_text(centerX, botTextMargin, text=botText,
                                font="Impact 20")
        self.canvas.create_text(centerX, topTxt2Margin, text=topTxt2,
                                font="Impact 18")

    def drawLeftArrow(self):
        leftRectCX = 180
        rectWidth, rectHeight, triangleGap = 50, 30, 30
        trianglePoint = 40
        botMargin = self.height/2
        leftStartX = leftRectCX - rectWidth
        leftEndX = leftRectCX + rectWidth
        botStartY = botMargin - rectHeight
        botEndY = botMargin + rectHeight
        self.canvas.create_rectangle(leftStartX, botStartY, leftEndX, botEndY,
                                     fill="black", width=0)
        self.canvas.create_polygon(leftStartX, botEndY + triangleGap,
            leftStartX - trianglePoint, botEndY - rectHeight, leftStartX,
            botStartY - triangleGap, fill="black", width=0)

    def drawRightArrow(self):
        leftMargin = 180
        rtRectCX = self.width - leftMargin
        botMargin = self.height/2
        rectWidth, rectHeight, triangleGap = 50, 30, 30
        trianglePoint = 40
        botStartY = botMargin - rectHeight
        botEndY = botMargin + rectHeight
        rightStartX = rtRectCX - rectWidth
        rightEndX = rtRectCX + rectWidth
        self.canvas.create_rectangle(rightStartX,botStartY,rightEndX,botEndY,
                                     fill="black", width=0)
        self.canvas.create_polygon(rightEndX, botEndY + triangleGap,
            rightEndX + trianglePoint, botEndY - rectHeight, rightEndX,
            botStartY - triangleGap, fill="black", width=0)

    def drawDownArrow(self):
        botRectCX = self.width/2
        botGap = 275
        botMargin = self.height - botGap
        rectWidth, rectHeight, triangleGap = 50, 30, 30
        trianglePoint = 40
        botStartX = botRectCX - rectHeight
        botEndX = botRectCX + rectHeight
        botStartY = botMargin - rectWidth
        botEndY = botMargin + rectWidth
        self.canvas.create_rectangle(botStartX, botStartY, botEndX, botEndY,
                                     fill="black", width=0)
        self.canvas.create_polygon(botStartX-triangleGap, botEndY,
            botRectCX, botEndY + trianglePoint, botEndX + triangleGap,
            botEndY, fill="black", width=0)

    def drawUpArrow(self):
        topRectCX = self.width/2
        topMargin = 275
        rectWidth, rectHeight, triangleGap = 50, 30, 30
        trianglePoint = 40
        topStartX = topRectCX - rectHeight
        topEndX = topRectCX + rectHeight
        topStartY = topMargin - rectWidth
        topEndY = topMargin + rectWidth
        self.canvas.create_rectangle(topStartX, topStartY, topEndX, topEndY,
                                     fill="black", width=0)
        self.canvas.create_polygon(topStartX-triangleGap, topStartY,
            topRectCX, topStartY - trianglePoint, topEndX + triangleGap,
            topStartY, fill="black", width=0)

    def drawTut(self):
        self.gameLaunched = True
        (x, y, dist, z) = self.painter.currentPos
        if dist > 0:
            regionTxt = "You are in the gesture region."
        else: regionTxt = "You are in the drawing region."
        targetX = self.width/2
        targetY = self.height/2
        zWeight = z*1000
        maxZ = 1000
        targetZ = 0
        xDiff = targetX - x
        yDiff = targetY - y
        zDiff = targetZ - zWeight
        distFrmTarget=((xDiff)**2+(yDiff)**2+(zDiff)**2)**0.5
        maxDist = (targetX**2 + targetY**2 + maxZ**2)**0.5
        ratio = distFrmTarget/maxDist
        percent = 1 - ratio
        (H, S, V) = (1/3.0, percent, 1)
        (R, G, B) = colorsys.hsv_to_rgb(H, S, V)
        R = int(R*255)
        G = int(G*255)
        B = int(B*255)
        color = self.rgbString(R, G, B)
        self.drawTutCont(regionTxt, color)
        if xDiff >= 0: self.drawRightArrow()
        elif xDiff < 0: self.drawLeftArrow()
        if yDiff >= 0: self.drawDownArrow()
        elif yDiff < 0: self.drawUpArrow()

    def redrawAll(self):
        if not self.painter.drawing:
            self.canvas.delete(ALL)
        if self.inMenu:
            self.drawMenu()
        elif self.inTut:
            self.drawTut()
        elif self.painter.drawing:
            self.drawPaint()
        elif self.possibleDrawing:
            self.drawConfirm()
        elif self.takingPic or self.takingPic2:
            self.drawCamInfo()
        elif self.resultScreen:
            self.drawResult()
        elif self.addItem:
            self.drawAdd()
        elif self.loadConfirm:
            self.drawAddConfirm()
        elif self.confirmPic:
            self.drawConfirmPic()
        elif self.browseScreen:
            self.drawBrowse()

    # not using redrawAll here since it would execute after every
    # timer fired, don't want that to happen here
    def redraw(self):
        self.canvas.delete(ALL)
        self.drawPaint()
        # what follows essentially clears PIL's image canvas by turning
        # all black (non-white) pixels white.
        pixel = self.image.load()
        for x in xrange(self.drawWidth):
            for y in xrange(self.drawHeight):
                if pixel[x, y] != (255, 255, 255):
                    pixel[x, y] = (255, 255, 255)

def main():
    paint = Painter()
    paint.run()

if __name__ == "__main__":
    main()