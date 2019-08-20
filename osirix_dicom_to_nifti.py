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
import fnmatch
import json
import copy

def remove_ds_store(folder):	
	# Get a list of all files in directory
	for rootDir, subdirs, filenames in os.walk(folder):
		# Find the files that matches the given patterm
		for filename in fnmatch.filter(filenames, '*[Dd][Ss]*[Ss]tore*'):
			try:
				#print (os.path.join(rootDir,filename))
				os.remove(os.path.join(rootDir, filename))
			except OSError:
				print("Error while deleting file")

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

def check_directory(input_dir,json_config):
	remove_ds_store(input_dir)
	output_dir = input_dir

	with open(json_config, 'r') as f:
		config = json.load(f)

	series_key = dict()
	for tag, series in enumerate(config["series_names"]):
		series_key[str(tag)] = series	
	
	if config["special_conversion"]=='HCC':
		for i in os.listdir(input_dir):
			#make_folder_if_absent(os.path.join(output_dir,i))
			for j in os.listdir(os.path.join(input_dir,i)):
				print ("Assessing "+i,j)
				sortcrap(os.path.join(input_dir,i,j),os.path.join(output_dir,i,j))
			print ("****Sorted through possible crap in "+i)
	
	if config["special_conversion"]=="CTA-2phase":
		pass


def make_big_table(input_dir,json_config):

	with open(json_config, 'r') as f:
		config = json.load(f)

	series_key = dict()
	for tag, series in enumerate(config["series_names"]):
		series_key[str(tag)] = series
	
	in_dir_list = os.listdir(input_dir)

	big_table = list()

	for i in in_dir_list:
		##Patient Folders
		#print (i)
		if i.startswith(".") == True:
			pass
		else:
		
			for j in os.listdir(os.path.join(input_dir,i)):
				print (j)
				##Study folders (only one, for now)
				study_folder = os.path.join(input_dir,i,j)
				slugged_study_folder = os.path.join(input_dir,i,slugify(j))
				shutil.move(study_folder,slugged_study_folder)
				
				for k in os.listdir(slugged_study_folder):
					##Series Folders
					print (j,k)
					
					series_folder_path = os.path.join(slugged_study_folder,k)
					slugged_series_folder = os.path.join(slugged_study_folder,slugify(k))
					shutil.move(series_folder_path,slugged_series_folder)
					dicoms_in_series = os.listdir(slugged_series_folder)

					try:
						info = pydicom.read_file(os.path.join(slugged_series_folder,dicoms_in_series[0]),force=True)

					except OSError as e:
						print (str(e)+" for "+os.path.join(slugged_series_folder,dicoms_in_series[0]))
						big_table.append(["File Name Error for "+i+j+k,"","","","",""])

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
						pixel_spc = info[0x0028,0x0030].value
						slice_thck = info[0x0018,0x0050].value

						big_table.append([mrn,acc,machine,slugged_series_folder,acquisition_time,series_num,series_desc," ",pixel_spc,slice_thck])
						#print (mrn,acc,os.path.join(input_dir,i,j,k),acquisition_time,series_desc)

					except KeyError:
						big_table.append(["Key Error for "+acc+series_desc,"","","","",""])
						#print ("Key Error for "+acc+series_desc)
						pass
	##Sort by MRN, then ACC, then Acq Time, then Series Number
	big_table = sorted(big_table, key=itemgetter(1,4,5))
	big_table.insert(0,["MRN","ACC","Machine","Series Path","Acq Time","Series Number","Series Desc","Tag"+str(series_key),"XY Resolution","Slice Size"])

	return big_table


def write_dicom_table(dicom_table, table_dir):
	with open(table_dir,'w') as t:
	  writer = csv.writer(t)
	  writer.writerows(dicom_table)

def write_by_series(json_config,input_table,output_dir):

	with open(json_config, 'r') as f:
		config = json.load(f)

	print ("Starting Conversion with "+str(config["project"])+" Configuration")
			
	##Create tag to series list

	series_key = dict()
	for tag, series in enumerate(config["series_names"]):
		series_key[str(tag)] = series

	with open(input_table,'rt') as t:
		reader = csv.reader(t, delimiter=',')

		#row_tags = [str(tag) for tag,series in series_key.items()]

		tagged_row = (row for row in reader if row[7] in [tag for tag,series in series_key.items()])

		for row in tagged_row:
			acc = row[1]
			make_folder_if_absent(os.path.join(output_dir,acc))

			image = series_key[row[7]]

			if os.path.isfile(os.path.join(output_dir,acc,image+".nii.gz"))==True:
				print ("ALREADY CONVERTED")
				continue

			if image == "two-phase":
				split_then_convert(image,row,output_dir,config)
				continue

			convert_to_nifti(image,row,output_dir)			
		else:
			pass
			print ("Already converted, or inappropriate tag "+str(row))

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

def split_then_convert(image,row,output_dir,config):

	print ("Splitting Folder By Acquisition Time")

	if config["special_conversion"] == "CTA-2phase":
		
		times = list()
		
		for i in os.listdir(row[3]):
			if os.path.isdir(os.path.join(row[3],i)):
				continue
			info = pydicom.read_file(os.path.join(row[3],i))
			times.append(info[0x0008,0x0032].value)
		
		unique_times = list(set(times))

		print ("Before Sort "+str(unique_times))
		unique_times.sort()
		print ("After Sort "+str(unique_times))

		make_folder_if_absent(os.path.join(row[3],"Arterial"))
		make_folder_if_absent(os.path.join(row[3],"Venous"))

		for i in os.listdir(row[3]):
			if os.path.isdir(os.path.join(row[3],i)):
				continue
			info = pydicom.read_file(os.path.join(row[3],i))
			if info[0x0008,0x0032].value == unique_times[0]:
				os.rename(os.path.join(row[3],i),os.path.join(row[3],"Arterial",i))
			if info[0x0008,0x0032].value == unique_times[1]:
				os.rename(os.path.join(row[3],i),os.path.join(row[3],"Venous",i))

		art_row = copy.copy(row)
		ven_row = copy.copy(row)
		
		art_row[3] = os.path.join(row[3],"Arterial")
		ven_row[3] = os.path.join(row[3],"Venous")

		if os.path.isfile(os.path.join(output_dir,row[1],"arterial.nii.gz"))==False and os.path.isfile(os.path.join(output_dir,row[1],"venous.nii.gz"))==False:	
			convert_to_nifti("arterial",art_row,output_dir)
			convert_to_nifti("venous",ven_row,output_dir)
		else:
			print ("ALREADY CONVERTED")

parser = argparse.ArgumentParser(description='HorosExportToNiftiForHCC')

parser.add_argument("--dicomDir", dest="input_dir", required=False)
parser.add_argument("--tablePath", dest="table_dir", required=False)
parser.add_argument("--niftiDir", dest="output_dir", required=False)
parser.add_argument("--configFile", dest="json_config", required=True)

parser.add_argument("--grabMetadata", action="store_true", dest="grabMeta", default=False)
parser.add_argument("--convertFromTable", action="store_true", dest="convert", default=False)


op  = parser.parse_args()

if op.grabMeta == True:
	remove_ds_store(op.input_dir)
	big_table = make_big_table(op.input_dir,op.json_config)
	write_dicom_table(big_table, op.table_dir)

if op.convert == True:
	if op.table_dir is not None and op.json_config is not None:
		write_by_series(op.json_config,op.table_dir,op.output_dir)
		check_directory(op.output_dir,op.json_config)
	else:
		print ("Need to define input table with proper tags")
