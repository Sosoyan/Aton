__author__ = "Ryan Heniser, Vahan Sosoyan"
__copyright__ = "2018 All rights reserved. See Copyright.txt for more details."
__version__ = "1.3.0"

import os
import hou

from hutil.Qt import QtCore, QtWidgets, QtGui
from htoa.node.parms import HaNodeSetStr
from htoa.node.node import nodeSetArrayString

from arnold import *


def warn(msg, *params):
    header = '[%s] ' % __name__
    AiMsgWarning(header + msg, *params)


def atonPatch():
    import htoa.session
    # Only monkey patch once -- the arnold.py soho script from HtoA can and
    # typically will be called many times. Only monkey patch (decorate) the
    # generate method once.
    if htoa.object.rop.HaRop.generate.__name__ == 'generate':
        htoa.session.HaRop.generate = generateDecorated(htoa.session.HaRop.generate)

def atonUpdate(self):
    
    if self.session.isInteractiveRender():

        options_node = AiUniverseGetOptions()

        if AiNodeLookUpUserParameter(options_node, 'aton_enable'):
            
            if AiNodeGetBool(options_node, 'aton_enable'):
                
                driver = "driver_aton"
                
                if not (AiNodeEntryLookUp(driver) is None):
                    
                    aton_node = getAtonDriver(self, driver, 'aton')

                    AiNodeSetStr(aton_node, "host", AiNodeGetStr(options_node, "aton_host"))
                    AiNodeSetInt(aton_node, "port", AiNodeGetInt(options_node, "aton_port"))
                    AiNodeSetStr(aton_node, "output", AiNodeGetStr(options_node, "aton_output"))
                    
                    if AiNodeLookUpUserParameter(options_node, 'aton_bucket'):
                        AiNodeSetStr(options_node, "bucket_scanning", AiNodeGetStr(options_node, "aton_bucket"))

                    if AiNodeLookUpUserParameter(options_node, 'aton_region_min_x'):
                        AiNodeSetInt(options_node, 'region_min_x', AiNodeGetInt(options_node, 'aton_region_min_x'))
                    if AiNodeLookUpUserParameter(options_node, 'aton_region_min_y'):
                        AiNodeSetInt(options_node, 'region_min_y', AiNodeGetInt(options_node, 'aton_region_min_y'))
                    if AiNodeLookUpUserParameter(options_node, 'aton_region_max_x'):
                        AiNodeSetInt(options_node, 'region_max_x', AiNodeGetInt(options_node, 'aton_region_max_x'))
                    if AiNodeLookUpUserParameter(options_node, 'aton_region_max_y'):
                        AiNodeSetInt(options_node, 'region_max_y', AiNodeGetInt(options_node, 'aton_region_max_y'))
                    
                    if AiNodeLookUpUserParameter(options_node, 'aton_ignore_mbl'):
                        AiNodeSetBool(options_node, 'ignore_motion_blur', AiNodeGetBool(options_node, 'aton_ignore_mbl'))
                    if AiNodeLookUpUserParameter(options_node, 'aton_ignore_sdv'):
                        AiNodeSetBool(options_node, 'ignore_subdivision', AiNodeGetBool(options_node, 'aton_ignore_sdv'))
                    if AiNodeLookUpUserParameter(options_node, 'aton_ignore_dsp'):
                        AiNodeSetBool(options_node, 'ignore_displacement', AiNodeGetBool(options_node, 'aton_ignore_dsp'))
                    if AiNodeLookUpUserParameter(options_node, 'aton_ignore_bmp'):
                        AiNodeSetBool(options_node, 'ignore_bump', AiNodeGetBool(options_node, 'aton_ignore_bmp'))
                    if AiNodeLookUpUserParameter(options_node, 'aton_ignore_sss'):
                        AiNodeSetBool(options_node, 'ignore_sss', AiNodeGetBool(options_node, 'aton_ignore_sss'))

                    # Get the outputs string array param (on the options node) as a python list
                    array = AiNodeGetArray(options_node, 'outputs')
                    elements = AiArrayGetNumElements(array)
                    outputs = [AiArrayGetStr(array, i) for i in xrange(elements)]

                    # RGBA primary should be the first in outputs--its last string
                    # should be the node name of the driver_houdini (IPR) main driver
                    name = outputs[0].split()[-1]
                    aton_outputs = [i.replace(name, AiNodeGetName(aton_node)) for i in outputs if i.endswith(name)]
                    nodeSetArrayString(options_node, 'outputs', aton_outputs)
                
                else:
                    warn("Aton Driver was not found.")
            else:
                warn("Aton is not Enabled.")
        else:
            warn("Aton User Options was not found.")

