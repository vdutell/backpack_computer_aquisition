import copy
import multiprocessing as mp
import time
import os
import numpy as np
from ximea import xiapi
from collections import namedtuple
import io
import mmap

frame_data = namedtuple("frame_data", "raw_data nframe tsSec tsUSec")

default_settings = {"timing_mode": "XI_ACQ_TIMING_MODE_FREE_RUN", #"XI_ACQ_TIMING_MODE_FRAME_RATE_LIMIT"
                    "img_format": "XI_RAW8",
                    'framerate': None,
                    'gain': 10,
                    'transport_packing': False,
                    'sensor_bit_depth': "XI_BPP_8",
                    'output_bit_depth': "XI_BPP_8",
                    'buffer_policy': "XI_BP_SAFE",
                    'bandwidth_limit': None,
                    'buffer_queue_size': None, #16                
                    'acq_buffer_size': None
                   }

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


def apply_cam_settings(cam, timing_mode=None, exposure=None, framerate=None,
                        gain=None, img_format=None,
                        auto_wb=None, transport_packing=None,
                        sensor_bit_depth=None,
                        output_bit_depth=None,
                        bandwidth_limit=None,
                        report_settings=True,
                        buffer_policy=None,
                        acq_buffer_size=None,
                        buffer_queue_size = None,
                        acq_transport_buffer_size=None
                        ):
    """
    Apply settings to the camera
    """
    
    #first reset settings
    cam.get_device_reset()
    
    
    if framerate is not None:
        #print(f'Setting framerate to {framerate}'
        #cam.set_param('framerate_limit', framerate)
        cam.set_framerate(framerate)
    if exposure is not None:
        #print(f'Setting Exposure to {exposure}')
        cam.set_exposure(exposure)
    if timing_mode is not None:
        #print(f'Setting Timing Mode to {timing_mode}')
        cam.set_acq_timing_mode(timing_mode)
    if gain is not None:
        #print(f'Setting gain to {gain}')
        cam.set_gain(gain)
    if img_format is not None:
        #print(f'Setting img_format to {img_format}')
        cam.set_imgdataformat(img_format)
    if sensor_bit_depth is not None:
        #print(f'Setting sensor bit depth to {sensor_bit_depth}')
        cam.set_param('sensor_bit_depth', output_bit_depth)
    if output_bit_depth is not None:
        #print(f'Setting output bit depth to {sensor_bit_depth}')
        cam.set_param('output_bit_depth', output_bit_depth)
    if auto_wb is not None:
        #print(f'Setting auto_wb to {auto_wb}')
        cam.set_param('auto_wb', 1)
    # NOTE: Transport Packing overrides bit depth and image format settings
    if transport_packing is not None:
        #print(f'Setting transport_packing to {transport_packing}')
        if(transport_packing==True):
            cam.set_imgdataformat('XI_RAW16')
            cam.set_param('output_bit_depth', 'XI_BPP_10')
            cam.enable_output_bit_packing()
            
    if bandwidth_limit is not None:
        print(f'Limiting bandwidth to {bandwidth_limit}')
        cam.set_param('limit_bandwidth_mode', "XI_ON")
        cam.set_param('limit_bandwidth', bandwidth_limit)
#         cam.set_limit_bandwidth(bandwidth_limit)

    ### BUFFER STUFF
    if buffer_policy is not None:
        cam.set_param('buffer_policy', buffer_policy)
    if buffer_queue_size is not None:
        cam.set_param('buffers_queue_size', buffer_queue_size)
    if acq_buffer_size is not None:
        cam.set_param('acq_buffer_size', acq_buffer_size)
#     if acq_transport_buffer_size is not None:
#         cam.set_param('transport_buffer_size', acq_transport_buffer_size)

        
    if(report_settings):
        #exposure time
        print(f'Exposure is set to {cam.get_exposure()/1000} ms')
        # timing mode
        print(f'Timing Mode is set to {cam.get_acq_timing_mode()}')
        # max framerate
        print(f'Max Framerate is set to {cam.get_framerate()}')
        # gain
        print(f'Gain is set to {cam.get_gain()}')
        # img data format
        print(f'Image Data Format is set to {cam.get_imgdataformat()}')
        # white balance
        wb = cam.get_param('auto_wb')
        print(f'Auto Whtie Balance is set to {wb}')
        # auto exposure gain
        print(f'AutoExpostureGain is set to {cam.is_aeag()}')
        # bit detph
        sbd = cam.get_param('sensor_bit_depth')
        obd = cam.get_param('output_bit_depth')
        print(f'Bit Depth is set to {sbd}(sensor),{obd}(output)')
        # im size
        print(f'Im Size is set to {cam.get_width()},{cam.get_height()}')
        # bandwidth
        bw = cam.get_param('limit_bandwidth')
        print(f'Bandwidth limit is set to {bw}')
        # buffer size
        print(f'Acq Buffer Size is set to {cam.get_acq_buffer_size()}')
        #print(f'Trans Buffer Size is set to {cam.get_acq_transport_buffer_size()}')
        print(f'Buffer Policy is {cam.get_buffer_policy()}')
        print(f'Buffer Queue Size is {cam.get_buffers_queue_size()}')
    return(cam)
        
