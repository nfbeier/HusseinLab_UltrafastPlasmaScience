# Author: Dr. Nicholas Beier

from newportxps import NewportXPS

class Actuator(object):
    '''
    Actuator class that contains information for a single Newport XPS Actuator.
    Intended to act as an object interfaced through the XPS class groupList dictionary
    
    XPS actuators come with defined group and positioner names that enabled different funcitonality:
    By default the group name is Group# where # is the XPS driver slot connected to the actuator
    and the positioner name is Group#.pos
    
    There are also minimum and maximum limits of motion for individual actuators defined by the
    limit switches. The minimum and maximum motion can be redefined to prevent damage or motion
    out of range of a desired experimental setup.
    
    Attributes
    ----------
    
    groupName : str
        Name of the actuator group as seen in the XPS Motion Menu
        
    posName : str
        Actuator positioner name. By default it is groupName + ".pos"
        
    minLimit : float
        Minimum limit for actuator motion in mm. By default set to 0 mm
        
    maxLimit : float
        Maximum limit for actuator motion in mm. By default set to 50 mm
    '''
    
    def __init__(self,name):
        '''
        Initializes the Actuator object with a given group name, default positioner name
        and two inches of travel.
        '''
        self.groupName = name
        self.posName = name + ".Pos"
        self.minLimit = 0
        self.maxLimit = 50
    
    def setGroup(self, newGroup):
        '''
        Set the actuator group name to a different group

        Parameters
        ----------
        newGroup : str
            Group name for new group

        Returns
        -------
        None.

        '''
        self.groupName = newGroup
    
    def getGroup(self):
        '''
        
        Returns
        -------
        str
            Group name of the actuator

        '''
        return self.groupName

    def setPos(self, pos):
        '''
        Set the actuator positioner name to a different name

        Parameters
        ----------
        pos : str
            Sets the positioner name to a new value.

        Returns
        -------
        None.

        '''
        self.posName = pos
        
    def getPos(self):
        '''

        Returns
        -------
        str
            Returns positioner name of the Actuator.

        '''
        return self.posName

    def setMinLimit(self,lim):
        '''
        Define the minimum travel positionin in millimeters

        Parameters
        ----------
        lim : float
            Minimum travel limit for actuator in mm.

        Returns
        -------
        None.
        
        '''
        self.minLimit = lim
        
    def getMinLimit(self):
        '''

        Returns
        -------
        TYPE
            Returns the minimum travel positionin in millimeters
        
        '''
        return self.minLimit
    
    def setMaxLimit(self,lim):
        '''
        Define the maximum travel position in millimeters

        Parameters
        ----------
        lim : float
            Maximum travel limit for actuator in mm. 
            WARNING: Make sure stage has enough throw to handle actuator limit.

        Returns
        -------
        None.
        
        '''
        self.maxLimit = lim
        
    def getMaxLimit(self):
        '''

        Returns
        -------
        float
            Returns the minimum travel positionin in millimeters.
            
        '''
        return self.maxLimit

