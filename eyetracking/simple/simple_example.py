''' Demonstrates how to subscribe to and handle data from gaze and event streams '''

import time

import adhawkapi
import adhawkapi.frontend

import requests
# import pygame

last_blink = None
last_reading, last_reading_count = [], 0

# calibration
import subprocess, re, sys
from sys import platform

pos = [0, 0]
URL = "https://localhost:3001"

# BLACK = (0, 0, 0)
# WHITE = (200, 200, 200)

# # pygame setup
# pygame.init()
# infoObject = pygame.display.Info()
# WIDTH, HEIGHT = infoObject.current_w, infoObject.current_h
# screen = pygame.display.set_mode((WIDTH, HEIGHT))
# clock = pygame.time.Clock()
# running = True

def getActiveWindowSize():
    if platform == "linux" or platform == "linux2":
        # linux
        pass
    elif platform == "darwin":
        # OS X
        output = subprocess.run(['osascript', 'eyetracking/simple/activeWindowDimMac.scpt'], capture_output=True)
        l, w, x, y = [int(x) for x in re.findall(r'\d+', output.stdout.decode('utf-8'))]
        return [l, w, x, y]
        
    elif platform == "win32":
        # Windows...
        pass

def checkInRange():
    size = getActiveWindowSize()

class FrontendData:
    ''' BLE Frontend '''


    def __init__(self):
        # Instantiate an API object
        # TODO: Update the device name to match your device
        self._api = adhawkapi.frontend.FrontendApi(ble_device_name='ADHAWK MINDLINK-294')

        

        # Tell the api that we wish to receive eye tracking data stream
        # with self._handle_et_data as the handler
        self._api.register_stream_handler(adhawkapi.PacketType.EYETRACKING_STREAM, self._handle_et_data)

        # Tell the api that we wish to tap into the EVENTS stream
        # with self._handle_events as the handler
        self._api.register_stream_handler(adhawkapi.PacketType.EVENTS, self._handle_events)

        # Start the api and set its connection callback to self._handle_tracker_connect/disconnect.
        # When the api detects a connection to a MindLink, this function will be run.
        self._api.start(tracker_connect_cb=self._handle_tracker_connect,
                        tracker_disconnect_cb=self._handle_tracker_disconnect)

    def shutdown(self):
        '''Shutdown the api and terminate the bluetooth connection'''
        self._api.shutdown()

    @staticmethod
    def _handle_et_data(et_data: adhawkapi.EyeTrackingStreamData):
        ''' Handles the latest et data '''
        if et_data.gaze is not None:
            xvec, yvec, zvec, vergence = et_data.gaze
            gazed(et_data.gaze)
            # print(f'Gaze={xvec:.2f},y={yvec:.2f},z={zvec:.2f},vergence={vergence:.2f}')

        if et_data.eye_center is not None:
            if et_data.eye_mask == adhawkapi.EyeMask.BINOCULAR:
                rxvec, ryvec, rzvec, lxvec, lyvec, lzvec = et_data.eye_center
                # print(f'Eye center: Left=(x={lxvec:.2f},y={lyvec:.2f},z={lzvec:.2f}) '
                #       f'Right=(x={rxvec:.2f},y={ryvec:.2f},z={rzvec:.2f})')

        if et_data.pupil_diameter is not None:
            if et_data.eye_mask == adhawkapi.EyeMask.BINOCULAR:
                rdiameter, ldiameter = et_data.pupil_diameter
                # print(f'Pupil diameter: Left={ldiameter:.2f} Right={rdiameter:.2f}')

        if et_data.imu_quaternion is not None:
            if et_data.eye_mask == adhawkapi.EyeMask.BINOCULAR:
                x, y, z, w = et_data.imu_quaternion
                # print(f'IMU: x={x:.2f},y={y:.2f},z={z:.2f},w={w:.2f}')

    @staticmethod
    def _handle_events(event_type, timestamp, *args):

        if event_type == adhawkapi.Events.BLINK:
            duration = args[0]
            blinked(timestamp)
            # print(f'Got blink: {timestamp} {duration}')
        if event_type == adhawkapi.Events.EYE_CLOSED:
            eye_idx = args[0]
            # print(f'Eye Close: {timestamp} {eye_idx}')
        if event_type == adhawkapi.Events.EYE_OPENED:
            eye_idx = args[0]
            # print(f'Eye Open: {timestamp} {eye_idx}')

    def _handle_tracker_connect(self):
        print("Tracker connected")
        self._api.set_et_stream_rate(60, callback=lambda *args: None)

        self._api.set_et_stream_control([
            adhawkapi.EyeTrackingStreamTypes.GAZE,
            adhawkapi.EyeTrackingStreamTypes.EYE_CENTER,
            adhawkapi.EyeTrackingStreamTypes.PUPIL_DIAMETER,
            adhawkapi.EyeTrackingStreamTypes.IMU_QUATERNION,
        ], True, callback=lambda *args: None)

        self._api.set_event_control(adhawkapi.EventControlBit.BLINK, 1, callback=lambda *args: None)
        self._api.set_event_control(adhawkapi.EventControlBit.EYE_CLOSE_OPEN, 1, callback=lambda *args: None)

    def _handle_tracker_disconnect(self):
        print("Tracker disconnected")

