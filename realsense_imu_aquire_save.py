import realsense.more_devices_test as pyrs2d
#import datetime
import time
import os

def run_realsense_aquisition(save_folder, collection_mins, component_name='IMU'):
    '''
    Aquire IMU data from realsense trackers and save it.
    Parameters:
        save_folder (str): name of folder to save images
        collection_mins (int): how long should we collect?
    Returns:
        None
    '''
    
    #MUST FIND EXACTLY 2 TRACKERS TO NOT THROW ERROR
    try:
        t1sd, t2sd = pyrs2d.get_devices_serial_numbers()
        t1 = pyrs2d.T265CameraSource(t1sd)
        t2 = pyrs2d.T265CameraSource(t2sd)
    except:
        print(f'{component_name} ERROR: Two Realsense Trackers Not Found!')
        print(f'{component_name} Not recording IMU Data.')
    
        return()
    
    ##File Structure
    if not os.path.exists(os.path.join(save_folder)):
        os.makedirs(os.path.join(save_folder))
    t1_file_name = os.path.join(save_folder, f"imu_data_{t1sd}.tsv")
    t2_file_name = os.path.join(save_folder, f"imu_data_{t2sd}.tsv")

    with open(t1_file_name, 'w') as t1_file:
        t1_file.write(f"i\txyz\ttime\n")    
    with open(t2_file_name, 'w') as t2_file:
        t2_file.write(f"i\txyz\ttime\n")
    
    start_time = time.time()
    i=0
    with open(t1_file_name, 'a+') as t1_file, open(t2_file_name, 'a+') as t2_file:
        while(time.time() - start_time < collection_mins*60):
        
            t1_file.write(f"{i}\t{t1.get_xyz()}\t{time.monotonic()}\n")
            t2_file.write(f"{i}\t{t2.get_xyz()}\t{time.monotonic()}\n")
            
            i+=1
    
    print(f'{component_name} Finished Realsense Aquisition.')

    #hardware resets not working at this time
    #t1.do_hardware_reset()
    #t2.do_hardware_reset()
    #print(f'{component_name} Camearas Reset.')
    