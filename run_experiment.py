import os
from multiprocessing import Process, Queue
import time
from ximea import xiapi
import numpy as np


def write_timestamp_queue(save_folder, q):
    '''
    Write queue to file to save timestamps, matching frame number to timestamp'''
    queue_savefile = os.path.join(save_folder,'timestamps.tsv')
    with open(queue_savefile, 'w') as f:
        f.write(f'collection\tframe_os\tos\tframe_od\tod\tframe_cy\tcy\n')
        while not q.empty():
            f.write(q.get())
            f.write('\n')
        f.close()
    return()
    
def write_sync_queue(save_folder, q):
    '''
    Write queue to file to save syncronizations'''    
    queue_savefile = os.path.join(save_folder,'timestamp_sync.tsv')
    with open(queue_savefile, 'w') as f:
        f.write('cam\tcam_time\twall_time\tdt\n')
        while not q.empty():
            f.write(q.get())
            f.write('\n')
        f.close()
    return()

def get_sync_string(cam_name, cam_handle):
    '''
    Clock camera and wall clocks together to ensure they match
    Params:
        cam_name (str): String name of camera (ie cam_od/cam_os/cam_cy
        cam_handle (XimeaCamera instance): camera handle to query time
    Returns:
        sync_string (str): string to write to file with cam name, time, and wall time
    '''
    t_wall_1 = time.monotonic()
    t_cam = cam_handle.get_param('timestamp')
    t_cam = t_cam/(1e9) #this is returned in nanoseconds, change to seconds
    t_wall_2 = time.monotonic()
    t_wall = np.mean((t_wall_1, t_wall_2)) #take middle of two wall times
    dt = t_cam - t_wall
    sync_string = f'{cam_name}\t{t_wall}\t{t_cam}\t{dt}'
    return(sync_string)
        

def run_queue_worker(q_in, save_folder):
    '''
    Start an infinite loop for a process that pops the oldest image from the queue and saves it to disk
    Params:
        q_in (queue): the queue to read from
        save_folder (str): name of the folder we write to 
    '''
    print('Saving Queue Started...')
    #while not queue.empty() & i>10:
    i=0
    while True:
        #pop a frame from the queue
        filename = os.path.join(save_folder, f'frame_{i}.bin')
        frame_data = q_in.get()
        with open(filename, 'wb') as f:
            f.write(frame_data)
            f.close()
        i+=1
        

        
def apply_cam_settings(cam, timing_mode=None, exposure=None, framerate=None,
                        gain=None, img_format=None, img_bpp=None,
                        auto_wb=None, transport_packing=None,
                        ):
        """
        Apply settings to the camera
        """

        #Exposure:
        if(exposure):
            cam.set_exposure(exposure)
        #Mode:
        if(timing_mode):
            cam.set_acq_timing_mode(timing_mode)
        #Framerate:
        if(framerate):
            cam.set_framerate(framerate)
        #Gain:
        if(gain):
            cam.set_gain(gain)
        #Format:
        if(img_format):
            cam.set_imgdataformat(img_format)
        #BPP Sensor:
        if(img_bpp):
            cam.set_imgdataformat(img_format)
        #White Blalance
        if auto_wb is not None:
            cam.set_param('auto_wb', 1)
            #cam.set_auto_wb(auto_wb)
        if transport_packing is not None:
            cam.set_imgdataformat('XI_RAW16')
            cam.set_param('output_data_bit_depth', 16) #12
            cam.enable_transport_packing()


