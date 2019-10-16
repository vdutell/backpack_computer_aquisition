from time import sleep, time
import pupil.pupil_src as pup_start
import zmq_socket as zmqs

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
    time_fn = time
    print(socket.set_time(time_fn))

    # Start the notifications puglin
    socket.notify({'subject': 'start_plugin', 'name': 'Annotation_Capture', 'args': {}})
    
    # Begin Recording
    print(f'{component_name} Beginning Recording for max {collection_mins} mins...')
    socket.start_recording(dir_name=save_folder)
    
    # Start Trial
    socket.annotation('start_trial', 0)

    # Continue Recording until we've reached the maximum collection minutes
    sleep(collection_mins*60)
    
    # End Trial
    socket.annotation('end_trial', 0)

    # Finish up
    socket.stop_recording()
    
    print(f'{component_name} Finished PupilLabs Aquisition.')
