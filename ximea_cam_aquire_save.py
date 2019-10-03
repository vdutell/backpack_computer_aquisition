import copy
import multiprocessing as mp
import time
import os as os
import numpy as np
from ximea import xiapi
from collections import namedtuple
import yaml
import mmap
import copy
import sys
import gc

import ctypes

frame_data = namedtuple("frame_data", "raw_data nframe tsSec tsUSec")

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

def get_cam_settings(cam, config_file):
    """
    Get the current settings of this camera, settings will be saved in
    alphabetical order, and have to be ordered correctly.
    
    If the config file already exists, ordering of keys remains the same
    and will only be updated.
    
    Params:
        camera (XimeaCamera instance): camera handle
        config_file (str): string filename of the config file for the camera
    """
    
    # if the config file already exists, pull the property names from that file
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            settings = yaml.load(f, Loader=yaml.UnsafeLoader)
        prop_names = list(settings.keys())
    
    # otherwise we have to grab them manually from the camera
    else:
        deny_list = ["api_progress_callback", "device_",
                    'list', 'ccMTX', '_file_name', "ffs_",
                    '_revision', "_profile", "number_devices", 
                    "hdr_", "lens_focus_move", 'manual_wb', "trigger_software"]
        prop_names = []
        for prop in dir(cam):
            if "get_" not in prop:
                continue

            prop = prop.replace("get_", "")

            if f"set_{prop}" not in dir(cam):
                continue

            if any([f in prop for f in deny_list]):
                continue
            
            prop_names.append(prop)
        
        for prop in dir(cam):
            if "enable_" not in prop:
                continue
            prop = prop.replace("enable_", '')
            
            if f"disable_{prop}" not in dir(cam):
                continue
            
            prop_names.append("is_" + prop)
    
    # go through the list of property names and attempt to get them
    # from the camera, if the camera gets grumpy, ignore it.
    cam_props = {}
    for prop in prop_names:
        if "is_" in prop:
            try:
                cam_props[prop] = cam.__getattribute__(prop)()
            except:
                pass
        else:
            try:
                cam_props[prop] = cam.__getattribute__(f"get_{prop}")()
            except:
                pass

    # take our collected properties and stuff them back into the config
    with open(config_file, 'w') as f:
        yaml.dump(cam_props, f, default_flow_style = False)
        

def apply_cam_settings(cam, config_file):
    """
    Apply settings to the camera from a config file.
    
    Params:
        camera (XimeaCamera instance): camera handle
        config_file (str): string filename of the config file for the camera
    """
    with open(config_file, 'r') as f:
        cam_props = yaml.load(f, Loader=yaml.UnsafeLoader)
        
    for prop, value in cam_props.items():
        if f"set_{prop}" in dir(cam):
            try:
                cam.__getattribute__(f"set_{prop}")(value)
            except Exception as e:
                print(e)
        elif prop in dir(cam) and "is_" in prop:
            en_dis = "enable_" if value else "disable_"
            try:
                cam.__getattribute__(f"{en_dis}{prop.replace('is_', '')}")()
            except Exception as e:
                print(e)
                                         
        else:
            print(f"Camera doesn't have a set_{prop}")
                