def run_ximea_aquisition(save_folder, frame_rate, max_frames=10):    
    '''
    Aquire images from ximea cameras and save them.
    Parameters:
        save_folder (str): name of folder to save images
        frame_rate (int): how fast should we collect?
        max_frames (int): max number of frames to collect (mostly for testing)
    Returns:
        None
    ''' 
    
    #queues to save camera and timestamp data
    q_ts = Queue() #timestamps of frames
    q_sy = Queue() #timestamp sync
    q_od = Queue() #camera frames
    q_os = Queue() #caemra frames
    q_cy = Queue() #camera frames
    queue_list = [q_ts, q_sy, q_od, q_os, q_cy] #don't put buffer queues here, or we'll never stop!
    
    #camera_settings
    cam_timing_mode='XI_ACQ_TIMING_MODE_FREE_RUN'
    cam_image_format='XI_RAW8' #'XI_RAW16'
    cam_bpp = 12
    cam_framerate=frame_rate #200
    cam_exposure= np.int(np.around(1e6*(1.0/frame_rate))) #in microseconds
    print(f'Setting cam exposure to {cam_exposure/1000} ms')
    cam_gain=10
    
    #prep camera od
    cam_od_id = 'XECAS1922000'
    cam_od_folder = os.path.join(save_folder,'cam_od')
    if not os.path.exists(cam_od_folder):
        os.makedirs(cam_od_folder)
        
    #prep camera os
    cam_os_id = 'XECAS1922001'
    cam_os_folder = os.path.join(save_folder,'cam_os')
    if not os.path.exists(cam_os_folder):
        os.makedirs(cam_os_folder)
    
    #prep camera cy
    cam_cy_id = 'DUMMY_FOR_NOW'
    cam_cy_folder = os.path.join(save_folder,'cam_cy')
    if not os.path.exists(cam_cy_folder):
        os.makedirs(cam_cy_folder)
    
    try:
        #right camera (OD)
        cam_od = xiapi.Camera()
        cam_od.open_device_by_SN(cam_od_id)

        #left camera (OS)
        cam_os = xiapi.Camera()
        cam_os.open_device_by_SN(cam_os_id)

          #cyclopean camera (CY)
#         cam_cy = xiapi.Camera()
#         cam_cy.open_device_by_SN(cam_cy_id)

        #synchronize our watches! (match wall clock to camera timestamp)
        print('Recording Timestamp Syncronization Pre...')
        od_ss = get_sync_string('cam_od_pre', cam_od)
        os_ss = get_sync_string('cam_os_pre', cam_os)
        #cy_ss = get_sync_string('cam_cy_pre', cam_cy)
        cy_ss = os_ss #temporaray
        q_sy.put(od_ss)
        q_sy.put(os_ss)
        q_sy.put(cy_ss)

        #apply camera settings
        apply_cam_settings(cam_od,
                                             timing_mode=cam_timing_mode,
                                             exposure=cam_exposure,
                                             framerate=cam_framerate,
                                             gain=cam_gain,
                                             img_format=cam_image_format,
                                             img_bpp = cam_bpp)
        apply_cam_settings(cam_os,
                                             timing_mode=cam_timing_mode,
                                             exposure=cam_exposure,
                                             framerate=cam_framerate,
                                             gain=cam_gain,
                                             img_format=cam_image_format,
                                             img_bpp = cam_bpp)
#         cam_cy = apply_cam_settings(cam_cy,
#                                              timing_mode=None,
#                                              exposure=cam_exposure,
#                                              framerate=cam_framerate,
#                                              gain=cam_gain,
#                                              img_format=cam_image_format,
#                                              img_bpp = cam_bpp)

    
        #start our job saving threads
        os_save_thread = Process(target=run_queue_worker, args=(q_os, cam_os_folder))
        os_save_thread.daemon = True
        os_save_thread.start()      
        
        od_save_thread = Process(target=run_queue_worker, args=(q_od, cam_od_folder))
        od_save_thread.daemon = True
        od_save_thread.start()      
        
        cy_save_thread = Process(target=run_queue_worker, args=(q_cy, cam_cy_folder))
        cy_save_thread.daemon = True
        cy_save_thread.start()      
        
        #add all the job saving threads to the queue
        save_jobs = []
        save_jobs.append(os_save_thread)
        save_jobs.append(od_save_thread)
        save_jobs.append(cy_save_thread)
