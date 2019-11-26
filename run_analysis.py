import os
import numpy as np
import cv2
from multiprocessing import Process
import re
import matplotlib.pyplot as plt

def convert_bin_png(filename, save_folder_list, im_shape=(1544,2064), img_format='XI_RAW8'):
    '''
    Take a file saved in .bin format from a ximea camera, and convert it to a png image.
    Parameters:
        filename (str): file to be converted
        save_folder (str): folder to save png files
        im_shape (2pule ints): shape of image
        img_format (str): Image format files are saved
    Returns:
        None
    '''
    
    fname, _ = os.path.splitext(os.path.basename(filename))
    save_filepath = os.path.join(save_folder, fname + '.png')
    binary_img = []
    
    if(img_format=='XI_RAW16'):
        with open(filename, 'rb') as f:
            bs = f.read(2)
            while(bs):
                #for raw_16 img is large and small bytes alternating
                bs = f.read(1)
                bs_b = f.read(1)
                byte = int.from_bytes(bs,'big')
                byte_big = int.from_bytes(bs_b,'big')
                #print(256*byte_big+byte)
                binary_img.append((256*byte_big+byte))
            f.close()
    
        im = np.array(binary_img).reshape(im_shape)
        im = cv2.cvtColor(np.uint16(im), cv2.COLOR_BayerGR2RGB)
        im = im.astype(np.uint16)
        
    elif(img_format=='XI_RAW8'):
        with open(filename, 'rb') as f:
            bs = f.read(1)
            while(bs):
                bs = f.read(1)
                bs = int.from_bytes(bs,'big')
                binary_img.append(bs)
            f.close()
        im = np.array(binary_img).reshape(im_shape)
        im = cv2.cvtColor(np.uint8(im), cv2.COLOR_BayerGR2RGB)
        im = im.astype(np.uint8)
        
    cv2.imwrite(save_filepath, im)
    print('*',end='')
    
    return()


def bin_to_im(binfile, nframe, dims=(1544,2064)):
    '''
    convert a single image from 8-bit raw bytes to png image.
    Input:
        binfile (str): path to binary file
        dims (2ple int): What are the dimensions of the iamge?
        nframe (int): Which frame number do we want within image?
        '''
    a = []
    # for uint8
    nbytes = np.prod(dims)
    startbyte = nframe*nbytes
    with open(binfile, 'rb') as fn:
        fn.seek(startbyte)
        bs = fn.read(1)
        for i in range(nbytes):
            bs = fn.read(1)
            bs = int.from_bytes(bs,'big')
            a.append(bs)
            
    a = np.array(a)
    im = a.reshape(dims)
    imc = cv2.cvtColor(np.uint8(im), cv2.COLOR_BayerGR2RGB)
    
    return(imc)

def convert_folder(read_folder, write_folder):
    '''
    Convert a folder of raw .bin files to .pngs
    Params:
        read_folder (str): where are .bin files stored?
        write_folder (str): where should we write the pngs to?
    '''
    #loop through files in folder
    for f in os.listdir(read_folder):
        if f.endswith(".bin"):
            convert_bin_png(os.path.join(read_folder,f), write_folder)
            
def calc_timestamp_stats(timestamp_file, write_folder):
    '''
      Figure out how well we did with timing in terms of capturing images
      Params:
          timestamp_file (str): tsv file holding timestamp data
          write_folder (str): folder to store output stats
    '''
    with open(timestamp_file, 'r') as f:
        ts_table=list(zip(line.strip().split('\t') for line in f))
