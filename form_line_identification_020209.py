# -*- coding: utf-8 -*-
"""
Created on Fri Dec 14 11:04:04 2018

@author: Ryan Stewart

THIS CODE TESTED ON FORM I-9 02/02/09
"""
from wand.image import Image
from wand.color import Color
import numpy as np
import pandas as pd
import io
import PIL
import pytesseract
import re
import more_itertools as mit


images = []
    
#loop through PDF files and convert them to PNG
with Image(filename="C:\\Users\\Ryan Stewart\\Desktop\\repos\\PDF-Data-Extraction\\I9_filled\\i-9_02-02-09(Filled).pdf", resolution = 300) as img:
    #find the filename
    filename = "C:\\Users\\Ryan Stewart\\Desktop\\repos\\PDF-Data-Extraction\\I9_filled\\i-9_02-02-09(Filled).pdf"
    
    #loop through pages of PDF
    for i, page in enumerate(img.sequence):
        with Image(page) as im:
            im.alpha_channel = False
            im.background_color = Color('white')
            im.format = 'png'
    
            swapPNG = io.BytesIO()
            im.save(swapPNG)
            images.append(swapPNG)

def scale(array):
    max = array.max()
    return(array/max)
    
###some image inverted the black and white pixels, function to tranform back
def invert(array):
    return(abs(1-array))

def enhance(data):
    '''
    @data an image array
    Takes an image array, scales it to a 0-1 scale, inverts the pixels if it is 
    predominantly dark pixels, converts it to a 2D image, and then converts 
    all pixels above .5 to 1 and all below .5 to 0, to enhance image resolution.
    '''
    data = scale(data)
    #convert to 2 dimensions if 3-dimensional
    if len(data.shape) > 2:
        data = data[:,:,2]
    #if color scheme is inverted, convert it back
    if np.mean(data) < 0.5:
        data = invert(data)
    data[data >= 0.7] = 1
    data[data < 0.7] = 0
    return(data)

