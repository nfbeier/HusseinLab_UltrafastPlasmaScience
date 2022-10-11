import time, serial
ser = serial.Serial(
        port = 'COM11', 
        baudrate = 115200, 
        timeout = 0.050
        )

class Motor:
    '''
    Contains methods of controlling direction and step delays of stepper motor.
    Attributes
    ----------
    mimim (int vector)
        Start stop limit.
    maxim (int vector)
        End stop limit.
    dir (bool vector)
        Direction to move motor in. 1 for forward and 0 for reverse.
    coord (float vector)
        Coordinate location of stage in mm.
    home (float vector)
        Coordinate location of home.
    '''

    def __init__(self, coord=[0.0, 0.0], home=[0.0, 0.0]):
        self.dir = [0, 0]
        self.min = [0.0, 0.0]
        self.max = [105.0, 105.0]
        self.coord = coord
        self.home = home

        # gpio pins
        self.gpio_dir = [13, 24]
        self.gpio_step = [19, 18]

    def get_dir(self):
        return self.dir

    def set_dir(self, dir, axis):
        '''
        Sets direction value and configures the motor to travel in set direction.
        Parameters
        ----------
        dir ([0,1]): Direction of travel. 1 indicates forward and 0 indicates reverse.
        axis ([0,1]): Axis being manipulated. 0 indicates x and 1 indicates y.
        '''
        self.dir[axis] = dir

        msg = str(self.gpio_dir[axis]) + str(dir).zfill(4)
        ser.write(msg.encode())

    def get_coord(self):
        return self.coord

    def set_coord(self, coord):
        self.coord = coord

    def get_home(self):
        return self.home
	
    def set_home(self, home_x, home_y):
        self.home = [home_x, home_y]

    def get_min(self):
        return self.min

    def set_min(self, minim):
        self.min = minim

    def get_max(self):
        return self.max

    def set_max(self, maxim):
        self.max = maxim

    def update_coord(self, dist, axis):
        '''
        Counts the number of steps taken from minumum to get location of stage.
        Parameters
        ----------
        dist ([0,1]): Direction of travel. 1 indicates forward and 0 indicates reverse.
        '''
        if self.dir[axis] == 0:  # If moving forward, add 1
            self.coord[axis] += dist
        else:
            self.coord[axis] -= dist
            
    def step_dist(self, inst, mm_dist, dir, axis):
        '''
        Takes a step of length mm_dist in direction dir.
        Parameters
        ----------
        inst: Instance of the Motor class.
        mm_dist (float): Distance in mm of the desired step.
        dir ([0,1]): Direction of travel. 0 indicates reverse and 1 indicates forward.
        axis ([0,1]): Axis being manipulated. 0 indicates x and 1 indicates y.
        '''
        inst.set_dir(dir, axis)
        msg = str(self.gpio_step[axis]) + str(mm_dist).zfill(4)  # Pad distance with zeros until it is of length 4
        ser.write(msg.encode())
        inst.update_coord(mm_dist, axis)

        ser.readline().decode("ascii")
             

class Control(Motor):
    def __init__(self):
        super().__init__()

    def left(self, inst, dist):
        '''
        Takes a step of length 1 mm left (reverse).
        Parameters
        ----------
        inst: Instance of the Motor class.
        dist: Distance of travel.
        '''
        super().step_dist(inst, dist, 0, 0)

    def right(self, inst, dist):
        '''
        Takes a step of length 1 mm right (forward).
        Parameters
        ----------
        inst: Instance of the Motor class.
        dist: Distance of travel.
        '''
        super().step_dist(inst, dist, 1, 0)

    def up(self, inst, dist):
        '''
        Takes a step of length 1 mm up (reverse).
        Parameters
        ----------
        inst: Instance of the Motor class.
        dist: Distance of travel.
        '''
        super().step_dist(inst, dist, 1, 1)

    def down(self, inst, dist):
        '''
        Takes a step of length 1 mm down (forward).
        Parameters
        ----------
        inst: Instance of the Motor class.
        dist: Distance of travel.
        '''
        super().step_dist(inst, dist, 0, 1)

    def return_home(self, inst):
        '''
        Calculates distance from the stage's current location to home. Then moves to home based on distance.
        Parameters
        ----------
        inst: Instance of the Motor class.
        '''
        coord = inst.get_coord()
        home = inst.get_home()
        dist = [abs(coord[0] - home[0]), abs(coord[1] - home[1])]  # number of mm steps needed to return home 
        dir_x = 0 if coord[0] < home[0] else 1
        super().step_dist(inst, dist[0], dir_x, 0)

        dir_y = 0 if coord[1] < home[1] else 1
        super().step_dist(inst, dist[1], dir_y, 1)