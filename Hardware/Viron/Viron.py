# -*- coding: utf-8 -*-

import telnetlib
import time

class VironLaser():
    def __init__(self, host, port, password, telnetgui=None):
        '''
        Initializes the telnet communication with the Viron laser.
        
        Args:
        - host (str): The IP address of the Viron laser.
        - port (int): The port number for the telnet connection.
        - password (str): The password for the Viron laser.
        '''
        self.host = host
        self.port = port
        self.password = password
        self.tn = None
        self.params = None
        self.qs_delay = None
        self.tngui = telnetgui

    def connect_to_laser(self): 
        '''
        Connects to the Viron laser using telnet.
        
        Returns:
        - True if the connection is successful.
        - False if the connection is unsuccessful.
        '''
        try:  
            self.tn = telnetlib.Telnet(self.host, self.port, timeout=2)
        except ConnectionRefusedError:
            self.tngui_print("Error: Connection Refused (Viron is likely not on)")
        except TimeoutError:
            self.tngui_print("Error: Connection Timed Out")
        else:
            self.login(self.password)
            self.params = VironParameters(self)
            return True
        return False

    def send_command(self, command, response=False):
        '''
        Sends a command to the Viron laser and returns the response.
        
        Args:
        - command (str): The command to send to the Viron laser.
        
        Returns:
        - response (Bool): The response received from the Viron laser.
        
        '''
        if self.tn is not None:
            self.tn.write(command.encode('ascii') + b'\r\n')
            time.sleep(0.1)
            rtn = self.tn.read_very_eager().decode('utf-8')
            if "Bad Command" in rtn:
                self.tngui_print("Error, Bad Command")
                return False
            elif "Bad Value" in rtn:
                self.tngui_print("Error, Bad Value")
                return False
            elif "Out of Range" in rtn:
                self.tngui_print("Error, Out of Range")
                return False
            elif "Requires Login" in rtn:
                self.tngui_print("Error, Requires Login")
                return False
            elif "Not During Fire" in rtn:
                self.tngui_print("Error, Not During Fire")
                return False
            if response:
                return rtn
            else:
                return True
        else:
            self.tngui_print("Error, Telnet connection not established")
            return False
    
    def set_stop(self):
        '''
        Sends the stop command to the Viron laser.
        '''
        result = self.send_command('$STOP')
        return result
    
    def set_standby(self):
        '''
        Sends the standby command to the Viron laser.
        '''
        result = self.send_command('$STANDBY')
        return result
        
    def set_fire(self):
        '''
        Sends the fire command to the Viron laser.
        '''
        if self.send_command('$FIRE'):
            return True
        return False
        
    def set_rep_rate(self, rate):
        '''
        Sets the repetition rate of the Viron laser.
        
        Args:
        - rate (int): The desired repetition rate.
        '''
        rate = int(rate)
        self.tngui_print("Setting Rep Rate to: ", rate)
        if rate in range(1, 21): 
            result = self.send_command(f'$DFREQ {rate}')  # Set the repetition rate
            self.tngui_print(result)
        else:
            self.tngui_print('Invalid repetition rate')
    
    def get_temps(self):
        '''
        Retrieves the laser and diode temperatures from the Viron laser.
        
        Returns: 
        - temps (dict): A dictionary containing the laser and diode temperatures.
        '''
        
        temps = {'Laser Temp': 'N/A', 'Diode Temp': 'N/A'}
        
        
        # there's gotta be a more elegant way to do this. Oh well.
        rtn = False
        rtn = self.send_command('$LTEMF ?', response=True)
        if rtn:
            temps['Laser Temp'] =  float(rtn.split()[1])
            
        rtn = False
        rtn = self.send_command('$DTEMF ?', response=True)
        if rtn:
            if 'off' in rtn.lower():
                temps['Diode Temp'] = 'Off'
            else:
                temps['Diode Temp'] = float(rtn.split()[1])
        
        return temps
            
    def get_status(self):
        '''
        Retrieves and self.tngui_prints the status information of the Viron laser.
        
        Returns:
        - status_code (str): A string containing the binary representation of the status, fault, and warning codes.
        '''
        status_full_return = self.send_command('$STATUS ?', response=True)

        # self.tngui_print(status_full_return)
        try:
            [_, status, fault, warning] = status_full_return.split()
        except AttributeError:
            print("AttributeError on get_status()")
            return "000000000000000000000000"
        except ValueError:
            print("ValueError on get_status()")
            return "000000000000000000000000"
        output_length = 8 * ((len(status) + 1) // 2) # Byte length output i.e input A is self.tngui_printed as 00001010

        # self.tngui_print(f'Status Binary: {int(status, 16):0{output_length}b}')
        # self.tngui_print(f'Fault Binary: {int(fault, 16):0{output_length}b}')
        # self.tngui_print(f'Warning Binary: {int(warning, 16):0{output_length}b}')
        
        laser_temp = float(self.send_command('$LTEMF ?', response=True).split()[1])
        # self.tngui_print(f'Laser Temperature: {laser_temp:.2f}')
        try:
            diode_temp = float(self.send_command('$DTEMF ?', response=True).split()[1])
            # self.tngui_print(f'Diode Temperature: {diode_temp:.2f}')
        except ValueError:
            # self.tngui_print('Diode Temperature Control is Off')
            pass
        return str(status)+str(fault)+str(warning)
    
    def _set_alignment_mode(self):
        '''
        Sets the Viron laser to alignment mode.
        
        UNTESTED
        
        '''
        # decrease output energy by increasing qs delay (0-400 us)
        self.qs_delay = self.send_command('$QSDELAY ?', response=True)
        self.tngui_print(self.qs_delay)
        
        result = self.send_command('$QSDELAY 300')
        return result
    
    def set_alignment_mode(self):
        # Todo: rework
        return
    

        
    def set_qs_delay(self, delay):
        """
        Sets the QS Delay of the Viron laser.
        
        Inputs:
        - delay (int): The desired QS Delay in microseconds.
        Returns:
        - True if the QS Delay is set successfully.
        """
        if delay not in range(0, 179) or type(delay) != int:
            self.tngui_print("Invalid QSPRE")
            return False
        if self.send_command(f'$QSPRE {delay}'):
            return True
        return False
    

    def set_qs_pre(self, delay):
        """
        Sets the QS Delay of the Viron laser.
        
        Inputs:
        - delay (int): The desired QS Delay in microseconds.
        Returns:
        - True if the QS Delay is set successfully.
        """
        if delay not in range(0, 401) or type(delay) != int:
            self.tngui_print("Invalid QS Delay")
            return False
        if self.send_command(f'$QSDELAY {delay}'):
            return True
        return False
    
    def set_single_shot(self):
        """
        Sets the Viron laser to single shot mode.
        """
        # set trigger to internal on diode and QS
        if not self.send_command("$TRIG II"):
            return False
        # set QS to single shot
        if not self.send_command("$QSON 2"):
            return False
        return True
        
        
    def fire_single_shot(self):
        """
        Fires a single shot from the Viron laser.
        """
        if not self.send_command("$FIRE"):
            return False
        return True
    
    def login(self, password):
        '''
        Logs in to the Viron laser with the specified password.
        
        Args:
        - password (str): The password for the Viron laser.
        '''
        result = self.send_command(f'$LOGIN {password}')
        self.tngui_print(result)
        
    def logout(self):
        '''
        Logs out of the Viron laser.
        '''
        result = self.send_command('$LOGOUT')
        self.tngui_print(result)  
        
    def close(self):
        '''
        Stops the laser, logs out, and closes the telnet connection.
        '''
        result = False
        result = self.set_stop()
        result = self.logout()
        if self.tn is not None:
            result = self.tn.close()
        return result
    
    def tngui_print(self, message):
        if self.tngui is not None:
            self.tngui.print_to_terminal(message)
        print(message)
        
class VironParameters:
    def __init__(self, vironLaser):
        '''
        Initializes the VironParameters class.
        
        Args:
        - vironLaser (VironLaser): The VironLaser object to be used.
        '''
        self.vl = vironLaser
        self.dict = {}
        self.dict['Laser Temp'] = self.vl.send_command('$LTEMF ?', response=True)
        self.dict['Diode Temp'] = self.vl.send_command('$DTEMF ?', response=True)
        self.dict['QS Delay'] = self.vl.send_command('$QSDELAY ?', response=True)
        self.dict['DCURR'] = self.vl.send_command('$DCURR ?', response=True)
        self.dict['QSDIVBY'] = self.vl.send_command('$QSDIVBY ?', response=True)
        self.dict['MAXPRF'] = self.vl.send_command('$MAXPRF ?', response=True)
        self.dict["MINPRF"] = self.vl.send_command('$MINPRF ?', response=True)
        self.dict["TERM"] = self.vl.send_command('$TERM ?', response=True)
        self.dict["DPW"] = self.vl.send_command('$DPW ?', response=True)
        self.dict["MAXCURR"] = self.vl.send_command('$MAXCURR ?', response=True)
        self.dict["DCURR"] = self.vl.send_command('$DCURR ?', response=True)
        
    def get_params(self):
        return self.dict
    
if __name__ == '__main__':
    vl = VironLaser('192.168.103.103', 23, 'VR6BE4EE')
    time.sleep(1)
    vl.get_status()
    time.sleep(1)
    vl.close()
