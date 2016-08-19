import vrepConst
import random


def rand():
    return random.uniform(0, 1)


class VREPMock(object):

    def __init__(self, objects=[], joints=[], vision=[], collision=[]):
        self.objects = [None] + [ob for ob in objects]
        self.joint_threshold = len(objects)
        self.objects.extend([j for j in joints])
        self.vision = [None] + [v for v in vision]
        self.positions = [None] + [[0, 0, 0] for ob in self.objects]
        self.orientations = [None] + [[0, 0, 0] for ob in self.objects]
        self.collisions = [None] + [c for c in collision]
        self.is_synchronous = False
        for var in dir(vrepConst):
            if not var.startswith('__'):
                setattr(self, var, getattr(vrepConst, var))
        self.simstate = self.sim_simulation_paused


    def simxGetJointPosition(self, clientID, jointHandle, operationMode):
        return 0, self.positions[jointHandle]

    def simxSetJointPosition(self, clientID, jointHandle, position, operationMode):
        if type(position) != list:
            position = [position, rand(), rand()]
        self.positions[jointHandle] = position
        return 0

    # def simxGetJointMatrix(self, clientID, jointHandle, operationMode):
    #     pass

    # def simxSetSphericalJointMatrix(self, clientID, jointHandle, matrix, operationMode):
    #     pass

    # def simxSetJointTargetVelocity(self, clientID, jointHandle, targetVelocity, operationMode):
    #     pass

    def simxSetJointTargetPosition(self, clientID, jointHandle, targetPosition, operationMode):
        if type(targetPosition) != list:
            targetPosition = [targetPosition, rand(), rand()]
        self.positions[jointHandle] = targetPosition
        return 0

    # def simxJointGetForce(self, clientID, jointHandle, operationMode):
    #     pass

    # def simxGetJointForce(self, clientID, jointHandle, operationMode):
    #     pass

    # def simxSetJointForce(self, clientID, jointHandle, force, operationMode):
    #     pass

    # def simxReadForceSensor(self, clientID, forceSensorHandle, operationMode):
    #     pass

    # def simxBreakForceSensor(self, clientID, forceSensorHandle, operationMode):
    #     pass

    # def simxReadVisionSensor(self, clientID, sensorHandle, operationMode):
    #     pass

    def simxGetObjectHandle(self, clientID, objectName, operationMode):
        try:
            return 0, self.objects.index(objectName)
        except:
            return 0, -1

    def simxGetVisionSensorImage(self, clientID, sensorHandle, options, operationMode):
        return 0, self.vision[sensorHandle]

    # def simxSetVisionSensorImage(self, clientID, sensorHandle, image, options, operationMode):
    #     pass

    # def simxGetVisionSensorDepthBuffer(self, clientID, sensorHandle, operationMode):
    #     pass

    # def simxGetObjectChild(self, clientID, parentObjectHandle, childIndex, operationMode):
    #     pass

    # def simxGetObjectParent(self, clientID, childObjectHandle, operationMode):
    #     pass

    # def simxReadProximitySensor(self, clientID, sensorHandle, operationMode):
    #     pass

    # def simxLoadModel(self, clientID, modelPathAndName, options, operationMode):
    #     pass

    # def simxLoadUI(self, clientID, uiPathAndName, options, operationMode):
    #     pass

    # def simxLoadScene(self, clientID, scenePathAndName, options, operationMode):
    #     pass

    def simxStartSimulation(self, clientID, operationMode):
        if self.is_synchronous:
            self.simstate = self.sim_simulation_advancing
        else:
            self.simstate = self.sim_simulation_advancing_running
        return 0

    def simxPauseSimulation(self, clientID, operationMode):
        self.simstate = self.sim_simulation_paused
        return 0

    def simxStopSimulation(self, clientID, operationMode):
        self.simstate = self.sim_simulation_stopped
        return 0

    # def simxGetUIHandle(self, clientID, uiName, operationMode):
    #     pass

    # def simxGetUISlider(self, clientID, uiHandle, uiButtonID, operationMode):
    #     pass

    # def simxSetUISlider(self, clientID, uiHandle, uiButtonID, position, operationMode):
    #     pass

    # def simxGetUIEventButton(self, clientID, uiHandle, operationMode):
    #     pass

    # def simxGetUIButtonProperty(self, clientID, uiHandle, uiButtonID, operationMode):
    #     pass

    # def simxSetUIButtonProperty(self, clientID, uiHandle, uiButtonID, prop, operationMode):
    #     pass

    # def simxAddStatusbarMessage(self, clientID, message, operationMode):
    #     pass

    # def simxAuxiliaryConsoleOpen(self, clientID, title, maxLines, mode, position, size, textColor, backgroundColor, operationMode):
    #     pass

    # def simxAuxiliaryConsoleClose(self, clientID, consoleHandle, operationMode):
    #     pass

    # def simxAuxiliaryConsolePrint(self, clientID, consoleHandle, txt, operationMode):
    #     pass

    # def simxAuxiliaryConsoleShow(self, clientID, consoleHandle, showState, operationMode):
    #     pass

    def simxGetObjectOrientation(self, clientID, objectHandle, relativeToObjectHandle, operationMode):
        return 0, self.orientations[objectHandle]

    def simxGetObjectPosition(self, clientID, objectHandle, relativeToObjectHandle, operationMode):
        return 0, self.positions[objectHandle]

    def simxSetObjectOrientation(self, clientID, objectHandle, relativeToObjectHandle, eulerAngles, operationMode):
        self.orientations[objectHandle] = eulerAngles
        return 0

    def simxSetObjectPosition(self, clientID, objectHandle, relativeToObjectHandle, position, operationMode):
        if type(position) != list:
            position = [position, rand(), rand()]
        self.positions[objectHandle] = position
        return 0

    # def simxSetObjectParent(self, clientID, objectHandle, parentObject, keepInPlace, operationMode):
    #     pass

    # def simxSetUIButtonLabel(self, clientID, uiHandle, uiButtonID, upStateLabel, downStateLabel, operationMode):
    #     pass

    # def simxGetLastErrors(self, clientID, operationMode):
    #     pass

    # def simxGetArrayParameter(self, clientID, paramIdentifier, operationMode):
    #     pass

    # def simxSetArrayParameter(self, clientID, paramIdentifier, paramValues, operationMode):
    #     pass

    # def simxGetBooleanParameter(self, clientID, paramIdentifier, operationMode):
    #     pass

    # def simxSetBooleanParameter(self, clientID, paramIdentifier, paramValue, operationMode):
    #     pass

    # def simxGetIntegerParameter(self, clientID, paramIdentifier, operationMode):
    #     pass

    # def simxSetIntegerParameter(self, clientID, paramIdentifier, paramValue, operationMode):
    #     pass

    # def simxGetFloatingParameter(self, clientID, paramIdentifier, operationMode):
    #     pass

    # def simxSetFloatingParameter(self, clientID, paramIdentifier, paramValue, operationMode):
    #     pass

    # def simxGetStringParameter(self, clientID, paramIdentifier, operationMode):
    #     pass

    def simxGetCollisionHandle(self, clientID, collisionObjectName, operationMode):
        try:
            return 0, self.collisions.index(collisionObjectName)
        except:
            return 0, -1

    # def simxGetCollectionHandle(self, clientID, collectionName, operationMode):
    #     pass

    # def simxGetDistanceHandle(self, clientID, distanceObjectName, operationMode):
    #     pass

    def simxReadCollision(self, clientID, collisionObjectHandle, operationMode):
        return False

    # def simxReadDistance(self, clientID, distanceObjectHandle, operationMode):
    #     pass

    # def simxRemoveObject(self, clientID, objectHandle, operationMode):
    #     pass

    # def simxRemoveModel(self, clientID, objectHandle, operationMode):
    #     pass

    # def simxRemoveUI(self, clientID, uiHandle, operationMode):
    #     pass

    # def simxCloseScene(self, clientID, operationMode):
    #     pass

    def simxGetObjects(self, clientID, objectType, operationMode):
        if objectType == self.sim_object_joint_type:
            return 0, list([idx for idx, name in enumerate(self.objects) if idx >= self.joint_threshold])
        else:
            return 0, list([idx for idx, name in enumerate(self.objects) if idx < self.joint_threshold and name is not None])

    # def simxDisplayDialog(self, clientID, titleText, mainText, dialogType, initialText, titleColors, dialogColors, operationMode):
    #     pass

    # def simxEndDialog(self, clientID, dialogHandle, operationMode):
    #     pass

    # def simxGetDialogInput(self, clientID, dialogHandle, operationMode):
    #     pass

    # def simxGetDialogResult(self, clientID, dialogHandle, operationMode):
    #     pass

    # def simxCopyPasteObjects(self, clientID, objectHandles, operationMode):
    #     pass

    # def simxGetObjectSelection(self, clientID, operationMode):
    #     pass

    # def simxSetObjectSelection(self, clientID, objectHandles, operationMode):
    #     pass

    # def simxClearFloatSignal(self, clientID, signalName, operationMode):
    #     pass

    # def simxClearIntegerSignal(self, clientID, signalName, operationMode):
    #     pass

    # def simxClearStringSignal(self, clientID, signalName, operationMode):
    #     pass

    # def simxGetFloatSignal(self, clientID, signalName, operationMode):
    #     pass

    # def simxGetIntegerSignal(self, clientID, signalName, operationMode):
    #     pass

    # def simxGetStringSignal(self, clientID, signalName, operationMode):
    #     pass

    # def simxGetAndClearStringSignal(self, clientID, signalName, operationMode):
    #     pass

    # def simxReadStringStream(self, clientID, signalName, operationMode):
    #     pass

    # def simxSetFloatSignal(self, clientID, signalName, signalValue, operationMode):
    #     pass

    # def simxSetIntegerSignal(self, clientID, signalName, signalValue, operationMode):
    #     pass

    # def simxSetStringSignal(self, clientID, signalName, signalValue, operationMode):
    #     pass

    # def simxAppendStringSignal(self, clientID, signalName, signalValue, operationMode):
    #     pass

    # def simxWriteStringStream(self, clientID, signalName, signalValue, operationMode):
    #     pass

    # def simxGetObjectFloatParameter(self, clientID, objectHandle, parameterID, operationMode):
    #     pass

    # def simxSetObjectFloatParameter(self, clientID, objectHandle, parameterID, parameterValue, operationMode):
    #     pass

    # def simxGetObjectIntParameter(self, clientID, objectHandle, parameterID, operationMode):
    #     pass

    # def simxSetObjectIntParameter(self, clientID, objectHandle, parameterID, parameterValue, operationMode):
    #     pass

    # def simxGetModelProperty(self, clientID, objectHandle, operationMode):
    #     pass

    # def simxSetModelProperty(self, clientID, objectHandle, prop, operationMode):
    #     pass

    def simxStart(self, connectionAddress, connectionPort, waitUntilConnected, doNotReconnectOnceDisconnected, timeOutInMs, commThreadCycleInMs):
        return 1

    def simxFinish(self, clientID):
        return 1

    def simxGetPingTime(self, clientID):
        return 0, 1

    def simxGetLastCmdTime(self, clientID):
        return 0, 1

    def simxSynchronousTrigger(self, clientID):
        return 0

    def simxSynchronous(self, clientID, enable):
        self.is_synchronous = enable
        return 0

    def simxPauseCommunication(self, clientID, enable):
        return 0

    # def simxGetInMessageInfo(self, clientID, infoType):
    #     pass

    # def simxGetOutMessageInfo(self, clientID, infoType):
    #     pass

    # def simxGetConnectionId(self, clientID):
    #     pass

    # def simxCreateBuffer(self, bufferSize):
    #     pass

    # def simxReleaseBuffer(self, buffer):
    #     pass

    # def simxTransferFile(self, clientID, filePathAndName, fileName_serverSide, timeOut, operationMode):
    #     pass

    # def simxEraseFile(self, clientID, fileName_serverSide, operationMode):
    #     pass

    # def simxCreateDummy(self, clientID, size, color, operationMode):
    #     pass

    # def simxQuery(self, clientID, signalName, signalValue, retSignalName, timeOutInMs):
    #     pass

    def simxGetObjectGroupData(self, clientID, objectType, dataType, operationMode):
        if objectType == self.sim_object_joint_type:
            if dataType == 15:
                # force/torque]
                handles = list([idx for idx, name in enumerate(self.objects) if idx >= self.joint_threshold])
                pos = [self.positions[h] for h in handles]
                pos = [item for sublist in pos for item in sublist]
                return 0, handles, [], pos, []

    def simxCallScriptFunction(self, clientID, scriptDescription, options, functionName, inputInts, inputFloats, inputStrings, inputBuffer, operationMode):
        if functionName == 'getsimstate':
            return 0, [self.simstate], [], []
        else:
            raise

    # def simxGetObjectVelocity(self, clientID, objectHandle, operationMode):
    #     pass

    # def simxPackInts(self, intList):
    #     pass

    # def simxUnpackInts(self, intsPackedInString):
    #     pass

    # def simxPackFloats(self, floatList):
    #     pass

    # def simxUnpackFloats(self, floatsPackedInString):
    #     pass