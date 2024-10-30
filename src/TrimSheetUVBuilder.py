#alt+shift+m to send to maya
#commandPort -n "localhost:7001" -stp "mel";
import maya.cmds as mc
import maya.mel as mel
import maya.OpenMayaUI as omui
from maya.OpenMaya import MVector
from PySide2.QtWidgets import QWidget, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QSlider, QGridLayout
from PySide2.QtCore import Qt
from shiboken2 import wrapInstance


class TrimSheetUVBilderWidget(QWidget):
    def __init__(self):
        mayaMainWindow = TrimSheetUVBilderWidget.GetMayaMainWindow()

        for existing in mayaMainWindow.findChildren(QWidget, TrimSheetUVBilderWidget.GetWindowUniqueId()):
            existing.deleteLater()

        super().__init__(parent=mayaMainWindow)
        self.setWindowTitle("TrimSheet UV Bilder")
        self.setWindowFlags(Qt.Window)
        self.setObjectName(TrimSheetUVBilderWidget.GetWindowUniqueId())

        self.masterlayout = QVBoxLayout()
        self.setLayout(self.masterlayout)

        self.shell =[]
        self.CreateInitiaizationSection()
        self.CreateManipuationSection()

    def ScaleShell(self, us, vs):
        mc.polyEditUV(self.shell, su=us, sv=vs, r=True)

    def GetShellSize(self):
        min,max, = self.GetShellBound()
        width =max[0] -min [0]
        height = max[1] -min[1]
        return width, height

    def FillShellToU1V1(self):
        width, height =self.GetShellSize()
        self.ScaleShell(1/width,1/height)
        self.MoveShellToOrigin()

    def MoveShell(self, u , v):
        width, height = self.GetShellSize()
        mc.polyEditUV(self.shell, u= width * u,v= height * v)


    def CreateManipuationSection(self):
        sectionLayout = QVBoxLayout()
        self.masterlayout.addLayout(sectionLayout)

        turnBtn = QPushButton("Turn")
        turnBtn.clicked.connect(self.Turn)
        sectionLayout.addWidget(turnBtn)

        movetoOriginBtn = QPushButton("Move to Origin")
        movetoOriginBtn.clicked.connect(self.MoveToOrigin)
        sectionLayout.addWidget(movetoOriginBtn)

        fillU1VBtn = QPushButton("Fill UV")
        fillU1VBtn.clicked.connect(self.FillShellToU1V1)
        sectionLayout.addWidget(fillU1VBtn)

        doubleUBtn = QPushButton("Double U")
        doubleUBtn.clicked.connect(lambda : self.ScaleShell(2, 1))
        sectionLayout.addWidget(doubleUBtn)

        HalfUBtn = QPushButton("Half U")
        HalfUBtn.clicked.connect(lambda : self.ScaleShell(0.5, 1))
        sectionLayout.addWidget(HalfUBtn)

        doubleVBtn = QPushButton("Double V")
        doubleVBtn.clicked.connect(lambda : self.ScaleShell(1, 2))
        sectionLayout.addWidget(doubleVBtn)

        HalfVBtn = QPushButton("Half V")
        HalfVBtn.clicked.connect(lambda : self.ScaleShell(1, 0.5))
        sectionLayout.addWidget(HalfVBtn)

        moveLayout = QGridLayout()
        sectionLayout.addLayout(moveLayout)

        moveUpBtn = QPushButton("Move Up")
        moveUpBtn.clicked.connect(lambda :self.MoveShell(0,1))
        moveLayout.addWidget(moveUpBtn, 0 ,1)

        movedownBtn = QPushButton("Move down")
        movedownBtn.clicked.connect(lambda :self.MoveShell(0,-1))
        moveLayout.addWidget(movedownBtn, 2 ,1)

        moveleftBtn = QPushButton("Move left")
        moveleftBtn.clicked.connect(lambda :self.MoveShell(-1,0))
        moveLayout.addWidget(moveleftBtn, 1,0)

        moverightBtn = QPushButton("Move right")
        moverightBtn.clicked.connect(lambda :self.MoveShell(1,0))
        moveLayout.addWidget(moverightBtn, 1,2)
        

    def GetShellBound(self):
        uvs = mc.polyListComponentConversion(self.shell, toUV=True)
        uvs = mc.ls(uvs, fl=True)

        firstUVCoord = mc.polyEditUV(uvs[0], q=True)
        minU = firstUVCoord[0]
        maxU = firstUVCoord[0]
        minV = firstUVCoord[1]
        minV = firstUVCoord[1]

        for uv in uvs:
            uvCoord = mc.polyEditUV(uv, q=True)
            if uvCoord[0] < minU:
                minU = uvCoord[0]

            if uvCoord[0] > maxU:
                maxU = uvCoord[0]

            if uvCoord[0] < minV:
                minV = uvCoord[1]

            if uvCoord[0] < maxV:
                maxV = uvCoord[1]

        return [minU, minV,], [maxU, maxV]
    
    def MoveToOrigin(self):
        min, max = self.GetShellBound()
        mc.polyEditUV(self.shell, u = -min[0], v = -min[1])



    def Turn(self):
        mc.select(self.shell, r=True)
        mel.eval("polyRotateUVs 90 1")


    def CreateInitiaizationSection(self):
        sectionLayout =QHBoxLayout()
        self.masterlayout.addLayout(sectionLayout)

        selectShellBtn= QPushButton("Select Shell")
        selectShellBtn.clicked.connect(self.SelectShell)
        sectionLayout.addWidget(selectShellBtn)

        unfoldBtn = QPushButton("Unfold")
        unfoldBtn.clicked.connect(self.Unfold)
        sectionLayout.addWidget(unfoldBtn)

        cutAndUnfoldBtn = QPushButton("Cut and Unfold")
        cutAndUnfoldBtn.clicked.connect(self.CutAndUnfold)
        sectionLayout.addWidget(cutAndUnfoldBtn)

        unitizeBtn = QPushButton("Unitize")
        unitizeBtn.clicked.connect(self.Unitize)
        sectionLayout.addWidget(unitizeBtn)

    def Unitize(self):
        edges = mc.polyListComponentConversion(self.shell, toEdge=True)
        edges = mc.ls(edges, fl=True)

        sewedEdges = []
        for edge in edges:
            vertices = mc.polyListComponentConversion(edge, toVertex=True)
            vertices = mc.ls(vertices,fl=True)

            uvs = mc.polyListComponentConversion(edge, toUV = True)
            uvs = mc.ls(uvs, fl=True)

            if len(vertices) == len(uvs):
                sewedEdges.append(edge)

        mc.polyForceUV(self.shell, unitize=True)
        mc.polyMapSewMove(sewedEdges)
        mc.u3dLayout(self.shell)

    def CutAndUnfold(self):
        edgesToCut = mc.ls(sl=True, fl=True)
        mc.polyProjection(self.shell, type="Planar", md="c")
        mc.polyMapCut(edgesToCut)
        mc.u3dUnfold(self.shell)
        mc.select(self.shell, r=True)
        mel.eval("texOrientShells")
        mc.u3dLayout(self.shell)


    def Unfold(self):
        mc.polyProjection(self.shell, type="Planar", md="c")
        mc.u3dUnfold(self.shell)
        mc.select(self.shell, r=True)
        mel.eval("texOrientShells")
        mc.u3dLayout(self.shell)

    def SelectShell(self):
        self.shell = mc.ls(sl=True)





    @staticmethod
    def GetMayaMainWindow():
        mayaMainWindow = omui.MQtUtil.mainWindow()
        return wrapInstance(int(mayaMainWindow), QMainWindow)

    @staticmethod
    def GetWindowUniqueId():
        return "92452989fde2e1f7bffcb681d6b27804"

def Run():
    TrimSheetUVBilderWidget().show()