def save_queue_worker(cam_name, save_queue_out, save_folder, ims_per_file):
    
    #setup folder structure and file
    if not os.path.exists(os.path.join(save_folder, cam_name)):
        os.makedirs(os.path.join(save_folder, cam_name))
    ts_file_name = os.path.join(save_folder, f"timestamps_{cam_name}.tsv")
    #make a newtimestamp file
    with open(ts_file_name, 'w') as ts_file:
        ts_file.write(f"i\tnframe\ttime\n")
    #open it for appending
    ts_file = open(ts_file_name, 'a+')
    #ts_file = os.open(ts_file_name, os.O_WRONLY | os.O_CREAT , 0o777 | os.O_APPEND | os.O_SYNC | os.O_DIRECT)      
    i = 0
    grbgim = save_queue_out.get()
    #grbgim = save_pipe_out.recv()
    grbgim = grbgim.raw_data
    #imstr_array = bytearray(ims_per_file * grbgim) #empty byte string the size of image batches
    try:
        if(ims_per_file == 1):
            while True:
                bin_file_name = os.path.join(save_folder, cam_name, f'frame_{i}.bin')
                #f = os.open(bin_file_name, os.O_WRONLY | os.O_CREAT , 0o777 | os.O_TRUNC | os.O_SYNC | os.O_DIRECT)
                #image = save_queue_out.get()
                #image = save_pipe_out.recv()
                #os.write(f, image.raw_data)
                ts_file.write( f"{i}\t{image.nframe}\t{image.tsSec}.{str(image.tsUSec).zfill(6)}\n")
                #os.close(f)
                #del(image)
                i+=1
        else:
            while True:
                fstart=i*ims_per_file
                bin_file_name = os.path.join(save_folder, cam_name, f'frames_{fstart}_{fstart+ims_per_file-1}.bin')
                f = os.open(bin_file_name, os.O_WRONLY | os.O_CREAT , 0o777 | os.O_TRUNC | os.O_SYNC | os.O_DIRECT)
                for j in range(ims_per_file):
                    #image = save_pipe_out.recv()
                    image = save_queue_out.get()
                    os.write(f, image.raw_data)
                    ts_file.write( f"{fstart+j}\t{image.nframe}\t{image.tsSec}.{str(image.tsUSec).zfill(6)}\n")
                    del(image)
                    save_queue_out.task_done()
                os.close(f)
                gc.collect()
                i+=1
    except:
        print('Exiting Save Thread')

##TODO: Safely handle a keyboard interrupt by continuing to save data until the pipes are empty
#     except KeyboardInterrupt:
#         print(f'{component_name} Detected Keyboard Interrupt. Finishing Saving Before Stopping. Send another Interrupt to stop saving')

#     except:
#         print('There was an Error in the save Thread!')
#     finally:
#         os.close(f)
#         os.close(ts_file)


def acquire_camera(cam_id, cam_name, sync_queue_in, save_queue_in, max_collection_seconds,
                   component_name='SCENE_CAM'):
    
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
    
    try:
        
        print(f'{component_name} Opening Camera {cam_name}')
        camera = xiapi.Camera()
        camera.open_device_by_SN(cam_id)
        
        apply_cam_settings(camera, cam_name+".yaml")
        framerate = camera.__getattribute__(f"get_framerate")()
        max_frames = np.int(np.around(max_collection_seconds * framerate))
        
        print(f'{component_name} Recording Timestamp Syncronization Pre...')
        sync_str = get_sync_string(cam_name + "_pre", camera)
        #sync_pipe_in.send(sync_str)
        sync_queue_in.put(sync_str)

        camera.start_acquisition()
        image = xiapi.Image()
        
        for i in range(max_frames):
            camera.get_image(image)
            #print(data.size)
            #data = image.bp, bp_size
            #data = copy.deepcopy(image.bp)
            #data = (ctypes.c_uint*image.bp_size).from_address(image.bp)
            data = image.get_image_data_raw()
            #data = ctypes.create_string_buffer(image.bp, image.bp_size)
            #data = ctypes.cast(image.bp, ctypes.POINTER(ctypes.c_uint))
            d = frame_data(data,image.nframe,
                                image.tsSec,
                               image.tsUSec)
            #save_pipe_in.send(copy.deepcopy(d))
            save_queue_in.put(d)
            #del(data, d)
            #save_pipe_in.send(copy.deepcopy(d))
        print(f'{component_name} Reached {max_frames} frames collected. Exiting.')
        #save_pipe_in.close() #close the connection 
        save_queue_in.close() #close the connection 

        
    except KeyboardInterrupt:
        print(f'{component_name} Detected Keyboard Interrupt. Stopping Acquisition')
        sync_str = get_sync_string(cam_name + "_post", camera)
        sync_queue_in.send(sync_str)
        sync_queue_in.close()
        save_queue_in.close()
