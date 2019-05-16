# dicomConversionToNiftiHCC

This python script facilitates batch MRI annotation with 3D Slicer's Case Iterator Extension by doing the following:

  * Near autonomous conversion of DICOM images to medical image processing-friendly nifti format
  * Deidentification
  * Assignment of a standardized naming convention relevant to a given annotation routine, for example, labling liver lesions on T1 and ADC sequences before and after treatment (easily customized for other uses)

## Dependencies

SimpleITK \
Numpy \
PyDicom \
NiPype \
Slugify

## Usage

Script assumes a nested folder eg tree study-->series-->DICOM (standard when exportingw with Osirix or Horos). This should easily by adapted for other folder structures if working with exported images from other DICOM viewers/PACS servers.

There are two script calls needed:.
1) Grab Metadata: create a .csv with relevant metadata in table for tagging of desired series by domain expert (or algorithm in future)

2) Convert From Table: conversion, deidentification and standardized naming of converted sequences using the annotated tag column from 1) Metadata table.

### Grab Metadata into Table

`python osirix_dicom_to_nifti.py --grabMetadata --tablePath ./path/to/metadata/table.csv --dicomDir ./path/to/folder/containing/study/folders`

This will generate a .csv file with columns of metadata for each series of an MRI study meant to allow inference of which series' are desired for conversion. 

**Heads up:** this can be a lot of rows as modern MRI studies generate a lot of series!

An empty tag column will be generated and with some domain knowledge the user must fill-in with the appropriate tag number.

Example is as follows (take note of the number inputted in the tag column):

