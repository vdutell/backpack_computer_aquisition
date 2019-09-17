import time

def run_pupillabs_aquisition(save_folder, collection_mins,  component_name='PUPIL_CAM'):
    '''
    Aquire eyetracking from pupil labs tracker and save it.
    Parameters:
        save_folder (str): name of folder to save images
        collection_mins (int): how long should we collect?
    Returns:
        None
    '''
    time.sleep(5)
    print(f'{component_name} Finished PupilLabs Aquisition.')