def generateDecorated(func):
    def generateDecorator(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        atonUpdate(self)
        return result
    
    return generateDecorator


def getAtonDriver(self, nodeEntryName, newSubStr):
    from htoa.object.camera import cameraTag

    nodeIter = AiUniverseGetNodeIterator(AI_NODE_DRIVER)
    while not AiNodeIteratorFinished(nodeIter):
        node = AiNodeIteratorGetNext(nodeIter)
        nodeEntry = AiNodeGetNodeEntry(node)
        if AiNodeEntryGetName(nodeEntry) == nodeEntryName:
            return node

    driverAtoNNode = AiNode(nodeEntryName)
    camTag = cameraTag(self.session.camera_name)
    HaNodeSetStr(driverAtoNNode, 'name',
                 (self.path + ':' + newSubStr + (':%s' % camTag if camTag else '')))
    return driverAtoNNode

def getHost():
    ''' Returns a host name from Aton driver '''
    aton_host = os.getenv("ATON_HOST")
    
    if (aton_host is None):
        return "127.0.0.1"
    else:
        return aton_host
    
def getPort(id):
    ''' Returns a port number from Aton driver '''
    aton_port = os.getenv("ATON_PORT")
    
    if aton_port is None:
        return 9200 + id;
    else:
        return int(aton_port)

def getOutputDrivers(path = False):
    ''' Returns a list of all output driver names '''
    rops = hou.nodeType(hou.nodeTypeCategories()['Driver'], 'arnold').instances()
    
    if path:
        return [i.path() for i in rops]
    
    return rops

def getBucketModes():
    rops = getOutputDrivers()
    if rops:
        parmTemplateGroup = rops[0].parmTemplateGroup()
        parmTamplateName = 'ar_bucket_scanning'
        parmTemplateExist = parmTemplateGroup.find(parmTamplateName)
        if parmTemplateExist:
            return rops[0].parm(parmTamplateName).parmTemplate().menuItems()

def getAllCameras(path = False):
    ''' Returns a list of all camera names '''
    cameras = hou.nodeType(hou.nodeTypeCategories()['Object'], 'cam').instances()
    
    if path:
        return [i.path() for i in cameras]
    
    return cameras

def getCurrentCamera(path = False):
    camera = hou.ui.paneTabOfType(hou.paneTabType.SceneViewer).curViewport().camera()
    if camera is not None:
        if path:
            return camera.path()
        else:
            return camera


class Output(object):
    def __init__(self, rop=None):
        if rop:

            userOptionsParmName = 'ar_user_options'
            parmTemplateGroup = rop.parmTemplateGroup()
            parmTemplate = parmTemplateGroup.find(userOptionsParmName)

            if parmTemplate:            
                self._init_attributes(rop)

        else:
            self._init_blank()
    
    @property
    def cameraPath(self):
        if self.camera:
            return self.camera.path()

    def _init_attributes(self, rop):
        self.rop = rop
        self.name = rop.name()
        self.path = rop.path()
        self.camera = self._get_camera()
        self._cameraResolution = self.camera.parmTuple('res').eval() if self.camera else (0,0)
        self.overrideCameraRes = rop.parm('override_camerares').eval()
        self.resFraction = rop.parm('res_fraction').eval()
        self.resOverride = rop.parmTuple('res_override').eval()
        self.resolution = self._get_resolution()
        self.AASamples = rop.parm('ar_AA_samples').eval()
        self.bucketScanning = rop.parm('ar_bucket_scanning').eval()
        self.userOptionsEnable = rop.parm('ar_user_options_enable').eval()
        self.userOptionsParm = rop.parm('ar_user_options')
        self.userOptions = self.userOptionsParm.eval()


    def _init_blank(self):
        self.rop = None
        self.name = None
        self.path = None
        self.camera = None
        self.overrideCameraRes = None
        self.resFraction = None
        self.resolution = (0,0)
        self.AASamples = 0
        self.bucketScanning = None
        self.userOptionsEnable = None
        self.userOptionsParm = None
        self.userOptions = None
   
    def _get_camera(self):
        camera = hou.node(self.rop.parm('camera').eval())
        if camera is None:
            sceneCameras = getAllCameras()
            if sceneCameras:
                camera = sceneCameras[0]
        return camera

    def _get_resolution(self):
        if self.rop.parm('override_camerares').eval():
            res_scale = self.rop.parm('res_fraction').eval()
            
            if res_scale == 'specific':
                return self.rop.parmTuple('res_override').eval()
            else:
                return (int(self._cameraResolution[0] * float(res_scale)), 
                        int(self._cameraResolution[1] * float(res_scale)))

        return self._cameraResolution

    def rollback(self):
        self.rop.parm('camera').set(self.cameraPath)
        self.rop.parm('override_camerares').set(self.overrideCameraRes)
        self.rop.parm('res_fraction').set(self.resFraction)
        self.rop.parmTuple('res_override').set(self.resOverride)
        self.rop.parm('ar_AA_samples').set(self.AASamples)
        self.rop.parm('ar_user_options_enable').set(self.userOptionsEnable)
        self.rop.parm('ar_user_options').set(self.userOptions)


class BoxWidget(QtWidgets.QFrame):
        def __init__(self, label, first=True):
            super(BoxWidget, self).__init__()
            self.label = QtWidgets.QLabel(label + ":")
            self.label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignCenter)

            if first:
                    self.label.setMinimumSize(75, 20)
                    self.label.setMaximumSize(75, 20)

            self.layout = QtWidgets.QHBoxLayout(self)
            self.layout.setSizeConstraint(QtWidgets.QLayout.SetMaximumSize)
            self.layout.setContentsMargins(0, 0, 0, 0)
            self.layout.addWidget(self.label)