#         save_jobs.append(q_os)
#         save_jobs.append(q_od)
#         save_jobs.append(q_cy)
        
        #setup image handles and start aquisition
        cam_od_im = xiapi.Image()
        cam_od.start_acquisition()
        cam_os_im = xiapi.Image()
        cam_os.start_acquisition()
        #cam_cy_im = xiapi.Image()
        #cam_cy.start_acquisition()
     
        for i in range(max_frames):
            if(i%100==0):
                print('*',end='')
            
            #get images and timestamps
            cam_os.get_image(cam_os_im)
            cam_os_ts_s = cam_os_im.tsSec
            cam_os_ts_u = cam_os_im.tsUSec
            cam_os_fnum = cam_os_im.nframe
            
            cam_od.get_image(cam_od_im)
            cam_od_ts_s = cam_od_im.tsSec
            cam_od_ts_u = cam_od_im.tsUSec
            cam_od_fnum = cam_od_im.nframe
            
            #cam_cy.get_image(cam_cy_im)
            #cam_cy_ts_s = cam_cy_im.tsSec
            #cam_cy_ts_u = cam_cy_im.tsUSec
            #cam_cy_fnum = cam_od_im.nframe
            cam_cy_ts_s = cam_od_ts_s
            cam_cy_ts_u = cam_od_ts_u
            cam_cy_fnum = cam_od_im.nframe
        
            #pull image from cameras
            cam_od_data = cam_od_im.get_image_data_raw()
            cam_os_data = cam_os_im.get_image_data_raw()
            cam_cy_data = cam_os_data #for now use dummy data 
            
            #calcuate the exact timestamp we took the image, add to timestamp queue
            q_ts.put(f'{i}\t{cam_os_fnum}\t{cam_os_ts_s}.{cam_os_ts_u}\t' +
                            f'{cam_od_fnum}\t{cam_od_ts_s}.{cam_od_ts_u}\t' +
                            f'{cam_cy_fnum}\t{cam_cy_ts_s}.{cam_cy_ts_u}')
            # put cam data in camera frame queues
            q_od.put(cam_od_data)
            q_os.put(cam_os_data)
            q_cy.put(cam_cy_data)
            
            
        print(f'Sampled to max num frames of {max_frames}')
        print('Cleanly Stopping Device Aquisition and closing file.')
        
        #synchronize our watches! (match wall clock to camera timestamp)
        print('Recording Timestamp Syncronization Post...')
        od_ss = get_sync_string('cam_od_post', cam_od)
        os_ss = get_sync_string('cam_os_post', cam_os)
        #cy_ss = get_sync_string('cam_cy_post', cam_cy)
        cy_ss = os_ss #temporaray
        q_sy.put(od_ss)
        q_sy.put(os_ss)
        q_sy.put(cy_ss)
        print('Writing Queue of Timestamps...')
        write_sync_queue(save_folder, q_sy)
        
        #stop acquisition
        cam_od.stop_acquisition()
        cam_os.stop_acquisition()
        #cam_cy.stop_acquisition()
        #stop communication
        cam_od.close_device()
        cam_os.close_device()
        #cam_cy.close_device()
    
        
        #write queue timestamps
        print('Writing Queue of Timestamps...')
        write_timestamp_queue(save_folder, q_ts)
        
        #wait for all queues to be empty (all files saved)
        print('Waiting for save threads/queues to finish...')
        for qu in queue_list:
            while not qu.empty():
                pass
        
    except KeyboardInterrupt:
        print('Detected Keyboard Interrupt. Stopping Acquisition Cleanly')
        
        #synchronize our watches! (match wall clock to camera timestamp)
        print('Recording Timestamp Syncronization Post...')
        od_ss = get_sync_string('cam_od_post', cam_od)
        os_ss = get_sync_string('cam_os_post', cam_os)
        #cy_ss = get_sync_string('cam_cy_post', cam_cy)
        cy_ss = os_ss #temporaray
        q_sy.put(od_ss)
        q_sy.put(os_ss)
        q_sy.put(cy_ss)
        print('Writing Queue of Timestamps...')
        write_sync_queue(save_folder, q_sy)
        
        #stop acquisition
        cam_od.stop_acquisition()
        cam_os.stop_acquisition()
        #cam_cy.stop_acquisition()
        #stop communication
        cam_od.close_device()
        cam_os.close_device()
        #cam_cy.close_device()

        #write queue timestamps
        write_timestamp_queue(save_folder, q_ts)


    except Exception as e:
        print(e)
        print('There was an Error. Cleanly Stopping Device Aquisition and closing file.')
        
        #synchronize our watches! (match wall clock to camera timestamp)
        print('Recording Timestamp Syncronization Post...')
        od_ss = get_sync_string('cam_od_post', cam_od)
        os_ss = get_sync_string('cam_os_post', cam_os)
        #cy_ss = get_sync_string('cam_cy_post', cam_cy)
        cy_ss = os_ss #temporaray
        q_sy.put(od_ss)
        q_sy.put(os_ss)
        q_sy.put(cy_ss)
        print('Writing Queue of Timestamps...')
        write_sync_queue(save_folder, q_sy)
        
        #stop acquisition
        cam_od.stop_acquisition()
        cam_os.stop_acquisition()
        #cam_cy.stop_acquisition()
        #stop communication
        cam_od.close_device()
        cam_os.close_device()
        #cam_cy.close_device()

        #write queue timestamps
        write_timestamp_queue(save_folder, q_ts)

    print('Finished Ximea Aquisition.')