class XPS(Actuator):
    '''
    XPS Class that interfaces with the Newport XPS Motion Controller through the
    Actuator class.
    
    The XPS Motion Controller can be interfaced through the Python package newportxps
    which can be found at https://github.com/pyepics/newportxps
    
    The XPS is assumed to be connected to the computer through a local ethernet connection
    with an IP Address of 192.167.0.254 and username/password of Administrator.
    
    Attributes
    ----------
    
    xps : str
        Name of the actuator group as seen in the XPS Motion Menu
        
   groupList : str
        Actuator positioner name. By default it is groupName + ".pos"
    '''
    
    
    def __init__(self,ipAddress = '192.168.0.79',username = 'Administrator',password = 'Administrator'):
        '''
        Initializes the XPS class.
        
        Attempts to establish connection with the XPS through IP Address.
        The groupList dictionary acts as a repository for the XPS actuators that
        are in use. Initialized as empty dictionary and is populated by actuators
        one at a time.
        
        The key passed to the dictionary should be the Actuator group name.
        '''
        
        try:
            self.xps = NewportXPS(ipAddress, username = username, password = password)
        except:
            print("XPS connection cannot be established.")
        self.groupList = {}
    
    def getXPSStatus(self):
        '''

        Returns
        -------
        str
            Returns the status of all groups currently connected to the XPS.
        
        '''
        return self.xps.get_group_status()
    
    def getStageStatus(self, group):
        '''
        Gets current status of the desired group

        Parameters
        ----------
        group : str
            Group name.

        Returns
        -------
        str
            Current status of group.

        '''
        return str(self.xps.get_group_status()[self.groupList[group].getGroup()])
    
    def getGroups(self):
        '''

        Returns
        -------
        list of str
            Returns all actuators populating the group list dictionary.
        
        '''
        return self.groupList
    
    def setGroup(self,newGroup):
        '''
        Adds to the grouplist dictionary a new actuator with Group Name newGroup

        Parameters
        ----------
        newGroup : str
            New group to be added to the group list.

        Returns
        -------
        None.
        
        '''
        self.groupList[newGroup] = Actuator(newGroup)
        
    def getStagePosition(self, group):
        '''

        Parameters
        ----------
        group : str
            Desired group name.

        Returns
        -------
        TYPE
            Returns the current stage position of the desired group in millimeters.

        '''
        return float(self.xps.get_stage_position(self.groupList[group].getPos()))
    
    def getminLimit(self,group):
        '''

        Parameters
        ----------
        group : str
            Desired group name.

        Returns
        -------
        float
            Returns the minimum motion limit for the desired group in millimeters.

        '''
        return self.groupList[group].getMinLimit()
    
    def getmaxLimit(self,group):
        '''

        Parameters
        ----------
        group : str
            Desired group name.

        Returns
        -------
        float
              Returns the maximum motion limit for the desired group in millimeters.
      
        '''
        return self.groupList[group].getMaxLimit()
    
    def setminLimit(self,group,val):
        '''
        Sets the minimum motion limit for the desired group in millimeters

        Parameters
        ----------
        group : str
            Desired group name.
        val : float
            Minimum actuator limit in millimeters.

        Returns
        -------
        None.

        '''
        self.groupList[group].setMinLimit(val)
    
    def setmaxLimit(self,group,val):
        '''
        Sets the maximum motion limit for the desired group in millimeters

        Parameters
        ----------
        group : str
            Desired group name.
        val : float
            Maximum actuator limit in millimeters.
        
        Returns
        -------
        None.
        
        '''
        self.groupList[group].setMaxLimit(val)
        
    def moveAbsolute(self,group,pos):
        '''
        Moves the desired actuator group to the position pos in millimeters
        
        If the new position is outside of the range of motion of the actuator it will not move

        Parameters
        ----------
        group : str
            Desired group name.
        pos : float
            Desired position to move to in millimeters.

        Returns
        -------
        bool
            Returns true if movement is finished.

        '''
        stageStatus = self.xps.get_group_status()[self.groupList[group].getGroup()]
        if stageStatus[:11].upper() == "Ready State".upper():
            if pos > self.getmaxLimit(group) or pos < self.getminLimit(group):
                print("Absolute Motion out of Bounds")
                return True
            else:
                self.xps.move_stage(self.groupList[group].getPos(),pos)
                return True
        else:
            print("Stage not ready to move")
            print(stageStatus)
            return True
        
    def moveRelative(self,group,pos):
        '''
        Moves the desired actuator group a distance pos relative to the current position in millimeters
        
        If the new position is outside of the range of motion of the actuator it will not move

        Parameters
        ----------
        group : str
            Desired group name.
        pos : float
            Desired relative distance to move actuator.

        Returns
        -------
        bool
            Returns true if movement is finished.

        '''
        stageStatus = self.xps.get_group_status()[self.groupList[group].getGroup()]
        if stageStatus[:11].upper() == "Ready State".upper():
            if float(self.getStagePosition(group)) + float(pos) > float(self.getmaxLimit(group)) or float(self.getStagePosition(group)) + float(pos) < float(self.getminLimit(group)):
                print("Relative Motion out of Bounds")
                return True
            else:    
                self.xps.move_stage(self.groupList[group].getPos(),pos,relative = True)
                return True
        else:
            print("Stage not ready to move")
            print(stageStatus)
            return True
            
    def initializeStage(self,group):
        '''
        Initializes the desired XPS group if in an initializable state.
        
        Will not initialize if the actuator has already been initialized
        
        Parameters
        ----------
        group : str
            Stage to initialize
        
        Returns
        -------
        None.
        
        '''
        stageStatus = self.xps.get_group_status()[self.groupList[group].getGroup()]
        if stageStatus == "Not initialized state" or stageStatus == "Not initialized state due to a GroupKill or KillAll command":
            try:
                self.xps.initialize_group(self.groupList[group].getGroup())
            except:
                print("XPS could not be initialized")
                pass
        else:
            print("XPS could not be initialized")
            print(stageStatus)
            
    def homeStage(self, group):
        '''
        Homes the desired XPS group if initialized but not homed
        
        Will not home if the actuator has already been homed
        
        Parameters
        ----------
        group : str
            Stage to home
            
        Returns
        -------
        None.
        
        '''
        stageStatus = self.xps.get_group_status()[self.groupList[group].getGroup()]
        if stageStatus == "Not referenced state":
            try:
                self.xps.home_group(self.groupList[group].getGroup())
            except:
                print("XPS could not be homed")
                pass
        else:
            print("XPS could not be homed")
            print(stageStatus)
            
    def enableGroup(self,group):
        '''
        Enables motion of an XPS group if in a disabled state
        
        Parameters
        ----------
        group : str
            Stage to enable.
            
        Returns
        -------
        None.
        '''
        stageStatus = self.xps.get_group_status()[self.groupList[group].getGroup()]
        if stageStatus == "Disabled state":
            try:
                self.xps.enable_group(self.groupList[group].getGroup())
            except:
                print("XPS could not be enabled")
                pass
        else:
            print("XPS could not be enabled")
            print(stageStatus)
        
    
    def disableGroup(self, group):
        '''
        Disables motion of an XPS group if in a disabled state
        
        Parameters
        ----------
        group : str
            Stage to disable.
            
        Returns
        -------
        None.
        '''
        stageStatus = self.xps.get_group_status()[self.groupList[group].getGroup()]
        if stageStatus[:11].upper() == "Ready state".upper():
            try:
                self.xps.disable_group(self.groupList[group].getGroup())
            except:
                print("XPS could not be disabled")
                pass
        else:
            print("XPS could not be disabled")
            print(stageStatus)
            
    def killAll(self, group):
        self.xps.kill_group(group)