#        print(ts_table)
#         line = f.readline() #column headers
#         while(line):
#             line = f.readline()
#             print(line)
#             frame, os, od = [re.split(line.strip(), '\t')]
#             print(frame, os, od)
        f.close()
    
    ts_table = np.squeeze(np.array(ts_table[1:]).astype('float'))
    #calculate dts between frames
    lr_camera_dcaps = np.abs(ts_table[:,1] - ts_table[:,2])
    os_dts = ts_table[1:,2] - ts_table[:-1,2]
    od_dts = ts_table[1:,4] - ts_table[:-1,4]
    cy_dts = ts_table[1:,6] - ts_table[:-1,6]
    #calculate frame skips
    os_skips = (ts_table[1:,1] - ts_table[:-1,1]) - 1
    od_skips = (ts_table[1:,3] - ts_table[:-1,3]) - 1
    cy_skips = (ts_table[1:,5] - ts_table[:-1,5]) - 1
    
    print(f'Mean camera time disparity: {np.mean(lr_camera_dcaps):.4f} seconds')
    print(f'Mean OS dts: {np.mean(os_dts):.4f} seconds')
    print(f'Mean OD dts: {np.mean(od_dts):.4f} seconds')
    print(f'Mean CY dts: {np.mean(cy_dts):.4f} seconds')    
    
    print(f'Mean OS skips: {np.mean(os_skips):.2f} frames')
    print(f'Mean OD skips: {np.mean(od_skips):.2f} frames')
    print(f'Mean CY skips: {np.mean(cy_skips):.2f} frames')   
    
    plt.hist(os_dts, label = 'OS dt', alpha=0.6, bins=30);
    plt.hist(od_dts, label = 'OD dt', alpha=0.6, bins=30);
    plt.hist(cy_dts, label = 'CY dt', alpha=0.6, bins=30);
    plt.axvline(1/200, label='200fps')
    plt.legend()
    plt.ylabel('Seconds')
    plt.title('Within CameraTiming Disparity for World Camera')
    plt.savefig(os.path.join(write_folder,'timestamp_stats_within_cam.png'))
    plt.show()
   
    plt.hist(lr_camera_dcaps, label = 'OD/OS Disparity', alpha=0.6, bins=30);
    plt.legend()
    plt.ylabel('Seconds')
    plt.title('Between Camera Timing Disparity for World Camera')
    plt.savefig(os.path.join(write_folder,'timestamp_stats_between_cam.png'))
    plt.show()
    
    plt.plot(os_dts,label='OS dt')
    plt.plot(od_dts,label='OD dt')
    plt.plot(cy_dts,label='CY dt')
    plt.axhline(1/200, label='200fps')
    plt.xlabel('frame number')
    plt.ylabel('DT')
    plt.legend()
    plt.title('DT Over Collection')
    plt.savefig(os.path.join(write_folder,'dt_over_collection.png'))
    plt.show()
    
    plt.plot(os_skips,label='OS skips')
    plt.plot(od_skips,label='OD skips')
    plt.plot(cy_skips,label='CY skips')
    plt.axhline(0, label='Zero')
    plt.xlabel('capture number')
    plt.ylabel('Skipped Frames')
    plt.legend()
    plt.title('Skipped Frames Over Collection')
    plt.savefig(os.path.join(write_folder,'skipped_frames_over_collection.png'))
    plt.show()
    
def run_ximea_analysis(capture_folder, analysis_folder, timestamp_stats=True, convert_ims=True):
    '''
    Analyze video data, including converting .bin files to png files.
    '''

    try:
        
        #calcuate stats on frame capture
        if(timestamp_stats):
            calc_timestamp_stats(os.path.join(capture_folder,'timestamps.tsv'),
                                analysis_folder)
        
        if(convert_ims):
 
            #OD
            od_cap_folder = os.path.join(capture_folder,'cam_od')
            od_ana_folder = os.path.join(analysis_folder,'cam_od')
            if not os.path.exists(od_ana_folder):
                os.makedirs(od_ana_folder)    
            #convert_folder(od_cap_folder, od_ana_folder)
            od_save_thread = Process(target=convert_folder, args=(od_cap_folder, od_ana_folder))
            od_save_thread.daemon = True
            od_save_thread.start()  
            
            #OS
            os_cap_folder = os.path.join(capture_folder,'cam_os')
            os_ana_folder = os.path.join(analysis_folder,'cam_os')
            if not os.path.exists(os_ana_folder):
                os.makedirs(os_ana_folder)
            #convert_folder(os_cap_folder, os_ana_folder)
            os_save_thread = Process(target=convert_folder, args=(os_cap_folder, os_ana_folder))
            os_save_thread.daemon = True
            os_save_thread.start()  

            #same for CY
            cy_cap_folder = os.path.join(capture_folder,'cam_cy')
            cy_ana_folder = os.path.join(analysis_folder,'cam_cy')
            if not os.path.exists(cy_ana_folder):
                os.makedirs(cy_ana_folder)
            #convert_folder(cy_cap_folder, cy_ana_folder)
            cy_save_thread = Process(target=convert_folder, args=(cy_cap_folder, cy_ana_folder))
            cy_save_thread.daemon = True
            cy_save_thread.start() 
            
            #wait for all processes to finish
            print('Waiting for frame conversions...')
            for proc in [od_save_thread, os_save_thread, cy_save_thread]:
                proc.join()
            print('Done with frame conversions.')
            
    except Exception as e:
        print(e)
        print('Problem with analzing saved scene camera files. Tell Vasha to make more informative error reporting!')