|MRN                                                                                                                                                                                              |ACC |Machine      |Series Path|Acq Time|Series Number                                              |Series Desc                                            |Tag(0=pre,1=ea,2=ea_sub,3=la,4=la_sub,5=pv,6=pv_sub,7=ev,8=ev_sub,9=adc)|
|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----|-------------|-----------|--------|-----------------------------------------------------------|-------------------------------------------------------|------------------------------------------------------------------------|
|9999999                                                                                                                                                                                          |000001|Avanto       |./Y90_Seg/name/body-mt-sinai-protocols-abdomen/trufisp-loc-1|110028.625|1                                                          |Trufisp_Loc                                            |                                                                        |
|9999999                                                                                                                                                                                          |000001|Avanto       |./Y90_Seg/name/body-mt-sinai-protocols-abdomen/cor-haste-2|110142.875|2                                                          |COR HASTE                                              |                                                                        |
|9999999                                                                                                                                                                                          |000001|Avanto       |./Y90_Seg/name/body-mt-sinai-protocols-abdomen/3point-dixon-t2-star-031511-fa10-modified-6611-opp-6|110544.7325|6                                                          |3-point Dixon_T2 star_03-15-11_FA10_modified 6/6/11_opp|                                                                        |
|9999999                                                                                                                                                                                                                                                                                                                                                                                |000001|Avanto       |./Y90_Seg/name/body-mt-sinai-protocols-abdomen/3point-dixon-t2-star-031511-fa10-modified-6611-in-5|110544.735|5                                                          |3-point Dixon_T2 star_03-15-11_FA10_modified 6/6/11_in |                                                                        |
|9999999                                                                                                                                                                                                                                                                                                                                                                                                                                                    |000001|Avanto       |./Y90_Seg/name/body-mt-sinai-protocols-abdomen/ax-vibe-pre-62612-13|110828.9625|13                                                         |AX VIBE PRE (6/26/12)                                  |0                                                                       |
|9999999                                                                                                                                                                                          |000001|Avanto       |./Y90_Seg/name/body-mt-sinai-protocols-abdomen/ax-vibe-post-2art-1min-3min-equ-14|111014.0575|14                                                         |AX VIBE POST 2ART,1MIN,3MIN EQU                        |1                                                                       |
|9999999                                                                                                                                                                                          |000001|Avanto       |./Y90_Seg/name/body-mt-sinai-protocols-abdomen/ax-vibe-post-2art-1min-3min-equ-sub-15|111014.0575|15                                                         |AX VIBE POST 2ART,1MIN,3MIN EQU_SUB                    |2                                                                       |
|9999999                                                                                                                                                                                          |000001|Avanto       |./Y90_Seg/name/body-mt-sinai-protocols-abdomen/ax-vibe-post-2art-1min-3min-equ-16|111035.2275|16                                                         |AX VIBE POST 2ART,1MIN,3MIN EQU                        |3                                                                       |
|9999999                                                                                                                                                                                          |000001|Avanto       |./Y90_Seg/name/body-mt-sinai-protocols-abdomen/ax-vibe-post-2art-1min-3min-equ-sub-17|111035.2275|17                                                         |AX VIBE POST 2ART,1MIN,3MIN EQU_SUB                    |4                                                                       |
|9999999                                                                                                                                                                                          |000001|Avanto       |./Y90_Seg/name/body-mt-sinai-protocols-abdomen/ax-vibe-post-2art-1min-3min-equ-18|111114.47|18                                                         |AX VIBE POST 2ART,1MIN,3MIN EQU                        |5                                                                       |
|9999999                                                                                                                                                                                          |000001|Avanto       |./Y90_Seg/name/body-mt-sinai-protocols-abdomen/ax-vibe-post-2art-1min-3min-equ-sub-19|111114.47|19                                                         |AX VIBE POST 2ART,1MIN,3MIN EQU_SUB                    |6                                                                       |
|9999999                                                                                                                                                                                          |000001|Avanto       |./Y90_Seg/name/body-mt-sinai-protocols-abdomen/ax-vibe-post-2art-1min-3min-equ-500|111131.799|500                                                        |AX VIBE POST 2ART,1MIN,3MIN EQU                        |                                                                        |
|9999999                                                                                                                                                                                          |000001|Avanto       |./Y90_Seg/name/body-mt-sinai-protocols-abdomen/ax-vibe-post-2art-1min-3min-equ-20|111316.04|20                                                         |AX VIBE POST 2ART,1MIN,3MIN EQU                        |7                                                                       |
|9999999                                                                                                                                                                                          |000001|Avanto       |./Y90_Seg/name/body-mt-sinai-protocols-abdomen/ax-vibe-post-2art-1min-3min-equ-sub-21|111316.04|21                                                         |AX VIBE POST 2ART,1MIN,3MIN EQU_SUB                    |8                                                                       |
|9999999                                                                                                                                                                                          |000001|Avanto       |./Y90_Seg/name/body-mt-sinai-protocols-abdomen/cor-vibe-post-3-min-22|111407.52|22                                                                                                                                                                                                                                               |000001|Avanto       |./Y90_Seg/name/body-mt-sinai-protocols-abdomen/pace-diffusion-50400800-10113-28|112810.835|28                                                         |PACE Diffusion 50-400-800 10-1-13                      |                                                                        |
|9999999                                                                                                                                                                                          |000001|Avanto       |./Y90_Seg/name/body-mt-sinai-protocols-abdomen/pace-diffusion-50400800-10113-adc-29|112810.835|29                                                         |PACE Diffusion 50-400-800 10-1-13_ADC                  |9                                                                       |
|9999999                                                                                                                                                                                                                                                               



### Convert DICOM to Nifti Using Tagged Metadata Table

Once the table above is properly annotated with the correct tags for the desired series, the second step is conversion.

`python osirix_dicom_to_nifti.py --convertFromTable --tablePath ./path/to/metadata/table.csv --dicomDir ./path/to/folder/containing/study/folders --niftiDir ./path/to/nifti/output/folder`

Study folders within designated nifti output folder will be named according to accession number for study, so conversion of these folder names to random strings using a secure look-up table is encouraged for thorough de-identification.