def process_I9_02_02_09(page):  
    
    """
    Takes the single data page form from this version of the I-9 and stores the information as a dictionary
    """
    page1 = page
    #enhance data
    page1 = enhance(np.array(PIL.Image.open(page1)))
        
    #get height and width
    height, width = page1.shape
    bottom = int(height)
    
    
    #Identify horizontal dark rows and use them to create horizontal scaler for distance
    dark_rows = [i for i,x in enumerate(test_data) if sum(x) <400] ### 
    row_groups = [tuple(group) for group in mit.consecutive_groups(dark_rows)]
    rows = [np.max(group) for group in row_groups]
    name_top_line, address_top_line = rows[3], rows[4]
    vertical_standard_scaler = address_top_line - name_top_line
    
    #group line rows together that represent single lines and identify the bottoms of the lines to orient OCR
    line_groups = [tuple(group) for group in mit.consecutive_groups(line_rows2[0])]
    line_bottoms = [np.max(group) for group in line_groups]
    print(line_bottoms)

    #can use this value to define distance. Won't depend on scale of scanned document
    vertical_standard_scaler = address_top_line - name_top_line
   
    
    
    #Identify vertical dark columns (form edges) and use them to create horizontal scaler for distance
    dark_columns = [i for i,x in enumerate(zip(*page1)) if sum(x) < 2650] ### 
    side_col_groups = [tuple(group) for group in mit.consecutive_groups(dark_columns)]
    side_cols = [np.max(group) for group in side_col_groups]
    middle_sect1_line, right_sect1_line = side_cols[-2], side_cols[-1]
    horizontal_standard_scaler = right_sect1_line - middle_sect1_line
    
    
    ### Data extraction
    # pull name, address, dob, ss, and contact out by using pytess. to convert image to string and use RE to separate
    name = re.findall("\\n([a-zA-Z0-9_ ]+)", pytesseract.image_to_string(page1[name_top_line:address_top_line]))[0]
    last, first, mid = name.split()[0], name.split()[1], name.split()[2]
    try:
        maiden = name.split()[3]
    except:
        pass
    
    
    street = re.findall("\\n([a-zA-Z0-9_ ]+)", pytesseract.image_to_string(page1[address_top_line:address_top_line+int(vertical_standard_scaler*1.0),middle_sect1_line - int(horizontal_standard_scaler*1.97227):middle_sect1_line+int(horizontal_standard_scaler*1.0)]))[0]
    dob = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*0.30252):address_top_line+int(vertical_standard_scaler*0.96639),middle_sect1_line+int(horizontal_standard_scaler*1.00739):middle_sect1_line+int(horizontal_standard_scaler*1.63586)])
    loc_box = page1[address_top_line+int(vertical_standard_scaler*1.0084):address_top_line+int(vertical_standard_scaler*1.94958),middle_sect1_line - int(horizontal_standard_scaler*1.9722):middle_sect1_line+int(horizontal_standard_scaler*.8)]
    loc = re.findall("\\n([a-zA-Z0-9_ ]+)", pytesseract.image_to_string(loc_box))[0]
    zip_code = loc.split()[-1]
    city = loc.split()[0]
    state = loc.split()[1]
    ss = re.findall("\\n([a-zA-Z0-9_ ]+)", pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*1.0084):address_top_line+int(vertical_standard_scaler*1.94958),middle_sect1_line+int(horizontal_standard_scaler*0.05):middle_sect1_line+int(horizontal_standard_scaler*2.18854)]))[0]
    
    info_dict = {"first":first,"last":last,"MI":mid,"street":street,"city":city,"state":state,"zip":zip_code,"DOB":dob, "SS":ss}
    
    
    ### Reviewing the Check Boxes
      
    #there are 4 check box options on this version of the form
    boxes = 4
    #resize image
    data2 = page1[address_top_line+int(vertical_standard_scaler*2.48739):address_top_line+int(vertical_standard_scaler*4.36134),middle_sect1_line+int(horizontal_standard_scaler*0.08133):middle_sect1_line+int(horizontal_standard_scaler*0.16451)]
    #scale to 0-1 scale
    data2 = scale(data2)
    #find the height of the image to divide it
    width2 = data2.shape[0]
    #create empty dicts to store values
    crops = {}
    means = {}
    #add the crop arrays and their means
    for i in range(4):
        crops["box" + str(i + 1)] = data2[int(width2/boxes)*i:int(width2/boxes)*(i+1),:]
        means["box" + str(i + 1)] = crops["box" + str(i + 1)].mean()
    #find the maximum and minimum value from the dict and the range
    key_max = max(means.keys(), key=(lambda k: means[k]))
    key_min = min(means.keys(), key=(lambda k: means[k]))
    value_max = means[key_max]
    value_min = means[key_min]
    value_range = value_max - value_min 
    
    #assign the box and translate the value to work auth status
    if value_range > 0.025:
        box =  (min(means, key = means.get))
        if box == "box1":
            info_dict["work authorization"] = "US Citizen"
        elif box == "box2":
            info_dict["work authorization"] = "Non-Cit. National"
        #if box 3 checked, look for Alien Auth Number
        elif box == "box3":
            info_dict["work authorization"] = "Lawful Perm. Resident"
            info_dict["Alien Reg. # / USCIS #"] = re.findall("[\d\s]{2,}", pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*3.30252):address_top_line+int(vertical_standard_scaler*3.83193),int(middle_sect1_line+horizontal_standard_scaler*1.19409):int(middle_sect1_line+horizontal_standard_scaler*2.16266)]))[0]
        elif box == "box4":
            info_dict["work authorization"] = "Auth. Alien"
            info_dict["Alien Reg. # / USCIS #"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*3.88235):address_top_line+int(vertical_standard_scaler*4.30252),middle_sect1_line+int(horizontal_standard_scaler*1.58041):middle_sect1_line+int(horizontal_standard_scaler*2.14787)])        
            info_dict["Alien auth. expiration"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*4.35294):address_top_line+int(vertical_standard_scaler*4.73109),middle_sect1_line+int(horizontal_standard_scaler*1.58201):middle_sect1_line+int(horizontal_standard_scaler*2.14770)])
        else:   
            info_dict["work authorization"] = "No Box Checked"
    
    info_dict["date signed"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*4.78151):address_top_line+int(vertical_standard_scaler*5.44538),middle_sect1_line+int(horizontal_standard_scaler*0.67652):middle_sect1_line+int(horizontal_standard_scaler*1.35675)])
    return info_dict