#         save_pipe_in.close() #close the connection#         
#         sync_pipe_in.send(sync_str)
#         sync_pipe_in.close()
#         save_pipe_in.close() #close the connection
        
    finally:
        print(f"{component_name} Camera {cam_name} Cleanup...")
        camera.stop_acquisition()
        camera.close_device()
    
        print(f"{component_name} Camera {cam_name} aquisition finished")
        

def ximea_acquire(save_folders_list, max_collection_mins=1, ims_per_file=100, component_name='SCENE_CAM', memsize=10):
    
    # 3 x save_queues
    # 3 x sync_queues
    
    cameras = {'od': "XECAS1922000"}
               #'os': "XECAS1922001"}
               #'cy': "XECAS1930001"}
            
    save_folders = [save_folders_list[0],
                    save_folders_list[1], # this line should be [0] when using 3 camears
                    save_folders_list[1]
                   ]
    
    #calculate queue size limit
    #limit our queue size so that we dont overflow memory.
    imsize_bits = 1544*2064
    queue_limt = int(memsize*1e9 // imsize_bits)
    
#     save_pipes = [mp.Pipe(duplex=False) for _ in cameras]
#     sync_pipes =  [mp.Pipe(duplex=False) for _ in cameras] 
    #sync_pipe_ins, sync_pipe_outs = *sync_pipes
    #save_pipe_ins, save_pipe_outs = *save_pipes
    save_queues = [mp.JoinableQueue() for _ in cameras]
    sync_queues = [mp.JoinableQueue() for _ in cameras]
    
    for save_folder in save_folders_list: 
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)
    
    #start save threads
    save_threads = []
    for i, cam in enumerate(cameras):
#         proc = mp.Process(target=save_queue_worker,
#                                        args=(cam,
#                                              save_pipes[i][0],
#                                              save_folders[i],
#                                              ims_per_file))
        proc = mp.Process(target=save_queue_worker, args=(cam,
                                             save_queues[i],
                                             save_folders[i],
                                             ims_per_file))
                                     
                                     
        proc.daemon = True
        proc.start()
        save_threads.append(proc)
    
    #start aquisition threads
    acquisition_threads = []
    for i, (cam_name, cam_sn) in enumerate(cameras.items()):
#         proc = mp.Process(target=acquire_camera,
#                           args=(cam_sn,
#                                 cam_name,
#                                 sync_pipes[i][1],
#                                 save_pipes[i][1],
#                                 max_collection_mins*60))
        proc = mp.Process(target=acquire_camera,
                          args=(cam_sn,
                                cam_name,
                                sync_queues[i],
                                save_queues[i],
                                max_collection_mins*60))
                                     
        proc.daemon = True
        acquisition_threads.append(proc)

        
    print(f"{component_name} Starting acquisition threads...")
    for proc in acquisition_threads:
        proc.start()

    print(f"{component_name} Aquiring Until Finished...")
    #every 10 seconds, garbage collect (for queue)
    gc_delay = 2
    for i in range(int(max_collection_mins*60//gc_delay)):
        time.sleep(gc_delay*2)
        gc.collect()
        q_size = [q.qsize() for q in save_queues]
        print(f'garbage collected! Queue size is {q_size}')
    
    for proc in acquisition_threads:
        proc.join()
    
    print(f"{component_name} Finished Aquiring. Waiting for Save Queues to Empty...")
    for q in save_queues:
        while not q.empty():
            time.sleep(1)
            gc.collect()
            q_size = [q.qsize() for q in save_queues]
            print(f'garbage collected! Queue size is {q_size}')
                                     
    
#     #sleep while we wait for collection, then wait until all pipes are empty
#     time.sleep(max_collection_mins*60)
#     for q in save_pipes:
#         while q[0].poll():
#             time.sleep(2)
    print(f"{component_name} Pipes are Empty.")
        
                                     
    print(f"{component_name} All Finished - Ending Process Now.")