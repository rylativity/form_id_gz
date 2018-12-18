# -*- coding: utf-8 -*-
"""
Created on Fri Dec 14 11:04:04 2018

@author: Ryan Stewart

THIS CODE TESTED ON FORM I-9 03/08/13 N
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
with Image(filename="C:\\Users\\Ryan Stewart\\Desktop\\repos\\PDF-Data-Extraction\\I9_filled\\i-9_03-08-13(Filled).pdf", resolution = 300) as img:
    #find the filename
    filename = "C:\\Users\\Ryan Stewart\\Desktop\\repos\\PDF-Data-Extraction\\I9_filled\\i-9_03-08-13(Filled).pdf"
    
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

def process_I9_03_08_13(pages):  
    
    """
    @pages refers to the two pages that must be filled out in this version of the I9
    Takes the two I9 pages and stores the entered information in a dataframe
    """
    page1=pages[0]
    #enhance data
    page1 = enhance(np.array(PIL.Image.open(page1)))
        
    #get height and width
    height, width = page1.shape
    bottom = int(height)
    
    
    ### New Kernel Array for data2 to identify thinner horizontal form lines###
    line_width2 = int(height * .0005)
    kernel_height2 = bottom - line_width2
    kernel_width2 = width - line_width2
    
    #create kernel array to find density of image to find the thinner lines around form boxes
    kernel_array2 = np.full((kernel_height2, kernel_width2), 1).astype('float64')
    for i in range(kernel_height2):
        for j in range(kernel_width2):
            density2 = np.mean(page1[i:i+line_width2, j:j+line_width2])
            #print((i,j), "density:", density)
            kernel_array2[i,j] = density2
    
    #convert all values to 1 (light) that are more than 0.03 above the minimum
    kernel_array2[kernel_array2 > np.min(kernel_array2) + 0.03] = 1
    
    #find rows that contain thin form lines
    row_sums2 = kernel_array2.sum(axis = 1)
    line_rows2 = np.where(row_sums2==np.min(row_sums2))
    
    #group line rows together that represent single lines and identify the bottoms of the lines to orient OCR
    line_groups = [tuple(group) for group in mit.consecutive_groups(line_rows2[0])]
    line_bottoms = [np.max(group) for group in line_groups]
    print(line_bottoms)
    name_top_line = line_bottoms[1]
    address_top_line = line_bottoms[2]
    dob_ss_email_top_line = line_bottoms[3]
    #can use this value to define distance. Won't depend on scale of scanned document
    vertical_standard_scaler = address_top_line - name_top_line
   
    
    
    #Identify vertical dark columns (form edges) and use them to create horizontal scaler for distance
    dark_columns = [i for i,x in enumerate(zip(*page1)) if sum(x) < 2200] ### the first of these can become the anchor column
    side_col_groups = [tuple(group) for group in mit.consecutive_groups(dark_columns)]
    side_cols = [np.max(group) for group in side_col_groups]
    left_form_line, right_form_line = side_cols[0], side_cols[1]
    horizontal_standard_scaler = right_form_line - left_form_line
    
    
    ### Data extraction
    # pull name, address, dob, ss, and contact out by using pytess. to convert image to string and use RE to separate
    name = re.findall("\\n([a-zA-Z0-9_ ]+)", pytesseract.image_to_string(page1[name_top_line:address_top_line]))[0]
    last, first, mid = name.split()[0], name.split()[1], name.split()[2]
    first, last, mid
    
    address = re.findall("\\n([a-zA-Z0-9_ ]+)", pytesseract.image_to_string(page1[address_top_line:dob_ss_email_top_line]))[0]
    city, state, zip_code, street = address.split()[-3], address.split()[-2], address.split()[-1], " ".join(address.split()[:-3])
    
    dob_ss_contact = re.findall("\\n([a-zA-Z0-9\/_\-@. ]+)",pytesseract.image_to_string(page1[dob_ss_email_top_line:line_bottoms[4]]))[0]
    dob = dob_ss_contact.split()[0]
    phone_num = dob_ss_contact.split()[-1]
    email = dob_ss_contact.split()[-2]
    ss = str(pytesseract.image_to_string(page1[dob_ss_email_top_line + int(vertical_standard_scaler*.60465):dob_ss_email_top_line + int(vertical_standard_scaler*.90698), int(left_form_line+horizontal_standard_scaler*.19911):int(left_form_line+horizontal_standard_scaler*0.25289)]) +
             pytesseract.image_to_string(page1[dob_ss_email_top_line + int(vertical_standard_scaler*.60465):dob_ss_email_top_line + int(vertical_standard_scaler*.90698), int(left_form_line+horizontal_standard_scaler*.26444):int(left_form_line+horizontal_standard_scaler*0.29867)]) +
             pytesseract.image_to_string(page1[dob_ss_email_top_line + int(vertical_standard_scaler*.60465):dob_ss_email_top_line + int(vertical_standard_scaler*.90698), int(left_form_line+horizontal_standard_scaler*.31556):int(left_form_line+horizontal_standard_scaler*0.38711)])
             ).replace("‘","")
    
    info_dict = {"first":first,"last":last,"MI":mid,"street":street,"city":city,"state":state,"zip":zip_code,"DOB":dob,"Phone":phone_num,"email":email, "SS":ss}
    
    
    ### Reviewing the Check Boxes
      
    #there are 4 check box options on this version of the form
    boxes = 4
    #resize image
    data2 = page1[dob_ss_email_top_line+int(vertical_standard_scaler*2.58915):dob_ss_email_top_line+int(vertical_standard_scaler*4.68217),left_form_line:left_form_line+int(horizontal_standard_scaler*0.02089)]
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
            info_dict["Alien Reg. # / USCIS #"] = re.findall("[\d\s]{2,}", pytesseract.image_to_string(page1[dob_ss_email_top_line+int(vertical_standard_scaler*3.4341):dob_ss_email_top_line+int(vertical_standard_scaler*3.96124),int(left_form_line+horizontal_standard_scaler*0.57467):int(left_form_line+horizontal_standard_scaler*0.816)]))[0].replace(" ", "")
        elif box == "box4":
            info_dict["work authorization"] = "Auth. Alien"
            info_dict["work auth. expiration date"] = pytesseract.image_to_string(page1[dob_ss_email_top_line+int(vertical_standard_scaler*4.0155):dob_ss_email_top_line+int(vertical_standard_scaler*4.6357),left_form_line+int(horizontal_standard_scaler*0.53644):left_form_line+int(horizontal_standard_scaler*0.68133)])
            info_dict["Alien Reg. # / USCIS #"] = pytesseract.image_to_string(page1[dob_ss_email_top_line+int(vertical_standard_scaler*5.5504):dob_ss_email_top_line+int(vertical_standard_scaler*6.0930),left_form_line+int(horizontal_standard_scaler*0.36711):left_form_line+int(horizontal_standard_scaler*0.60889)])        
            info_dict["Form I-94 Admission Number"] = pytesseract.image_to_string(page1[dob_ss_email_top_line+int(vertical_standard_scaler*6.1163):dob_ss_email_top_line+int(vertical_standard_scaler*7.02326),left_form_line+int(horizontal_standard_scaler*0.27289):left_form_line+int(horizontal_standard_scaler*0.60756)])
            info_dict["Foreign Passport Country"] = pytesseract.image_to_string(page1[dob_ss_email_top_line+int(vertical_standard_scaler*8.7287):dob_ss_email_top_line+int(vertical_standard_scaler*9.33333),left_form_line+int(horizontal_standard_scaler*0.228):left_form_line+int(horizontal_standard_scaler*0.73956)])
            info_dict["Foreign Passport Number"] = pytesseract.image_to_string(page1[dob_ss_email_top_line+int(vertical_standard_scaler*8.1938):dob_ss_email_top_line+int(vertical_standard_scaler*8.6899),left_form_line+int(horizontal_standard_scaler*0.26756):left_form_line+int(horizontal_standard_scaler*0.73956)])
    else:
        info_dict["work authorization"] = "No Box Checked"
    
    info_dict["date signed"] = pytesseract.image_to_string(page1[dob_ss_email_top_line+int(vertical_standard_scaler*10.31008):dob_ss_email_top_line+int(vertical_standard_scaler*10.97674),left_form_line+int(horizontal_standard_scaler*0.83289):left_form_line+int(horizontal_standard_scaler*0.98622)])
    

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