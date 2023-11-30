# -*- coding: utf-8 -*-


import telnetlib
import time

class VironLaser():
    def __init__(self, host, port, password):
        '''
        Initializes the telnet communication with the Viron laser.
        The default IP Address as of June 21, 2023 is '192.168.103.103' with 
        port 23. The current password is VR6BE4EE.
        '''
        
        self.tn = telnetlib.Telnet(host,port)
        self.login(password)
    
    def send_command(self,command):
        self.tn.write(command.encode('ascii') + b'\r\n')
        time.sleep(0.5)
        return self.tn.read_very_eager().decode('utf-8')
    
    def set_stop(self):
        result = self.send_command('$STOP')
        print(result)
    
    def set_standby(self):
        result = self.send_command('$STANDBY')
        print(result)
        
    def set_fire(self):
        result = self.send_command('$FIRE')
        print(result)
    
    def get_status(self):
        status_full_return = self.send_command('$STATUS ?')

        print(status_full_return)
        [_, status, fault, warning] = status_full_return.split()
        
        output_length = 8 * ((len(status) + 1 ) // 2) # Byte length output i.e input A is printed as 00001010

        print(f'Status Binary: {int(status, 16):0{output_length}b}')
        print(f'Fault Binary: {int(fault, 16):0{output_length}b}')
        print(f'Warning Binary: {int(warning, 16):0{output_length}b}')
        
        laser_temp = float(self.send_command('$LTEMF ?').split()[1])
        print(f'Laser Temperature: {laser_temp:.2f}')
        try:
            diode_temp = float(self.send_command('$DTEMF ?').split()[1])
            print(f'Diode Temperature: {diode_temp:.2f}')
        except ValueError:
            print('Diode Temperature Control is Off')
        
    def login(self, password):
        result = self.send_command(f'$LOGIN {password}')
        print(result)
        
    def logout(self):
        result = self.send_command('$LOGOUT')
        print(result)  
        
    def close(self):
        self.set_stop()
        self.logout()
        self.tn.close()
        
if __name__ == '__main__':
    vl = VironLaser('192.168.103.103', 23, 'VR6BE4EE')
    time.sleep(1)
    vl.get_status()
    time.sleep(1)
    vl.close()