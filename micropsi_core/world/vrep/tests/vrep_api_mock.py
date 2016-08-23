
import numpy as np
import vrepConst
import random


def rand():
    return random.uniform(0, 1)


class VREPMock(object):

    def __init__(self, objects=[], joints=[], vision=[], collision=[]):
        self.objects = [None] + [ob for ob in objects]
        self.joint_threshold = len(objects) + 1
        self.objects.extend([j for j in joints])
        self.vision = [None] + [v for v in vision]
        self.positions = [None] + [[rand(), rand(), rand()] for ob in self.objects]
        self.orientations = [None] + [[rand(), rand(), rand()] for ob in self.objects]
        self.collisions = [None] + [c for c in collision]
        self.collision_states = [None] + [False for c in collision]
        self.is_synchronous = False
        for var in dir(vrepConst):
            if not var.startswith('__'):
                setattr(self, var, getattr(vrepConst, var))
        self.simstate = self.sim_simulation_paused
        self.initialized = False
        self.repeat_error_call = 1

    def mock_collision(self, collision_handle, state):
        self.collision_states[collision_handle] = state

    def mock_error_response(self, errcode=1):
        return errcode

    def mock_repeat_error_response(self, errcode=1):
        if self.repeat_error_call > 0:
            self.repeat_error_call -= 1
            return errcode
        else:
            self.repeat_error_call = 1
            return self.simx_return_ok

    def simxGetJointPosition(self, clientID, jointHandle, operationMode):
        return self.simx_return_ok, self.positions[jointHandle]

    def simxSetJointPosition(self, clientID, jointHandle, position, operationMode):
        if type(position) != list:
            position = [position, position, position]
        self.positions[jointHandle] = [sum(x) for x in zip(self.positions[jointHandle], position)]
        return self.simx_return_ok

    # def simxGetJointMatrix(self, clientID, jointHandle, operationMode):
    #     pass

    # def simxSetSphericalJointMatrix(self, clientID, jointHandle, matrix, operationMode):
    #     pass

    # def simxSetJointTargetVelocity(self, clientID, jointHandle, targetVelocity, operationMode):
    #     pass

    def simxSetJointTargetPosition(self, clientID, jointHandle, targetPosition, operationMode):
        if type(targetPosition) != list:
            targetPosition = [targetPosition, targetPosition, targetPosition]
        self.positions[jointHandle] = [sum(x) for x in zip(self.positions[jointHandle], targetPosition)]
        return self.simx_return_ok

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
            return self.simx_return_ok, self.objects.index(objectName)
        except:
            pass
        try:
            return self.simx_return_ok, self.vision.index(objectName)
        except:
            pass
        return self.simx_return_ok, -1

    def simxGetVisionSensorImage(self, clientID, sensorHandle, options, operationMode):
        if self.vision[sensorHandle]:
            return self.simx_return_ok, [16, 16], np.empty((16, 16, 3))
        return self.simx_return_remote_error_flag

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
        return self.simx_return_ok

    def simxPauseSimulation(self, clientID, operationMode):
        self.simstate = self.sim_simulation_paused
        return self.simx_return_ok

    def simxStopSimulation(self, clientID, operationMode):
        self.simstate = self.sim_simulation_stopped
        return self.simx_return_ok

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
        return self.simx_return_ok, self.orientations[objectHandle]

    def simxGetObjectPosition(self, clientID, objectHandle, relativeToObjectHandle, operationMode):
        return self.simx_return_ok, self.positions[objectHandle]

    def simxSetObjectOrientation(self, clientID, objectHandle, relativeToObjectHandle, eulerAngles, operationMode):
        self.orientations[objectHandle] = eulerAngles
        return self.simx_return_ok

    def simxSetObjectPosition(self, clientID, objectHandle, relativeToObjectHandle, position, operationMode):
        if type(position) != list:
            position = [position, position, position]
        self.positions[objectHandle] = position
        return self.simx_return_ok

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
            return self.simx_return_ok, self.collisions.index(collisionObjectName)
        except:
            return self.simx_return_ok, -1

    # def simxGetCollectionHandle(self, clientID, collectionName, operationMode):
    #     pass

    # def simxGetDistanceHandle(self, clientID, distanceObjectName, operationMode):
    #     pass

    def simxReadCollision(self, clientID, collisionObjectHandle, operationMode):
        return self.simx_return_ok, self.collision_states[collisionObjectHandle]

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
            return self.simx_return_ok, list([idx for idx, name in enumerate(self.objects) if idx >= self.joint_threshold])
        else:
            return self.simx_return_ok, list([idx for idx, name in enumerate(self.objects) if idx < self.joint_threshold and name is not None])

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
        self.initialized = True
        return 1

    def simxFinish(self, clientID):
        self.initialized = False
        return 1

    def simxGetPingTime(self, clientID):
        return self.simx_return_ok, 1

    def simxGetLastCmdTime(self, clientID):
        return self.simx_return_ok, 1

    def simxSynchronousTrigger(self, clientID):
        return self.simx_return_ok

    def simxSynchronous(self, clientID, enable):
        self.is_synchronous = enable
        return self.simx_return_ok

    def simxPauseCommunication(self, clientID, enable):
        return self.simx_return_ok

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
                return self.simx_return_ok, handles, [], pos, []

    def simxCallScriptFunction(self, clientID, scriptDescription, options, functionName, inputInts, inputFloats, inputStrings, inputBuffer, operationMode):
        if functionName == 'getsimstate':
            return self.simx_return_ok, [self.simstate], [], []
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