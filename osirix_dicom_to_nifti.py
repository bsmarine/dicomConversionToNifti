#### This takes DICOM files of studies with multiple series exported from Osirix (with hierarchy and non-deidentified options selected) and converts them into Nifti files in a two part process:
### 1) A csv "big table" is created with a row for each series of each study. User then assigns a tag in the column following series description that will correspond to an abbreviated output file name for a converted nifti.
### 2) After desired tags are annotated in the "big table" manually (or in the future a more clever way) the code is run again reading this annotated "big table" and converts tagged series acccordingly into nifits and puts then in a folder named by accession number


import SimpleITK as sitk
import numpy as np
import os
import pydicom
import csv
from operator import itemgetter
from nipype.interfaces.dcm2nii import Dcm2niix
from slugify import slugify
import shutil
import argparse

def make_folder_if_absent(acc_folder):
    if os.path.exists(acc_folder) == True:
      pass
    else:
      os.mkdir(acc_folder)

def sortcrap(input,output):
    input_img = sitk.ReadImage(input)
    print ("Directions")
    print (input_img.GetDirection())
    if len(input_img.GetDirection())>9:
        combinenflip(input_img,output)
    elif np.rint(input_img.GetDirection()[0]) == 1 and np.rint(input_img.GetDirection()[4] == 1):
        print (input_img.GetDirection())
        flip(input_img,output)
    else:
        img = input_img
        new_spacing = img.GetSpacing()[0],img.GetSpacing()[1],img.GetSpacing()[2]
        sitk.WriteImage(img,output)

def flip(img,output):
        new_spacing = img.GetSpacing()[0],img.GetSpacing()[1],img.GetSpacing()[2]
        arr = sitk.GetArrayFromImage(img)
				
        #Flip over x-axis
        fl_narr = np.flip(arr,axis=0)
				
        #Change to Image from Array
        new_img = sitk.GetImageFromArray(fl_narr)

        #Update Spacing/Resolution
        new_img.SetSpacing(new_spacing)
        print ("Confirm Spacing of New Flip-Only Routine")
        print (new_img.GetSpacing())

        #Write Image
        sitk.WriteImage(new_img,output)


def combinenflip(img,output):
    new_spacing = img.GetSpacing()[0],img.GetSpacing()[1],img.GetSpacing()[2]
    arr = sitk.GetArrayFromImage(img)
    print ("Shape of breakdown")
    print (arr[0].shape)
    print (arr[1].shape)
		
    #Combine and Flip Arrays with Numpy
    new_arr = np.append(arr[1],arr[0],axis=0)
    #fl_narr = new_arr
    fl_narr = np.flip(new_arr,axis=1)
    print ("Shape of New Array")
    print (fl_narr.shape)
		
    #Change to Image from Array
    new_img = sitk.GetImageFromArray(fl_narr)
		
    #Update Spacing/Resolution
    new_img.SetSpacing(new_spacing)
    print ("Confirm Voxel Dimensions")
    print (new_img.GetSpacing())
		
    #Write Image
    sitk.WriteImage(new_img,output)

def check_directory(input_dir):
  output_dir = input_dir
  for i in os.listdir(input_dir):
      if "DS_Store" in i:
          pass
      else:
          #make_folder_if_absent(os.path.join(output_dir,i))
          for j in os.listdir(os.path.join(input_dir,i)):
            if "DS_Store" in j:
              pass
            else:
              print ("Assessing "+i,j)
              sortcrap(os.path.join(input_dir,i,j),os.path.join(output_dir,i,j))
          print ("****Sorted through possible crap in "+i)

def make_big_table(input_dir):
    in_dir_list = os.listdir(input_dir)

    big_table = list()

    for i in in_dir_list:
        ##Patient Folders
        #print (i)
        if i.startswith(".") == True:
          pass
        else:
        
          for j in os.listdir(os.path.join(input_dir,i)):
            if "ds-store" in j:
              pass
            else:
              
            
            ##Study folders (only one, for now)
              study_folder = os.path.join(input_dir,i,j)
              slugged_study_folder = os.path.join(input_dir,i,slugify(j))
              shutil.move(study_folder,slugged_study_folder)
            
              for k in os.listdir(slugged_study_folder):
                ##Series Folders
                print (k)
                if "ds-store" in k:
                  pass
                else:
                
                  series_folder_path = os.path.join(slugged_study_folder,k)
                  slugged_series_folder = os.path.join(slugged_study_folder,slugify(k))
                  shutil.move(series_folder_path,slugged_series_folder)
                  dicoms_in_series = os.listdir(slugged_series_folder)
                  info = pydicom.read_file(os.path.join(slugged_series_folder,dicoms_in_series[0]))

                  try:
                      acc = info[0x008,0x0050][:]
                      mrn = info[0x010,0x0020][:]
                      dob = info[0x010,0x0030].value
                      machine = info[0x008,0x1090].value
                      gender = info[0x010,0x0040].value
                      series_desc = info[0x0008,0x103e].value
                      #date = info[0x008,0x0022].value
                      acquisition_time = info[0x0008,0x0032].value
                      series_num = info[0x0020,0x0011].value
                      acq_date = info[0x0008,0x0020].value

                      big_table.append([mrn,acc,machine,slugged_series_folder,acquisition_time,series_num,series_desc])
                      #print (mrn,acc,os.path.join(input_dir,i,j,k),acquisition_time,series_desc)

                  except KeyError:
                      big_table.append(["Key Error for "+acc+series_desc,"","","","",""])
                      #print ("Key Error for "+acc+series_desc)
                      pass
    ##Sort by MRN, then ACC, then Acq Time, then Series Number
    big_table = sorted(big_table, key=itemgetter(1,4,5))
    big_table.insert(0,["MRN","ACC","Machine","Series Path","Acq Time","Series Number","Series Desc","Tag(0=pre,1=ea,2=ea_sub,3=la,4=la_sub,5=pv,6=pv_sub,7=ev,8=ev_sub,9=adc)"])

    return big_table