def run_pupillabs_aquisition(save_folder, frame_rate):
    '''
    Aquire eyetracking from pupil labs tracker and save it.
    Parameters:
        save_folder (str): name of folder to save images
        frame_rate (int): how fast should we collect?
    Returns:
        None
    '''
    time.sleep(5)
    print('Finished PupilLabs Aquisition.')

def run_realsense_aquisition(save_folder, frame_rate):
    '''
    Aquire IMU data from realsense trackers and save it.
    Parameters:
        save_folder (str): name of folder to save images
        frame_rate (int): how fast should we collect?
    Returns:
        None
    '''
    time.sleep(5)
    print('Finished Realsense Aquisition.')


def run_experiment(subject_name=None, task_name=None, exp_type=None, save_dir='./capture', max_frames=10):
    
    '''
    Run a data collection, either pre or post calibration, or an experiment.
    Params:
        subject (string): Subject ID to be included in file structure
        task_name (string): Name of task to be included in file structure
        exp_type (string): Type of experiment, either 'pre', 'post', or 'exp'
        save_dir (string): Name of base directly to save experiment files
        
    '''
    #test for valid input
    valid_experiments=['pre','post','exp']
    if(subject_name==None):
       raise ValueError("Please Specify a Subject ID!")
    
    if(exp_type not in valid_experiments):
       raise ValueError(f"Please Specify an experiment type: {valid_experiments}")
    
    #set parameters
    if(exp_type=='exp'):
        frame_rate = 200
        print('Running an experiment.')
    elif(exp_type=='pre'):
        frame_rate = 20
        print('Running a calibration.')
    
    print(f'Collecting at {frame_rate} fps.')
    
    #create directory structure for saving
    save_folder = os.path.join(save_dir, subject_name, task_name, exp_type)
    scene_cam_folder = os.path.join(save_folder,'scene_camera')
    eye_cam_folder = os.path.join(save_folder,'eye_camera')
    imu_folder = os.path.join(save_folder, 'imu')

    #start collection for eye tracker (pupil labs)
    eyetracker_thread = Process(target=run_pupillabs_aquisition, 
                                        args=(eye_cam_folder, frame_rate))
    eyetracker_thread.daemon = True  # Daemonize thread
    eyetracker_thread.start()        # Start the execution   
    print(f'Started eyetracking aquisition at {frame_rate}fps...')
    

    #start collection for IMUS (intel realsense)
    imu_thread = Process(target=run_realsense_aquisition, 
                                        args=(imu_folder, frame_rate))
    imu_thread.daemon = True  # Daemonize thread
    imu_thread.start()        # Start the execution   
    print(f'Started imu aquisition at {frame_rate}fps...')    
    
    
    #start collection for scene cameras (ximea)
    print(f'Starting scene aquisition at {frame_rate}fps...')
    run_ximea_aquisition(scene_cam_folder, frame_rate, max_frames=max_frames)
    
    
    return()


