import os
import numpy as np
import cv2
from multiprocessing import Process
import re
import matplotlib.pyplot as plt

def convert_bin_png(filename, save_folder, im_shape=(1544,2064), img_format='XI_RAW8'):
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
    lr_camera_dcaps = np.abs(ts_table[:,1] - ts_table[:,2])
    os_dts = ts_table[1:,1] - ts_table[:-1,1]
    od_dts = ts_table[1:,2] - ts_table[:-1,2]
    cy_dts = ts_table[1:,3] - ts_table[:-1,3]
    
    print(f'Mean camera time disparity: {np.mean(lr_camera_dcaps):.4f} seconds')
    print(f'Mean OS dts: {np.mean(os_dts):.4f} seconds')
    print(f'Mean OD dts: {np.mean(od_dts):.4f} seconds')
    print(f'Mean CY dts: {np.mean(cy_dts):.4f} seconds')    
    
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
    