class LineEditBox(BoxWidget):
        def __init__(self, label, text='', first=True):
            super(LineEditBox, self).__init__(label, first)

            self.lineEditBox = QtWidgets.QLineEdit()
            self.lineEditBox.setText(u"%s" % text)
            self.layout.addWidget(self.lineEditBox)

        def setEnabled(self, value):
            self.label.setEnabled(value)
            self.lineEditBox.setEnabled(value)

        def text(self):
            return self.lineEditBox.text()

        def setText(self, text):
            self.lineEditBox.setText(text)

class SliderBox(BoxWidget):
        def __init__(self, label, value=0, first=True):
            super(SliderBox, self).__init__(label, first)

            self.spinBox = QtWidgets.QSpinBox()
            self.spinBox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
            self.spinBox.setValue(value)

            self.slider = QtWidgets.QSlider()
            self.slider.setOrientation(QtCore.Qt.Horizontal)
            self.slider.setValue(value)

            self.slider.valueChanged.connect(self.spinBox.setValue)

            self.layout.addWidget(self.spinBox)
            self.layout.addWidget(self.slider)

        def setMinimum(self, spinValue=None, sliderValue=None):
            if spinValue is not None: self.spinBox.setMinimum(spinValue)
            if sliderValue is not None: self.slider.setMinimum(sliderValue)

        def setMaximum(self, spinValue=None, sliderValue=None):
            if spinValue is not None: self.spinBox.setMaximum(spinValue)
            if sliderValue is not None: self.slider.setMaximum(sliderValue)

        def setValue(self, spinValue=None, sliderValue=None):
            if sliderValue is not None: self.slider.setValue(sliderValue)
            if spinValue is not None: self.spinBox.setValue(spinValue)

        def setEnabled(self, value):
            self.spinBox.setEnabled(value)
            self.slider.setEnabled(value)
        
        def value(self):
            return self.spinBox.value()

        def connect(self, func):
            self.slider.valueChanged.connect(func)

        def setEnabled(self, value):
            self.label.setEnabled(value)
            self.spinBox.setEnabled(value)
            self.slider.setEnabled(value)

        @property
        def valueChanged(self):
            return self.spinBox.valueChanged

class SpinBox(BoxWidget):
        def __init__(self, label, value=0, first=True):
            super(SpinBox, self).__init__(label, first)
            self.spinBox = QtWidgets.QSpinBox()
            self.spinBox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
            self.spinBox.setValue(value)
            self.spinBox.setMaximumSize(50, 20)
            self.spinBox.setRange(-99999, 99999)
        
            self.layout.addWidget(self.spinBox)

        def value(self):
            return self.spinBox.value()

        def setValue(self, value):
            self.spinBox.setValue(value)

        @property
        def valueChanged(self):
            return self.spinBox.valueChanged