def write_dicom_table(dicom_table, table_dir):
    with open(table_dir,'w') as t:
      writer = csv.writer(t)
      writer.writerows(dicom_table)

def write_by_series(input_table,output_dir):
    with open(input_table,'rt') as t:
        reader = csv.reader(t, delimiter=',')
        for row in reader:
            print (row)
            if row[7] not in ['0','1','2','3','4','5','6','7','8','9']:
                print ("Skipping Conversion for "+row[1]+row[5])
                pass
#            if row[7] not in ['0','1','2','3','4','5','6','7','8','9']:
#                pass
            else:
                acc = row[1]
                make_folder_if_absent(os.path.join(output_dir,acc))

                if row[7] == '0'and os.path.isfile(os.path.join(output_dir,acc,'T1_pre'+'.nii.gz'))== False:
                    convert_to_nifti('T1_pre',row,output_dir)
                elif row[7] == '1'and os.path.isfile(os.path.join(output_dir,acc,'T1_EA'+'.nii.gz'))== False:
                    convert_to_nifti('T1_EA',row,output_dir)
                elif row[7] == '2'and os.path.isfile(os.path.join(output_dir,acc,'T1_EA_sub'+'.nii.gz'))== False:
                    convert_to_nifti('T1_EA_sub',row,output_dir)
                elif row[7] == '3' and os.path.isfile(os.path.join(output_dir,acc,'T1_LA'+'.nii.gz'))== False:
                    convert_to_nifti('T1_LA',row,output_dir)
                elif row[7] == '4'and os.path.isfile(os.path.join(output_dir,acc,'T1_LA_sub'+'.nii.gz'))== False:
                    convert_to_nifti('T1_LA_sub',row,output_dir)
                elif row[7] == '5' and os.path.isfile(os.path.join(output_dir,acc,'T1_PV'+'.nii.gz'))== False:
                    convert_to_nifti('T1_PV',row,output_dir)
                elif row[7] == '6' and os.path.isfile(os.path.join(output_dir,acc,'T1_PV_sub'+'.nii.gz')) == False:
                    convert_to_nifti('T1_PV_sub',row,output_dir)
                elif (row[7] == '7' and os.path.isfile(os.path.join(output_dir,acc,'T1_ev'+'.nii.gz')) == False):
                    convert_to_nifti('T1_EV',row,output_dir)
                elif (row[7] == '8' and os.path.isfile(os.path.join(output_dir,acc,'T1_ev_sub'+'.nii.gz')) == False):
                    convert_to_nifti('T1_EV_sub',row,output_dir)
                elif (row[7] == '9'and os.path.isfile(os.path.join(output_dir,acc,'ADC'+'.nii.gz')) == False):
                    convert_to_nifti('ADC',row,output_dir)
                else:
                    print ("Already converted, or inappropriate tag "+str(row))

                    pass

def convert_to_nifti(name,row,output_dir):
    print ("Begin Converting "+row[1]+row[6])
    print ("Converting from this source dir "+os.path.abspath(row[3]))
    print ("Writing to this dest filename "+os.path.join(output_dir,row[1],name))
    acc = row[1]
    converter = Dcm2niix()
    converter.inputs.source_dir = os.path.abspath(row[3])
    converter.inputs.compress = 'y'
    converter.inputs.out_filename = name
    converter.inputs.output_dir = os.path.join(output_dir,acc)

    try:
        converter.run()

    except Exception as e:
        print (e)
        print ("Error with dcm2nii for "+row[1]+row[6]+", skipping")


parser = argparse.ArgumentParser(description='HorosExportToNiftiForHCC')

parser.add_argument("--dicomDir", dest="input_dir", required=False)
parser.add_argument("--tablePath", dest="table_dir", required=False)
parser.add_argument("--niftiDir", dest="output_dir", required=False)

parser.add_argument("--grabMetadata", action="store_true", dest="grabMeta", default=False)
parser.add_argument("--convertFromTable", action="store_true", dest="convert", default=False)


op  = parser.parse_args()

if op.grabMeta == True:
	big_table = make_big_table(op.input_dir)
	write_dicom_table(big_table, op.table_dir)

if op.convert == True:
  if op.table_dir is not None:
    write_by_series(op.table_dir,op.output_dir)
    check_directory(op.output_dir)
  else:
    "Need to define input table with proper tags"