def save_queue_worker(cam_name, save_queue, save_folder, ims_per_file):
    
    #setup folder structure and file
    if not os.path.exists(os.path.join(save_folder, cam_name)):
        os.makedirs(os.path.join(save_folder, cam_name))
    ts_file_name = os.path.join(save_folder, f"timestamps_{cam_name}.tsv")
    with open(ts_file_name, 'w') as timestamp_file:
        timestamp_file.write(f"i\tnframe\ttime\n")
        
    i = 0
    grbgim = save_queue.get().raw_data
    imlen = len(grbgim)
    
    try:
        while True:        
            bin_filename = os.path.join(save_folder,
                                        cam_name,
                                        f'frame_{i}.bin')
            f = os.open(bin_filename, os.O_CREAT|os.O_TRUNC|os.O_WRONLY|os.O_SYNC)

            image = save_queue.get()
            os.write(f, image.raw_data)

            tsstr_list = f"{i}\t{image.nframe}\t{image.tsSec}.{str(image.tsUSec).zfill(6)}\n"

            with open(ts_file_name, 'a+') as ts_file:
                ts_file.write(tsstr_list)
            os.close(f)

            i+=1
    
    except KeyboardInterrupt:
        print('Detected Keyboard Interrupt. Not saving anymore....')
              

def acquire_camera(cam_id, cam_name, sync_queue, save_queue, max_collection_seconds, **settings):
    """
    Acquire frames from a single camera.
    
    Parameters:
        cam_id (str):  The serial number of the camera
        cam_name (str): A text name for the camera
        sync_queue (Multithreading.Queue): A queue which accepts the sync strings
        save_queue (Mutlithreading.Queue): A queue which accepts xiapi.Images
        max_collection_seconds (int): the maximum number of seconds to run
        
        Any keywords which are present in default_settings may also be passed as 
        keyword arguments to this function as well.
        IE:
            acquire_camera("some_id",
                           "a camera",
                           Q,
                           Q2,
                           10,
                           timing_mode=None,
                           framerate=None, ...)
   
    """  
    
    s = copy.deepcopy(default_settings)
    s.update(settings)
    settings = s
    
    #cyclopean camera captures fast, binocular cameras capture slower
    if(cam_name=='cy'):
        settings['bandwidth_limit'] = 1200
        settings['framerate'] = 200
        doffset_framerate = 20
    else:
        settings['bandwidth_limit'] = 600
        settings['framerate'] = 100
        doffset_framerate = 25
        
    #set exposure in relation to framerate
    settings['exposure'] = np.int(np.around(1e6*(1.0/settings['framerate'])))-doffset_framerate
    exp_time = (settings['exposure'] / 1000)
    
    max_frames = max_collection_seconds * settings['framerate']
    
    try:
        camera = xiapi.Camera()
        camera.open_device_by_SN(cam_id)
        
        print('Recording Timestamp Syncronization Pre...')
        sync_str = get_sync_string(cam_name + "_pre", camera)
        sync_queue.put(sync_str)
        
        camera = apply_cam_settings(camera, **settings)
        
        camera.start_acquisition()
        
        image = xiapi.Image()
        print(f'Recording for {max_frames} frames total...')
        for _ in range(max_frames):
            camera.get_image(image)
            save_queue.put(frame_data(image.get_image_data_raw(),
                                      image.nframe,
                                      image.tsSec,
                                      image.tsUSec))
        print(f'Reached {max_frames} frames collected. Exiting.')
        
    except KeyboardInterrupt:
        print('Detected Keyboard Interrupt. Stopping Acquisition')
        sync_str = get_sync_string(cam_name + "_post", camera)
        sync_queue.put(sync_str)
        
    finally:
        print(f"Camera {cam_name} Cleanup...")
        camera.stop_acquisition()
        camera.close_device()
    
        print(f"Camera {cam_name} aquisition finished")
        

def ximea_acquire(save_folder_list, max_collection_time=5000, ims_per_file=100, **settings):
    
    # 3 x save_queues
    # 3 x sync_queues
    
    cameras = {'od': "XECAS1922000"}
               #'os': "XECAS1922001"}
               #'cy': "XECAS1930001"}
    
    save_folders = [save_folder_list[0],
                    save_folder_list[0],
                    save_folder_list[1]
                   ]
    
    save_queues = [mp.Queue() for _ in cameras]
    sync_queues = [mp.Queue() for _ in cameras]
    
    #make folders we'll need
    for save_folder in save_folder_list: 
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)

    #start save threads
    save_threads = []
    for i, cam in enumerate(cameras):
        proc = mp.Process(target=save_queue_worker,
                                       args=(cam,
                                             save_queues[i],
                                             save_folders[i],
                                             ims_per_file))
        proc.daemon = True
        proc.start()
        save_threads.append(proc)
    
    #start aquisition threads
    acquisition_threads = []
    for i, (cam_name, cam_sn) in enumerate(cameras.items()):
        proc = mp.Process(target=acquire_camera,
                          args=(cam_sn,
                                cam_name,
                                sync_queues[i],
                                save_queues[i],
                                max_collection_time),
                          kwargs=settings)
        acquisition_threads.append(proc)
        proc.daemon = True
    
    print("Starting acquisition threads...")
    for proc in acquisition_threads:
        proc.start()

    print("Aquiring Until Finished...")
    for proc in acquisition_threads:
        proc.join()
    
    print("Finished Aquiring. Waiting for Save Queues to Empty...")
    for q in save_queues:
        while not q.empty():
            time.sleep(1)
    print("All Done!")