class ComboBox(BoxWidget):
        def __init__(self, label, first=True):
            super(ComboBox, self).__init__(label, first)
            self.items = list()

            self.comboBox = QtWidgets.QComboBox()
            self.comboBox.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                        QtWidgets.QSizePolicy.Fixed)
            self.currentIndexChanged = self.comboBox.currentIndexChanged

            self.layout.addWidget(self.comboBox)

        def setEnabled(self, value):
            self.label.setEnabled(value)
            self.comboBox.setEnabled(value)

        def setCurrentIndex(self, value):
            self.comboBox.setCurrentIndex(value)


        def setCurrentName(self, value):
            for idx, item in enumerate(self.items):
                if item == value:
                    self.comboBox.setCurrentIndex(idx)

        def currentIndex(self):
            return self.comboBox.currentIndex()

        def currentName(self):
            index = self.comboBox.currentIndex()
            if self.items:
                return self.items[index]

        def addItems(self, items):
            if items:
                for i in items:
                    self.comboBox.addItem(i)
                self.items += items

        def newItems(self, items):
            if items:
                self.clear()
                for i in items:
                    self.comboBox.addItem(i)
                self.items += items


        def clear(self):
            self.comboBox.clear()
            self.items = []

class CheckBox(BoxWidget):
        def __init__(self, label, title='', first=True):
            super(CheckBox, self).__init__(label, first)
            self.checkBox = QtWidgets.QCheckBox(title)
    
            self.layout.addWidget(self.checkBox)

        @property
        def stateChanged(self):
            return self.checkBox.stateChanged

        def isChecked(self):
            return self.checkBox.isChecked()

        def setChecked(self, value):
            self.checkBox.setChecked(value)