def run_analysis(subject_name=None, task_name=None, exp_type=None, 
                 read_dir='./capture', save_dir='./analysis',
                 run_timestamp_stats=True, run_convert_ims=True):
    
    '''
    Run a data analysis, on a pre or post calibration, or an experiment.
    Params:
        subject (string): Subject ID to be included in file structure
        task_name (string): Name of task to be included in file structure
        exp_type (string): Type of experiment, either 'pre', 'post', or 'exp'
        save_dir (string): Name of base directly to save experiment files
        
    '''
    
    #create directory structure to find capture files
    read_folder = os.path.join(read_dir, subject_name, task_name, exp_type)
    scene_cam_read_folder = os.path.join(read_folder,'scene_camera')
    eye_cam_read_folder = os.path.join(read_folder,'eye_camera')
    imu_read_folder = os.path.join(read_folder, 'imu')
    
    #create directory structure to save analyzed files
    save_folder = os.path.join(save_dir, subject_name, task_name, exp_type)
    scene_cam_save_folder = os.path.join(save_folder,'scene_camera')
    eye_cam_save_folder = os.path.join(save_folder,'eye_camera')
    imu_save_folder = os.path.join(save_folder, 'imu')
    
    #run sceme camera analysis
    print('Running Frame Analysis...')
    run_ximea_analysis(scene_cam_read_folder, scene_cam_save_folder,
                       timestamp_stats=run_timestamp_stats,
                       convert_ims=run_convert_ims)
    
    #run eye tracker analysis
    #run IMU analysis
    
    print("Finished Anaysis!")
    

    
def count_missed_frames(timestamp_file, cam_name):
    with open(timestamp_file, 'r') as f:
        ts_table=list(zip(line.strip().split('\t') for line in f))
    
    ts_table = np.squeeze(np.array(ts_table[1:]).astype('float'))
    total_frames = ts_table.shape[0]
    nf = ts_table[:,1]
    df = nf[1:] - nf[:-1] - 1
    df = np.sum(df)
    dfp = df / total_frames * 100
    
    print(f'{cam_name} missed frames total: {df} / {total_frames} = {dfp:0.2f}%')
    
    return(dfp)
    

def plot_camera_timing(timestamp_file, figwrite_file, cam_name):
    with open(timestamp_file, 'r') as f:
        ts_table=list(zip(line.strip().split('\t') for line in f))
    
    ts_table = np.squeeze(np.array(ts_table[1:]).astype('float'))
    ts = ts_table[:,2]
    dt = ts[1:] - ts[:-1]

    med_dt = np.median(dt)
    med_fr = 1/np.median(dt)
    mean_dt = np.mean(dt)
    mean_fr = 1/np.mean(dt)

    plt.plot(dt)
    plt.axhline(med_dt,label=f'median: {med_dt:.5f} = {med_fr:.2f}fps',c='black')
    plt.axhline(0.005,label='200fps',c='red')
    plt.axhline(mean_dt,label=f'mean: {mean_dt:.5f} = {mean_fr:.2f}fps',c='green')
    plt.plot(dt, label='sample', c='blue')
    plt.ylabel('dt')
    plt.legend()
    plt.title(f'{cam_name} Camera Timing')
    plt.savefig(figwrite_file)
    plt.show()
    