def blinked(timestamp):
    global last_blink
    DBL_BLINK_TIME = 1.5
    # print(timestamp - last_blink)
    if last_blink is not None and timestamp - last_blink < DBL_BLINK_TIME:
        x = requests.post(URL, json = {pos: pos})
        print(x['success_message'])
    last_blink = timestamp

def gazed(gaze_data):
    global last_reading, last_reading_count
    TOLERANCES, MIN_FOCUS_COUNT = [0.015, 0.015, 0.015], 50
    if last_reading != []:
        if all([last_reading[i] - gaze_data[i] < TOLERANCES[i] for i in range(2)]):
            last_reading_count += 1
        else:
            last_reading_count = 0
        # if last_reading_count >= MIN_FOCUS_COUNT:
            # focused
            # print('locked')
        # else:
            # print('reading')
        # print(gaze_data)
    
    last_reading = gaze_data

# def calibration_texts():
#     global WIDTH, HEIGHT
#     font = pygame.font.Font('freesansbold.ttf', 32)
 
#     text = font.render('Stare at the centre and click the button', True, '#ffffff', '#000000')
#     textRect = text.get_rect()
    
#     # set the center of the rectangular object.
#     textRect.center = (WIDTH // 2, HEIGHT // 2)
#     return text, textRect

# def convertPos(relative_x, relative_y, marked_pos):
#     padding = 70
#     tl, tr, bl, br = marked_pos
#     x = (relative_x / (br[0] - bl[0])) * 1372 # (WIDTH - 3 * padding)
#     y = (relative_y / (br[1] - tr[1])) * (HEIGHT - 3 * padding)
#     return x, y
    


def main():
    ''' App entrypoint '''
    frontend = FrontendData()
    # calibrated = False
    # last_five = []
    # while True:
    # #     # poll for events
    # #     # pygame.QUIT event means the user clicked X to close your window
    # #     for event in pygame.event.get():
    # #         if event.type == pygame.QUIT:
    # #             running = False

    # #     # fill the screen with a color to wipe away anything from last frame
    # #     screen.fill('#000000')
    # #     if not calibrated:
    # #         circle = pygame.draw.circle(screen, (255, 0, 0),
    # #             [WIDTH//2, HEIGHT//2], 10)
        
    # #     # show the text and dots in order
    # #     text, textRect = calibration_texts()
    # #     screen.blit(text, textRect)
    # #     if not calibrated:
    # #         mouse_pos = pygame.mouse.get_pos()
    # #         mouse_pressed = pygame.mouse.get_pressed()[0]
    # #         # print(mouse_pos, positions[i])
    # #         if circle.collidepoint(mouse_pos) and mouse_pressed:
    # #             print("clicked")
    # #             base_pos = last_reading
        
    # #     if calibrated:
            
    # #         pygame.draw.rect(screen, (0,255,0), )

    
    # #     # flip() the display to put your work on screen
    # #     pygame.display.flip()

    # #     clock.tick(60)  # limits FPS to 60
    #     last_five.append(last_reading)
    #     if len(last_five) > 0:
    #         last_five.pop(0)
    #     print(last_reading)
        
    #     time.sleep(1)
    # pygame.display.quit()
    # # pygame.quit()
    # print("calibration successful")
    
    try:
        base = None
        c = 0
        while True:
            if not base and last_reading is not None and c < 5:
                base = last_reading
            if last_reading[1] > base[1] + 0.75:
                pos[1] = 1
            elif last_reading[1] < base[1] - 0.75:
                pos[1] = -1
            else:
                pos[1] = 0
            if last_reading[0] > base[0] + 1:
                print(last_reading[0], base[0])
                pos[0] = 1
            elif last_reading[0] < base[0] - 1:
                print(last_reading[0], base[0])
                pos[0] = -1
            else:
                pos[0] = 0
            print(pos)
            time.sleep(1)
            c += 1
    except (KeyboardInterrupt, SystemExit):
        frontend.shutdown()
if __name__ == '__main__': 
    main()
    pass