class Aton(QtWidgets.QWidget):
    
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        
        self.objName = self.__class__.__name__.lower()

        # Properties
        self._output = None
        
        # Default Settings
        self.defaultPort = getPort(self.getInstanceCount())
        self.defaultHost = getHost()
        self.outputsList = [Output(rop) for rop in getOutputDrivers()]

        # Init UI
        self.setObjectName(self.objName)
        self.setProperty("saveWindowPref", True)
        self.setProperty("houdiniStyle", True)
        self.setStyleSheet(hou.qt.styleSheet())
        self.setWindowIcon(QtGui.QIcon(self.icon_path))

        # Setup UI
        self.setupUI()
        
    @property
    def icon_path(self):
        path = os.path.split(__file__)

        if path:
            path = os.path.abspath(os.path.join(path[0], os.pardir))
            path = os.path.abspath(os.path.join(path, os.pardir))
            path = os.path.abspath(os.path.join(path, os.pardir))
            path = os.path.join(path, 'config/Icons/aton_icon.png')
            return path
        
    @property
    def ipr(self):
        desk = hou.ui.curDesktop()
        return desk.paneTabOfType(hou.paneTabType.IPRViewer)

    @property
    def output(self):
        idx  = self.outputComboBox.currentIndex()
        if idx >= 0:
            self._output = self.outputsList[idx]
        else:
            self._output = Output()
        return self._output

    def closeEvent(self, event):

        if self.ipr.isActive():
            self.ipr.killRender()
        self.removeAtonOverrides()
        
        self.setParent(None)
        self.destroy()

    def setupUI(self):

        def buildUI():

            self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.setAttribute(QtCore.Qt.WA_AlwaysShowToolTips)

            # Main Layout
            mainLayout = QtWidgets.QVBoxLayout()
            
            # General Group
            generalGroupBox = QtWidgets.QGroupBox("General")
            generalLayout = QtWidgets.QVBoxLayout(generalGroupBox)
            
            # Host Layout
            hostLayout = QtWidgets.QHBoxLayout()
            self.hostLineEdit = LineEditBox("Host", u"%s"%self.defaultHost)
            self.hostCheckBox = QtWidgets.QCheckBox()
            self.hostCheckBox.setChecked(True)
            self.hostCheckBox.stateChanged.connect(self.hostLineEdit.setEnabled)
            hostLayout.addWidget(self.hostLineEdit)
            hostLayout.addWidget(self.hostCheckBox)

            # Port Layout
            portLayout = QtWidgets.QHBoxLayout()
            self.portSlider = SliderBox("Port")
            self.portSlider.setMinimum(0, 0)
            self.portSlider.setMaximum(9999, 15)
            self.portSlider.setValue(self.defaultPort)
            self.portSlider.connect(portUpdateUI)
            self.portCheckBox = QtWidgets.QCheckBox()
            self.portCheckBox.setChecked(True)
            self.portCheckBox.stateChanged.connect(self.portSlider.setEnabled)
            portLayout.addWidget(self.portSlider)
            portLayout.addWidget(self.portCheckBox)

            # Output Driver Layout
            outputDriverLayout = QtWidgets.QHBoxLayout()
            self.outputComboBox = ComboBox("Output")
            self.outputComboBox.addItems([i.path for i in self.outputsList])
            self.outputComboBox.currentIndexChanged.connect(outputUpdateUI)
            self.setWindowTitle('%s - %s' %(self.__class__.__name__, self.output.name))
            outputDriverLayout.addWidget(self.outputComboBox)

            # Camera Layout
            cameraLayout = QtWidgets.QHBoxLayout()
            self.cameraComboBox = ComboBox("Camera")
            self.cameraComboBox.addItems(getAllCameras(path=True))
            self.cameraComboBox.setCurrentName(self.output.cameraPath)
            cameraLayout.addWidget(self.cameraComboBox)

            # Overrides Group
            overridesGroupBox = QtWidgets.QGroupBox("Overrides")
            overridesLayout = QtWidgets.QVBoxLayout(overridesGroupBox)

            # IPR Update Layout
            IPRUpdateLayout = QtWidgets.QHBoxLayout()
            self.IPRUpdateCheckBox = CheckBox('IPR', " Auto Update")
            self.IPRUpdateCheckBox.setChecked(self.ipr.isAutoUpdateOn())
            self.IPRUpdateCheckBox.stateChanged.connect(lambda: self.ipr.setAutoUpdate(
                                                                self.IPRUpdateCheckBox.isChecked()))
            IPRUpdateLayout.addWidget(self.IPRUpdateCheckBox)

            # Bucket Layout
            bucketLayout = QtWidgets.QHBoxLayout()
            self.bucketComboBox = ComboBox("Bucket Scan")
            self.bucketComboBox.addItems(getBucketModes())
            self.bucketComboBox.setCurrentName(self.output.bucketScanning)
            bucketLayout.addWidget(self.bucketComboBox)

            # Resolution Layout
            resolutionLayout = QtWidgets.QHBoxLayout()
            self.resolutionSlider = SliderBox("Resolution %")
            self.resolutionSlider.setMinimum(1, 1)
            self.resolutionSlider.setMaximum(200, 40)
            self.resolutionSlider.setValue(100, 20)
            self.resolutionSlider.connect(resUpdateUI)
            xres, yres = self.output.resolution[0], self.output.resolution[1]
            self.resolutionInfoLabel = QtWidgets.QLabel(str(xres)+'x'+str(yres))
            self.resolutionInfoLabel.setMaximumSize(100, 20)
            self.resolutionInfoLabel.setEnabled(False)
            resolutionLayout.addWidget(self.resolutionSlider)
            resolutionLayout.addWidget(self.resolutionInfoLabel)

            # Camera AA Layout
            cameraAaLayout = QtWidgets.QHBoxLayout()
            self.cameraAaSlider = SliderBox("Camera (AA)")
            self.cameraAaSlider.setMinimum(-64, -3)
            self.cameraAaSlider.setMaximum(64, 16)
            self.cameraAaSlider.setValue(self.output.AASamples, self.output.AASamples)
            cameraAaLayout.addWidget(self.cameraAaSlider)

            # Render region layout
            renderRegionLayout = QtWidgets.QHBoxLayout()
            self.renderRegionXSpinBox = SpinBox("Region X")
            self.renderRegionYSpinBox = SpinBox("Y", 0, False)
            self.renderRegionRSpinBox = SpinBox("R", 0, False)
            self.renderRegionTSpinBox = SpinBox("T", 0, False)
            self.renderRegionRSpinBox.setValue(self.output.resolution[0])
            self.renderRegionTSpinBox.setValue(self.output.resolution[1])
            renderRegionGetNukeButton = QtWidgets.QPushButton("Get")
            renderRegionGetNukeButton.clicked.connect(self.getNukeCropNode)
            renderRegionLayout.addWidget(self.renderRegionXSpinBox)
            renderRegionLayout.addWidget(self.renderRegionYSpinBox)
            renderRegionLayout.addWidget(self.renderRegionRSpinBox)
            renderRegionLayout.addWidget(self.renderRegionTSpinBox)
            renderRegionLayout.addWidget(renderRegionGetNukeButton)

            # Overscan Layout
            overscanLayout = QtWidgets.QHBoxLayout()
            self.overscanSlider = SliderBox("Overscan")
            self.overscanSlider.setMinimum(0)
            self.overscanSlider.setMaximum(9999, 250)
            self.overscanSlider.setValue(0, 0)
            overscanLayout.addWidget(self.overscanSlider)

            # Ignore Group
            ignoresGroupBox = QtWidgets.QGroupBox("Ignore")
            ignoresGroupBox.setMaximumSize(9999, 75)

            # Ignore Layout
            ignoresLayout = QtWidgets.QVBoxLayout(ignoresGroupBox)
            ignoreLayout = QtWidgets.QHBoxLayout()
            self.motionBlurCheckBox = QtWidgets.QCheckBox(' Motion Blur')
            self.subdivsCheckBox = QtWidgets.QCheckBox(" Subdivs")
            self.displaceCheckBox = QtWidgets.QCheckBox(' Displace')
            self.bumpCheckBox = QtWidgets.QCheckBox(' Bump')
            self.sssCheckBox = QtWidgets.QCheckBox(' SSS')
            ignoreLayout.addWidget(self.motionBlurCheckBox)
            ignoreLayout.addWidget(self.subdivsCheckBox)
            ignoreLayout.addWidget(self.displaceCheckBox)
            ignoreLayout.addWidget(self.bumpCheckBox)
            ignoreLayout.addWidget(self.sssCheckBox)

            # Main Buttons Layout
            mainButtonslayout = QtWidgets.QHBoxLayout()
            startButton = QtWidgets.QPushButton("Start / Refresh")
            stopButton = QtWidgets.QPushButton("Stop")
            resetButton = QtWidgets.QPushButton("Reset")
            startButton.clicked.connect(self.startRender)
            stopButton.clicked.connect(self.stopRender)
            resetButton.clicked.connect(resetUI)
            mainButtonslayout.addWidget(startButton)
            mainButtonslayout.addWidget(stopButton)
            mainButtonslayout.addWidget(resetButton)

            # Add Layouts to Main
            generalLayout.addLayout(hostLayout)
            generalLayout.addLayout(portLayout)
            generalLayout.addLayout(outputDriverLayout)
            overridesLayout.addLayout(IPRUpdateLayout)
            overridesLayout.addLayout(cameraLayout)
            overridesLayout.addLayout(bucketLayout)
            overridesLayout.addLayout(resolutionLayout)
            overridesLayout.addLayout(cameraAaLayout)
            overridesLayout.addLayout(renderRegionLayout)
            overridesLayout.addLayout(overscanLayout)
            ignoresLayout.addLayout(ignoreLayout)

            mainLayout.addWidget(generalGroupBox)
            mainLayout.addWidget(overridesGroupBox)
            mainLayout.addWidget(ignoresGroupBox)
            mainLayout.addLayout(mainButtonslayout)

            addUICallbacks()

            return mainLayout

        def portUpdateUI(value):
            self.portSlider.spinBox.setValue(value + self.defaultPort)

        def outputUpdateUI(index):
            if index >= 0:
                self.setWindowTitle('%s - %s' %(self.__class__.__name__, self.output.name))
                resUpdateUI(self.resolutionSlider.slider.value())
                self.cameraComboBox.setCurrentName(self.output.cameraPath)
                self.bucketComboBox.setCurrentName(self.output.bucketScanning)
                self.cameraAaSlider.setValue(self.output.AASamples, self.output.AASamples)
                self.renderRegionRSpinBox.setValue(self.output.resolution[0])
                self.renderRegionTSpinBox.setValue(self.output.resolution[1])
        
        def resUpdateUI(value):
            self.resolutionSlider.setValue(value * 5)
            xres = self.output.resolution[0] * value * 5 / 100
            yres = self.output.resolution[1] * value * 5 / 100
            self.resolutionInfoLabel.setText("%dx%d"%(xres, yres))

        def resetUI(*args):
            if self.ipr.isActive():
                self.stopRender()
            
            # Update Defualt Settings
            self.outputsList = [Output(rop) for rop in getOutputDrivers()]

            self.hostCheckBox.setChecked(True)
            self.portCheckBox.setChecked(True)
            self.hostLineEdit.setText(self.defaultHost)
            self.portSlider.setValue(self.defaultPort, 0)
            self.IPRUpdateCheckBox.setChecked(True)

            self.bucketComboBox.newItems(getBucketModes())
            self.cameraComboBox.newItems(getAllCameras(path=True))     
            self.outputComboBox.newItems(getOutputDrivers(path=True))

            self.resolutionSlider.setValue(100, 20)
            self.renderRegionXSpinBox.setValue(0)
            self.renderRegionYSpinBox.setValue(0)
            self.overscanSlider.setValue(0, 0)
            self.motionBlurCheckBox.setChecked(False)
            self.subdivsCheckBox.setChecked(False)
            self.displaceCheckBox.setChecked(False)
            self.bumpCheckBox.setChecked(False)
            self.sssCheckBox.setChecked(False)

            outputUpdateUI(self.outputComboBox.currentIndex())
  
        def addUICallbacks():
            self.cameraComboBox.currentIndexChanged.connect(self.addAtonOverrides)
            self.bucketComboBox.currentIndexChanged.connect(self.addAtonOverrides)
            self.cameraAaSlider.valueChanged.connect(self.addAtonOverrides)
            self.resolutionSlider.valueChanged.connect(self.addAtonOverrides)
            self.renderRegionXSpinBox.valueChanged.connect(self.addAtonOverrides)
            self.renderRegionYSpinBox.valueChanged.connect(self.addAtonOverrides)
            self.renderRegionRSpinBox.valueChanged.connect(self.addAtonOverrides)
            self.renderRegionTSpinBox.valueChanged.connect(self.addAtonOverrides)
            self.overscanSlider.valueChanged.connect(self.addAtonOverrides)
            self.motionBlurCheckBox.toggled.connect(self.addAtonOverrides)
            self.subdivsCheckBox.toggled.connect(self.addAtonOverrides)
            self.displaceCheckBox.toggled.connect(self.addAtonOverrides)
            self.bumpCheckBox.toggled.connect(self.addAtonOverrides)
            self.sssCheckBox.toggled.connect(self.addAtonOverrides)

        self.setLayout(buildUI())

    def generalUISetEnabled(self, value):
        self.hostLineEdit.setEnabled(value)
        self.hostCheckBox.setEnabled(value)
        self.portSlider.setEnabled(value)
        self.portCheckBox.setEnabled(value)
        self.outputComboBox.setEnabled(value)

    def getInstanceCount(self):
        count = 1
        for w in QtWidgets.QApplication.instance().topLevelWidgets():
            if w.objectName() == self.objName:
                count += 1
        return count

    def getNukeCropNode(self, *args):
        ''' Get crop node data from Nuke '''
        def find_between(s, first, last):
            try:
                start = s.index(first) + len(first)
                end = s.index(last, start)
                return s[start:end]
            except ValueError:
                return ""

        clipboard = QtWidgets.QApplication.clipboard()
        data = clipboard.text()

        cropData = None
        checkData1 = "set cut_paste_input [stack 0]"
        checkData2 = "Crop {"

        if (checkData1 in data.split('\n', 10)[0]) and \
           (checkData2 in data.split('\n', 10)[3]):
                cropData = find_between(data.split('\n', 10)[4], "box {", "}" ).split()

        if len(data.split(',')) == 4:
            cropData = data.split(',')

        if cropData is not None:
            nkX, nkY, nkR, nkT = int(float(cropData[0])),\
                                 int(float(cropData[1])),\
                                 int(float(cropData[2])),\
                                 int(float(cropData[3]))

            self.renderRegionXSpinBox.setValue(nkX)
            self.renderRegionYSpinBox.setValue(nkY)
            self.renderRegionRSpinBox.setValue(nkR)
            self.renderRegionTSpinBox.setValue(nkT)

    def getRegion(self, attr, resScale = True):
        if resScale:
            resValue = self.resolutionSlider.value()
        else:
            resValue = 100

        ovrScnValue = self.overscanSlider.value() * resValue / 100

        xres = self.output.resolution[0] * resValue / 100
        yres = self.output.resolution[1] * resValue / 100

        result = {0 : lambda: xres,
                  1 : lambda: yres,
                  2 : lambda: (self.renderRegionXSpinBox.value() * resValue / 100) - ovrScnValue,
                  3 : lambda: yres - (self.renderRegionTSpinBox.value() * resValue / 100) - ovrScnValue,
                  4 : lambda: (self.renderRegionRSpinBox.value() * resValue / 100) - 1 + ovrScnValue,
                  5 : lambda: (yres - (self.renderRegionYSpinBox.value() * resValue / 100)) - 1 + ovrScnValue}[attr]()

        return result      

    def iprIsNotActive(self):
        return not self.ipr.isActive()  

    def startRender(self):

        if self.output:
            
            # Set IPR Options
            self.ipr.setPreview(True)  
            self.ipr.killRender()
            self.ipr.setRopNode(self.output.rop)
            self.ipr.startRender()
            
            # Add Aton Overrides
            self.addAtonOverrides()
            self.generalUISetEnabled(False)

    def stopRender(self):
        self.ipr.killRender()
        self.removeAtonOverrides()
        self.generalUISetEnabled(True)

    def AASamplesChanged(self):
        return self.cameraAaSlider.value() != self.output.AASamples

    def cameraChanged(self):
        return self.cameraComboBox.currentName() != self.output.camera.path()

    def resolutionChanged(self):
        xRes, yRes = self.getRegion(0), self.getRegion(1)
        xReg, yReg, rReg, tReg = self.getRegion(2), self.getRegion(3), \
                                 self.getRegion(4), self.getRegion(5)
        
        if xRes != self.output.resolution[0] or yRes != self.output.resolution[1]:
            return True
        elif xReg != 0 or yReg != 0 or rReg != xRes -1 or tReg != yRes -1:
            return True
        elif self.overscanSlider.value() != 0:
            return True
        else:
            return False

    def bucketScanningChanged(self):
        return self.bucketComboBox.currentName() != self.output.bucketScanning

    def ignoreMBLChanged(self):
        return self.motionBlurCheckBox.isChecked()

    def ignoreSDVChanged(self):
        return self.subdivsCheckBox.isChecked()

    def ignoreDSPChanged(self):
        return self.displaceCheckBox.isChecked()

    def ignoreBMPChanged(self):
        return self.bumpCheckBox.isChecked()

    def ignoreSSSChanged(self):
        return self.sssCheckBox.isChecked()

    def addAtonOverrides(self,):
        if self.ipr.isActive():

            userOptions = self.output.userOptions
            
            if not userOptions is None:

                self.ipr.pauseRender()

                # Enable User Options Overrides
                self.output.rop.parm('ar_user_options_enable').set(True)

                # Aton Attributes
                userOptions += ' ' if userOptions else ''
                userOptions += 'declare aton_enable constant BOOL aton_enable on '
                userOptions += 'declare aton_host constant STRING aton_host \"%s\" '%self.hostLineEdit.text()
                userOptions += 'declare aton_port constant INT aton_port %d '%self.portSlider.value()
                userOptions += 'declare aton_output constant STRING aton_output \"%s\" '%self.output.name

                # Camera
                if self.cameraChanged():
                    self.output.rop.parm('camera').set(self.cameraComboBox.currentName())
                else:
                     self.output.rop.parm('camera').set(self.output.camera.path())

                # AA Samples
                if self.AASamplesChanged():
                    self.output.rop.parm('ar_AA_samples').set(self.cameraAaSlider.value())
                else:
                    self.output.rop.parm('ar_AA_samples').set(self.output.AASamples)

                # Resolution
                if self.resolutionChanged():
                    self.output.rop.parm('override_camerares').set(True)
                    self.output.rop.parm('res_fraction').set('specific')
                    self.output.rop.parm('res_overridex').set(self.getRegion(0))
                    self.output.rop.parm('res_overridey').set(self.getRegion(1))
                    
                    # Render Region
                    userOptions += 'declare aton_region_min_x constant INT aton_region_min_x %d '%self.getRegion(2)
                    userOptions += 'declare aton_region_min_y constant INT aton_region_min_y %d '%self.getRegion(3)
                    userOptions += 'declare aton_region_max_x constant INT aton_region_max_x %d '%self.getRegion(4)
                    userOptions += 'declare aton_region_max_y constant INT aton_region_max_y %d '%self.getRegion(5)
                else:
                    self.output.rop.parm('override_camerares').set(self.output.overrideCameraRes)
                    self.output.rop.parm('res_fraction').set(self.output.resFraction)
                    self.output.rop.parm('res_overridex').set(self.output.resOverride[0])
                    self.output.rop.parm('res_overridey').set(self.output.resOverride[1])

                # Bucket Scanning
                if self.bucketScanningChanged():
                    userOptions += 'declare aton_bucket constant STRING aton_bucket \"%s\" '%self.bucketComboBox.currentName()

                # Ignore Feautres
                if self.ignoreMBLChanged():
                    userOptions += 'declare aton_ignore_mbl constant BOOL aton_ignore_mbl %s '%('on' if self.motionBlurCheckBox.isChecked() else 'off')
                if self.ignoreSDVChanged():
                    userOptions += 'declare aton_ignore_sdv constant BOOL aton_ignore_sdv %s '%('on' if self.subdivsCheckBox.isChecked() else 'off')
                if self.ignoreDSPChanged():
                    userOptions += 'declare aton_ignore_dsp constant BOOL aton_ignore_dsp %s '%('on' if self.displaceCheckBox.isChecked() else 'off')
                if self.ignoreBMPChanged():
                    userOptions += 'declare aton_ignore_bmp constant BOOL aton_ignore_bmp %s '%('on' if self.bumpCheckBox.isChecked() else 'off')
                if self.ignoreSSSChanged():
                    userOptions += 'declare aton_ignore_sss constant BOOL aton_ignore_sss %s '%('on' if self.sssCheckBox.isChecked() else 'off')

                self.output.userOptionsParm.set(userOptions)
           
                self.ipr.resumeRender()
            else:
                self.stopRender()


    def removeAtonOverrides(self):
        for output in self.outputsList:
            output.rollback()