def plot_camera_dframe(timestamp_file, figwrite_file, cam_name):
    with open(timestamp_file, 'r') as f:
        ts_table=list(zip(line.strip().split('\t') for line in f))
    
    ts_table = np.squeeze(np.array(ts_table[1:]).astype('float'))
    ts = ts_table[:,1]
    dt = ts[1:] - ts[:-1]

    med_dt = np.median(dt)
    mean_dt = np.mean(dt)
    

    plt.plot(dt)
    plt.axhline(1,label='All Frames Kept',c='red')
    plt.axhline(med_dt,label=f'median: {med_dt:.5f}',c='black')
    plt.axhline(mean_dt,label=f'mean: {mean_dt:.5f}',c='green')
    plt.plot(dt, label='sample', c='blue')
    plt.ylabel('dframe')
    plt.legend()
    plt.title(f'{cam_name} Camera Dframes')
    plt.savefig(figwrite_file)
    plt.show()
    
def ximea_timestamp_to_framenum(timestamp_file, timestamp):
    '''
    Given a unix timestamp, what is the closest frame from a ximea camera recording?
    Params:
        timestamp_file (str): path to a timestamp file for this camera
        timestamp (float): timestamp desired.
    Returns:
        i (int): frame number of collection *NOT NFRAME CAMERA COUNTER*) closest to timestamp
        true_timestamp (float): What is the real timestamp of this frame?
    '''
    with open(timestamp_file, 'r') as f:
        ts_table=list(zip(line.strip().split('\t') for line in f))
    
    ts_table = np.squeeze(np.array(ts_table[1:]).astype('float'))
    closest_idx = np.argmin(np.abs(ts_table[:,3]-timestamp))
    i = int(ts_table[closest_idx,0])
    true_timestamp = ts_table[closest_idx,3]
    return(i, true_timestamp)
    
def ximea_framenum_to_timestamp(timestamp_file, framenum):
    '''
    Given a unix timestamp, what is the closest frame from a ximea camera recording?
    Params:
        timestamp_file (str): path to a timestamp file for this camera
        framenum (int): framenum desired ***THIS IS NOT NFRAME CAMERA COUNTER but counter with respect to collection******.
    Returns:
        ts (float): timestamp of framenum frame
    '''
    
    with open(timestamp_file, 'r') as f:
        ts_table=list(zip(line.strip().split('\t') for line in f))
    
    ts_table = np.squeeze(np.array(ts_table[1:]).astype('float'))
    ts = np.float(ts_table[np.where(ts_table[:,0]==framenum),3])
    return(ts)

def ximea_get_frame(frame_number, save_batchsize, cam_name, cam_save_folder, img_dims=(1544,2064), normalize=True):
    '''
    Get the filename and offset of a given frame number from the camera.
    Params:
        frame_number (int): number of frame desired
        save_bathsize (int): what was the batchsize during collection?
        cam_name (str): what is the name of the caera? OD/OS/CY
        cam_save_folder (str): what is the name of the folder?
        img_dims (int, int): dimensions of frame reading in.
    Returns:
        frame (2d numpy array): 2d array of frame from saved file
    '''
    
    file_start = int(np.floor(frame_number/save_batchsize)*save_batchsize)
    file_end = file_start + save_batchsize - 1
    frame_offset = frame_number%file_start if file_start>0 else frame_number
    file_name = f'frames_{file_start}_{file_end}.bin'
    file_path = os.path.join(cam_save_folder, cam_name, file_name)
    
    frame = bin_to_im(file_path, frame_offset, img_dims)
    
    if normalize:
        frame = frame/75
        frame[frame > 1] = 1
        
    return(frame)

