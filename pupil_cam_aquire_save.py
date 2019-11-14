from time import time as t_time
from time import sleep
import zmq_socket as zmqs
import keyboard

def run_pupillabs_aquisition(save_folder, collection_mins, port=46173, component_name='PUPIL_CAM'):
    '''
    Aquire eyetracking from pupil labs tracker and save it.
    Parameters:
        save_folder (str): name of folder to save images
        collection_mins (int): how long should we collect?
    Returns:
        None
    '''
    
    #connect to already running pupil capture instance
    try:
        socket = zmqs.ZMQsocket(port=port)
        socket.connect()
    except:
        print(f'{component_name} Couldnt connect to Pupil Capture Instance. Check Pupil Capture is open and port matches.')
        
    # Sync time
    time_fn = t_time
    print(socket.set_time(time_fn))

    # Start the notifications puglin
    socket.notify({'subject': 'start_plugin', 'name': 'Annotation_Capture', 'args': {}})
    
    # Begin Recording
    print(f'{component_name} Beginning Recording for max {collection_mins} mins...')
    print(save_folder)
    socket.start_recording(dir_name=save_folder)
    
    #start our listener for recording events
    starttime = t_time()
    # keep listening until we've maxed out collection time
    while (t_time() - starttime) < 60*collection_mins:  
        if keyboard.is_pressed('s'):  # if key 's' is pressed 
            print('You Pressed s!')
            socket.annotation('start_trial', 0)
            sleep(1)
        if keyboard.is_pressed('e'):  # if key 'e' is pressed 
            print('You Pressed e!')
            socket.annotation('end_trial', 0)
            sleep(1)
        else:
            pass

    # Finish up
    socket.stop_recording()
    
    print(f'{component_name} Finished PupilLabs Aquisition.')