"""
#### Page 2
    page2 = pages[1]
    
        #enhance data
    page2 = enhance(np.array(PIL.Image.open(page2)))
        
    #get height and width
    height, width = page2.shape
    bottom = int(height)
    
    
    ### New Kernel Array for data2 to identify thinner horizontal form lines###
    line_width3 = int(height * .0005)
    kernel_height3 = bottom - line_width3
    kernel_width3 = width - line_width3
    
    #create kernel array to find density of image to find the thinner lines around form boxes
    kernel_array3 = np.full((kernel_height3, kernel_width3), 1).astype('float64')
    for i in range(kernel_height3):
        for j in range(kernel_width3):
            density3 = np.mean(page2[i:i+line_width3, j:j+line_width3])
            #print((i,j), "density:", density)
            kernel_array3[i,j] = density3
    
    #convert all values to 1 (light) that are more than 0.03 above the minimum
    kernel_array3[kernel_array3 > np.min(kernel_array3) + 0.03] = 1
    
    #find rows that contain thin form lines
    row_sums3 = kernel_array3.sum(axis = 1)
    line_rows3 = np.where(row_sums3==np.min(row_sums3))
    
    #group line rows together that represent single lines and identify the bottoms of the lines to orient OCR
    line_groups2 = [tuple(group) for group in mit.consecutive_groups(line_rows3[0])]
    line_bottoms2 = [np.max(group) for group in line_groups2]
    print(line_bottoms2)
    
    doc_info_top_line = line_bottoms2[2]
    vertical_standard_scaler2 = doc_info_top_line-line_bottoms2[0]
    
    #Identify vertical dark columns (form edges) and use them to create horizontal scaler for distance
    dark_columns2 = [i for i,x in enumerate(zip(*page2)) if sum(x) < 2200] ### the first of these can become the anchor column
    side_col_groups2 = [tuple(group) for group in mit.consecutive_groups(dark_columns2)]
    side_cols2 = [np.max(group) for group in side_col_groups2]
    left_form_line2, right_form_line2 = side_cols2[0], side_cols2[-1]
    horizontal_standard_scaler2 = right_form_line2 - left_form_line2
    
    
    #Pull document information
    info_dict["Document Title"] = re.findall("\\n([a-zA-Z0-9\/_\-@. ]+)", pytesseract.image_to_string(page2[doc_info_top_line:doc_info_top_line+int(vertical_standard_scaler2*0.43655),left_form_line2:right_form_line2]))[0]
    info_dict["Issuing Authority"] = re.findall("\\n([a-zA-Z0-9\/_\-@. ]+)", pytesseract.image_to_string(page2[doc_info_top_line+int(vertical_standard_scaler2*0.45685):doc_info_top_line+int(vertical_standard_scaler2*0.88325),left_form_line2:right_form_line2]))[0]
    info_dict["Document Number"] = re.findall("\\n([a-zA-Z0-9\/_\-@. ]+)", pytesseract.image_to_string(page2[doc_info_top_line+int(vertical_standard_scaler2*0.90355):doc_info_top_line+int(vertical_standard_scaler2*1.35025),left_form_line2:right_form_line2]))[0]
    info_dict["Expiration Date"] = re.findall("\\n([a-zA-Z0-9\/_\-@. ]+)", pytesseract.image_to_string(page2[doc_info_top_line+int(vertical_standard_scaler2*1.37056):doc_info_top_line+int(vertical_standard_scaler2*1.86802),left_form_line2:right_form_line2]))[0]
    return info_dict
    """