def pupil_framenum_to_timestamp(timestamp_file, framenum):
    '''
    Given a unix timestamp, what is the closest frame from a pupil camera recording?
    Params:
        timestamp_file (str): path to a timestamp file for this camera
        framenum (int): framenum desired
    Returns:
        ts (float): timestamp of framenum frame
    '''
    timestamp_list = np.load(timestamp_file)
    ts = timestamp_list[framenum]
    return(ts)

def pupil_timestamp_to_framenum(timestamp_file, timestamp):
    '''
    Given a unix timestamp, what is the closest frame from a pupil camera recording?
    Params:
        timestamp_file (str): path to a timestamp file for this camera
        timestamp (float): timestamp desired.
    Returns:
        i (int): frame number of collection *NOT NFRAME CAMERA COUNTER*) closest to timestamp
        true_timestamp (float): What is the real timestamp of this frame?
    '''
    timestamp_list = np.load(timestamp_file)
    i = np.argmin(np.abs(timestamp_list-timestamp))
    true_timestamp = timestamp_list[i]

    return(i, true_timestamp)

def pupl_get_framemeans(video_file, frame_start, nframes):
    '''
    Caclualte the framemeans for a set of frames in sucession
    '''
    vidcap = cv2.VideoCapture(video_file)
    means = []
    for i in range(frame_start):
        success, frame = vidcap.read()
    for i in range(frame_start, frame_start+nframes):
        success, frame = vidcap.read()
        means.append(np.mean(frame))
    
    return(means)

def pupil_get_frame(video_file, framenum, normalize=False):
    '''
    Grab the Pupil Cam Frame at a given framenum
    Params:
        video_file (str): path to a video file for this camera
        framenum (int): framenumber desired.
        normalize (bool): normalize the frame?
    Returns:
        frame (2d array): image from pupil camera
    '''
    vidcap = cv2.VideoCapture(video_file)
    for i in range(framenum):
        success, frame = vidcap.read()
    if(normalize):
        frame = 255*(frame/np.max(image))
    return(frame)

def convert_ximea_time_to_unix_time(timestamp_file, sync_file):
    '''
    Convert the ximea camera times to unix timestamps
    Params:
        timestamp_file (str): path to .csv file with ximea timesstamps
        sync_file (str): path to .csv file with sync information
    Returns:
        unix_timestamp_array (2d np array): Unix Timestamps Inferred
    '''
    with open(timestamp_file, 'r') as f:
        ts_table=list(zip(line.strip().split('\t') for line in f))
    ts_table = np.squeeze(np.array(ts_table[1:]).astype(np.double))

    with open(sync_file, 'r') as f:
        sync_table=list(zip(line.strip().split('\t') for line in f))
        
    (unix_pre, cam_pre) = np.array(sync_table[1][0][1:]).astype(np.double)
    (unix_post, cam_post) = np.array(sync_table[2][0][1:]).astype(np.double)

    #how far off have the computer and camera timestamps drifted?
    t_elapsed_unix = np.double(unix_post) - np.double(unix_pre)
    t_elapsed_cam = np.double(cam_post) - np.double(cam_pre)
    drift = np.abs(t_elapsed_unix - t_elapsed_cam)
    print(f'Time Elapsed: {t_elapsed_unix} seconds')
    print(f'Time Drift pre to post: {drift} seconds')
    
    # We assume here that time.time() in Linux's 0.001s precision is better than camera's.
    # Convert Camera timestamps to Unix timestamps.
    #first convert to [0,1]
    #t_cam_converted = (ts_table[:,2] - cam_pre) / (cam_post - cam_pre)
    #then convert to wall time
    #t_cam_converted = (t_cam_converted * (unix_post - unix_pre)) + unix_pre
    
    #assume time in camera is linear, and just change offset at pre.
    t_cam_converted = ts_table[:,2] - ts_table[0,2] + unix_pre
    
    print(t_cam_converted[0])
    
    #add unix time to data
    t_cam_converted = np.append(ts_table, np.expand_dims(t_cam_converted,1),axis=1)
    
    return(t_cam_converted)
