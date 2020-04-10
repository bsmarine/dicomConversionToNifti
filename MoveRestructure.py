import sys
import os
import SimpleITK as sitk
import pydicom
from slugify import slugify
import shutil
import argparse

def gen_dcm_identifiers(in_dir):
    ##Get Absolute Path For Every DCM File Recursively
    dcms_path_list = [os.path.abspath(os.path.join(dire,dcm)) for dire,sub_dir,dcms in os.walk(in_dir) if 'dcm' in str(dcms) for dcm in dcms]
    
    ##Output List
    output_list = list()
    
    ## Generate List with MRN, Accession Number, Series Description, Series Number, Acq Date
    for dcm_file in dcms_path_list:
        info = pydicom.read_file(dcm_file)
        try:
            mrn = info[0x010,0x0020][:]
            acc = info[0x008,0x0050][:]
            series_desc = info[0x0008,0x103e].value
            series_num = info[0x0020,0x0011].value
            acq_date = info[0x0008,0x0020].value
            
            string = str(series_desc)+"_"+str(series_num)+"_"+str(acq_date)
            string_date = slugify(string)
            
            output_list.append([mrn,acc,string_date,dcm_file])
            
        except KeyError:
            print ("Error getting metadata from "+str(dcm_file))
            
    return output_list

def create_folders_move(dcm_ids,out_dir):
    if os.path.exists(out_dir) == False:
        os.mkdir(out_dir)
    for i in dcm_ids:
        print (i)
        if os.path.exists(os.path.join(out_dir,i[0]))==False:
            os.mkdir(os.path.join(out_dir,i[0]))
        if os.path.exists(os.path.join(out_dir,i[0],i[1]))==False:
            os.mkdir(os.path.join(out_dir,i[0],i[1]))
        if os.path.exists(os.path.join(out_dir,i[0],i[1],i[2]))==False:
            os.mkdir(os.path.join(out_dir,i[0],i[1],i[2]))
        try:
            shutil.move(i[3],os.path.join(out_dir,i[0],i[1],i[2]))
            print ("######## Moving "+str(i[3])) 
        except:
            print ("Error, likely file already exists in destination")
            
parser = argparse.ArgumentParser(description='MoveRestructureScript')

parser.add_argument("--dicomDir", dest="in_dir", required=True)
parser.add_argument("--outDir", dest="out_dir", required=True)

op  = parser.parse_args()

create_folders_move(gen_dcm_identifiers(op.in_dir), op.out_dir)
