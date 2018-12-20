# -*- coding: utf-8 -*-
"""
Created on Fri Dec 14 11:04:04 2018

@author: Ryan Stewart

THIS CODE TESTED ON FORM I-9 07/17/17
"""
from wand.image import Image
from wand.color import Color
import numpy as np
import io
import PIL
import pytesseract
import re
import more_itertools as mit
import matplotlib.pyplot as plt

"""
for console use

fig,ax = plt.subplots(figsize = (20,20))
plt.imshow(test_data)
plt.grid(b=True, which='major', color = "b")
plt.grid(b=True, which='minor', color = "r")
plt.yscale("linear")

    
def pyt_converter(start_row, end_row, start_col, end_col):
    start_coefficient = (start_row - 731)/380
    end_coefficient = (end_row - 731)/380
    start_coef = (start_col - 175)/2250
    end_coef = (end_col - 175)/2250
    print(f"pytesseract.image_to_string(page2[doc_title_top_line+int(vertical_standard_scaler2*{start_coefficient:.5f}):doc_title_top_line+int(vertical_standard_scaler2*{end_coefficient:.5f}),left_side_col2+int(horizontal_standard_scaler2*{start_coef:.5f}):left_side_col+int(horizontal_standard_scaler2*{end_coef:.5f})])")
"""

images = []
    
#loop through PDF files and convert them to PNG
with Image(filename="C:\\Users\\Ryan Stewart\\Desktop\\repos\\data\\i-9_07-17-17(Filled).pdf", resolution = 300) as img:
    #find the filename
    filename = "C:\\Users\\Ryan Stewart\\Desktop\\repos\\i-9_07-17-17(Filled).pdf"
    
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

def process_I9_07_17_17(pages):  
    
    """
    Takes the single data page form from this version of the I-9 and stores the information as a dictionary
    """
    page1 = pages[0]
    #enhance data
    page1 = enhance(np.array(PIL.Image.open(page1)))
        
    #get height and width
    height, width = page1.shape
    bottom = int(height)
    
    
    #Identify horizontal dark rows and use them to create horizontal scaler for distance
    dark_rows = [i for i,x in enumerate(page1) if sum(x) <400] ### 
    row_groups = [tuple(group) for group in mit.consecutive_groups(dark_rows)]
    rows = [np.max(group) for group in row_groups]
    name_top_line, address_top_line = rows[3], rows[4]
      
    #can use this value to define distance. Won't depend on scale of scanned document
    vertical_standard_scaler = address_top_line - name_top_line
   
    
    
    #Identify vertical dark columns (form edges) and use them to create horizontal scaler for distance
    dark_columns = [i for i,x in enumerate(zip(*page1)) if sum(x) < 2300] ### 
    side_col_groups = [tuple(group) for group in mit.consecutive_groups(dark_columns)]
    side_cols = [np.max(group) for group in side_col_groups]
    left_side_col, right_side_col = side_cols[0], side_cols[-1]
    horizontal_standard_scaler = right_side_col - left_side_col
    
    
    ### Data extraction
    # Section 1
    # pull name, address, dob, ss, and contact out by using pytess. to convert image to string and use RE to separate
    info_dict = {}
    info_dict["Last_Name"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*-0.64286):address_top_line+int(vertical_standard_scaler*-0.00794),left_side_col+int(horizontal_standard_scaler*0.00000):left_side_col+int(horizontal_standard_scaler*0.31699)])
    info_dict["First_Name"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*-0.64286):address_top_line+int(vertical_standard_scaler*-0.00794),left_side_col+int(horizontal_standard_scaler*0.31966):left_side_col+int(horizontal_standard_scaler*0.59652)])
    info_dict["MI"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*-0.64286):address_top_line+int(vertical_standard_scaler*-0.00794),left_side_col+int(horizontal_standard_scaler*0.59831):left_side_col+int(horizontal_standard_scaler*0.71244)])
    info_dict["Other_Last_Name"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*-0.64286):address_top_line+int(vertical_standard_scaler*-0.00794),left_side_col+int(horizontal_standard_scaler*0.71422):left_side_col+int(horizontal_standard_scaler*0.99955)])
    info_dict["Street"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*0.34921):address_top_line+int(vertical_standard_scaler*0.97619),left_side_col+int(horizontal_standard_scaler*0.00000):left_side_col+int(horizontal_standard_scaler*0.37896)])
    info_dict["Apt"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*0.34921):address_top_line+int(vertical_standard_scaler*0.97619),left_side_col+int(horizontal_standard_scaler*0.38519):left_side_col+int(horizontal_standard_scaler*0.49086)])
    info_dict["City"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*0.34921):address_top_line+int(vertical_standard_scaler*0.97619),left_side_col+int(horizontal_standard_scaler*0.49264):left_side_col+int(horizontal_standard_scaler*0.76995)])
    info_dict["State"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*0.34921):address_top_line+int(vertical_standard_scaler*0.97619),left_side_col+int(horizontal_standard_scaler*0.77352):left_side_col+int(horizontal_standard_scaler*0.84084)])
    info_dict["Zip"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*0.34921):address_top_line+int(vertical_standard_scaler*0.97619),left_side_col+int(horizontal_standard_scaler*0.84307):left_side_col+int(horizontal_standard_scaler*0.99955)])
    info_dict["DOB"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*1.34127):address_top_line+int(vertical_standard_scaler*2.09524),left_side_col+int(horizontal_standard_scaler*0.00000):left_side_col+int(horizontal_standard_scaler*0.20820)])
    info_dict["SSN"] = "".join(re.findall("\d+",pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*1.55556):address_top_line+int(vertical_standard_scaler*2.04762),left_side_col+int(horizontal_standard_scaler*0.21801):left_side_col+int(horizontal_standard_scaler*0.42131)])))
    info_dict["Email"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*1.34127):address_top_line+int(vertical_standard_scaler*2.09524),left_side_col+int(horizontal_standard_scaler*0.43112):left_side_col+int(horizontal_standard_scaler*0.74855)])
    info_dict["Phone"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*1.34127):address_top_line+int(vertical_standard_scaler*2.09524),left_side_col+int(horizontal_standard_scaler*0.75212):left_side_col+int(horizontal_standard_scaler*0.99955)])
    ### Reviewing the Check Boxes
      
    #there are 4 check box options on this version of the form
    boxes = 4
    #resize image
    data2 = page1[address_top_line+int(vertical_standard_scaler*3.81746):address_top_line+int(vertical_standard_scaler*5.83333),left_side_col+int(horizontal_standard_scaler*0.00535):left_side_col+int(horizontal_standard_scaler*0.02630)]
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
            info_dict["Alien Reg. # / USCIS #"] = re.findall("[\d\s]{2,}", pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*4.81746):address_top_line+int(vertical_standard_scaler*5.27778),left_side_col+int(horizontal_standard_scaler*0.57557):left_side_col+int(horizontal_standard_scaler*0.75123)]))[0]
        elif box == "box4":
            info_dict["work authorization"] = "Auth. Alien"
            info_dict["Alien Reg. # / USCIS #"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*6.97619):address_top_line+int(vertical_standard_scaler*7.65079),left_side_col+int(horizontal_standard_scaler*0.34819):left_side_col+int(horizontal_standard_scaler*0.60901)])        
            info_dict["Alien auth. expiration"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*5.40476):address_top_line+int(vertical_standard_scaler*5.85714),left_side_col+int(horizontal_standard_scaler*0.58761):left_side_col+int(horizontal_standard_scaler*0.71690)])
            info_dict["I-94 Adm. #"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*7.68254):address_top_line+int(vertical_standard_scaler*8.49206),left_side_col+int(horizontal_standard_scaler*0.25011):left_side_col+int(horizontal_standard_scaler*0.60678)])
            info_dict["Foreign Passp. #"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*8.53175):address_top_line+int(vertical_standard_scaler*9.31746),left_side_col+int(horizontal_standard_scaler*0.22916):left_side_col+int(horizontal_standard_scaler*0.61079)])
            info_dict["Foreign Passp. Country"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*9.35714):address_top_line+int(vertical_standard_scaler*9.87302),left_side_col+int(horizontal_standard_scaler*0.19215):left_side_col+int(horizontal_standard_scaler*0.60767)])
        else:   
            info_dict["work authorization"] = "No Box Checked"
    
    #info_dict["date signed"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*4.78151):address_top_line+int(vertical_standard_scaler*5.44538),middle_sect1_line+int(horizontal_standard_scaler*0.67652):middle_sect1_line+int(horizontal_standard_scaler*1.35675)])
    
    info_dict["Preparer/Transl. Last Name"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*14.73810):address_top_line+int(vertical_standard_scaler*15.13492),left_side_col+int(horizontal_standard_scaler*0.00312):left_side_col+int(horizontal_standard_scaler*0.52296)])
    info_dict["Preparer/Transl. First Name"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*14.73810):address_top_line+int(vertical_standard_scaler*15.13492),left_side_col+int(horizontal_standard_scaler*0.52742):left_side_col+int(horizontal_standard_scaler*0.99911)])
    info_dict["Preparer Street"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*15.65079):address_top_line+int(vertical_standard_scaler*16.12698),left_side_col+int(horizontal_standard_scaler*0.00312):left_side_col+int(horizontal_standard_scaler*0.47659)])
    info_dict["Preparer City"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*15.65079):address_top_line+int(vertical_standard_scaler*16.12698),left_side_col+int(horizontal_standard_scaler*0.48016):left_side_col+int(horizontal_standard_scaler*0.77129)])
    info_dict["Preparer State"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*15.65079):address_top_line+int(vertical_standard_scaler*16.12698),left_side_col+int(horizontal_standard_scaler*0.77486):left_side_col+int(horizontal_standard_scaler*0.84351)])
    info_dict["Preparer Zip"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*15.65079):address_top_line+int(vertical_standard_scaler*16.12698),left_side_col+int(horizontal_standard_scaler*0.84708):left_side_col+int(horizontal_standard_scaler*0.99911)])
    
    
    
    
    #### Page 2
    page2 = pages[1]
    page2 = enhance(np.array(PIL.Image.open(page2)))
    
        #get height and width
    height, width = page1.shape
    bottom = int(height)
    
    
    #Identify horizontal dark rows and use them to create horizontal scaler for distance
    dark_rows2 = [i for i,x in enumerate(page2) if sum(x) <400] ### 
    row_groups2 = [tuple(group) for group in mit.consecutive_groups(dark_rows2)]
    rows2 = [np.max(group) for group in row_groups2]
    doc_title_top_line, sect2_top_line = rows2[4], rows2[1]
    
    #can use this value to define distance. Won't depend on scale of scanned document
    vertical_standard_scaler2 = doc_title_top_line - sect2_top_line
    
    
    #Identify vertical dark columns (form edges) and use them to create horizontal scaler for distance
    dark_columns2 = [i for i,x in enumerate(zip(*page2)) if sum(x) < 2300] ### 
    side_col_groups2 = [tuple(group) for group in mit.consecutive_groups(dark_columns2)]
    side_cols2 = [np.max(group) for group in side_col_groups2]
    left_side_col2, right_side_col2 = side_cols2[0], side_cols2[-1]
    horizontal_standard_scaler2 = right_side_col2 - left_side_col2
    
    
    
    
    
    #Section 2
    
    info_dict["List A Document"] = pytesseract.image_to_string(page2[doc_title_top_line+int(vertical_standard_scaler2*0.08947):doc_title_top_line+int(vertical_standard_scaler2*0.22895),left_side_col2+int(horizontal_standard_scaler2*0.00178):left_side_col+int(horizontal_standard_scaler2*0.32000)])
    info_dict["List B Document"] = pytesseract.image_to_string(page2[doc_title_top_line+int(vertical_standard_scaler2*0.08947):doc_title_top_line+int(vertical_standard_scaler2*0.22895),left_side_col2+int(horizontal_standard_scaler2*0.33911):left_side_col+int(horizontal_standard_scaler2*0.66133)])
    info_dict["List C Document"] = pytesseract.image_to_string(page2[doc_title_top_line+int(vertical_standard_scaler2*0.08947):doc_title_top_line+int(vertical_standard_scaler2*0.22895),left_side_col2+int(horizontal_standard_scaler2*0.67556):left_side_col+int(horizontal_standard_scaler2*0.99822)])
     
    info_dict["Iss. Authority (A)"] = pytesseract.image_to_string(page2[doc_title_top_line+int(vertical_standard_scaler2*0.33421):doc_title_top_line+int(vertical_standard_scaler2*0.47368),left_side_col2+int(horizontal_standard_scaler2*0.00178):left_side_col+int(horizontal_standard_scaler2*0.32000)])
    info_dict["Iss. Authority (B)"] = pytesseract.image_to_string(page2[doc_title_top_line+int(vertical_standard_scaler2*0.33421):doc_title_top_line+int(vertical_standard_scaler2*0.47368),left_side_col2+int(horizontal_standard_scaler2*0.33911):left_side_col+int(horizontal_standard_scaler2*0.66133)])
    info_dict["Iss. Authority (C)"] = pytesseract.image_to_string(page2[doc_title_top_line+int(vertical_standard_scaler2*0.33421):doc_title_top_line+int(vertical_standard_scaler2*0.47368),left_side_col2+int(horizontal_standard_scaler2*0.67556):left_side_col+int(horizontal_standard_scaler2*0.99822)])
     
    info_dict["Doc. # (A)"] = pytesseract.image_to_string(page2[doc_title_top_line+int(vertical_standard_scaler2*0.57105):doc_title_top_line+int(vertical_standard_scaler2*0.71316),left_side_col2+int(horizontal_standard_scaler2*0.00178):left_side_col+int(horizontal_standard_scaler2*0.32000)])
    info_dict["Doc. # (B)"] = pytesseract.image_to_string(page2[doc_title_top_line+int(vertical_standard_scaler2*0.57105):doc_title_top_line+int(vertical_standard_scaler2*0.71316),left_side_col2+int(horizontal_standard_scaler2*0.33911):left_side_col+int(horizontal_standard_scaler2*0.66133)])
    info_dict["Doc. # (C)"] = pytesseract.image_to_string(page2[doc_title_top_line+int(vertical_standard_scaler2*0.57105):doc_title_top_line+int(vertical_standard_scaler2*0.71316),left_side_col2+int(horizontal_standard_scaler2*0.67556):left_side_col+int(horizontal_standard_scaler2*0.99822)])
    
    info_dict["Doc. Expir. (A)"] = pytesseract.image_to_string(page2[doc_title_top_line+int(vertical_standard_scaler2*0.81842):doc_title_top_line+int(vertical_standard_scaler2*0.97632),left_side_col2+int(horizontal_standard_scaler2*0.00178):left_side_col+int(horizontal_standard_scaler2*0.32000)])
    info_dict["Doc. Expir. (B)"] = pytesseract.image_to_string(page2[doc_title_top_line+int(vertical_standard_scaler2*0.81842):doc_title_top_line+int(vertical_standard_scaler2*0.97632),left_side_col2+int(horizontal_standard_scaler2*0.33911):left_side_col+int(horizontal_standard_scaler2*0.66133)])
    info_dict["Doc. Expir. (C)"] = pytesseract.image_to_string(page2[doc_title_top_line+int(vertical_standard_scaler2*0.81842):doc_title_top_line+int(vertical_standard_scaler2*0.97632),left_side_col2+int(horizontal_standard_scaler2*0.67556):left_side_col+int(horizontal_standard_scaler2*0.99822)])
    
    
    info_dict["Employ. Start Date"] = pytesseract.image_to_string(page2[doc_title_top_line+int(vertical_standard_scaler2*3.38947):doc_title_top_line+int(vertical_standard_scaler2*3.53947),left_side_col2+int(horizontal_standard_scaler2*0.45911):left_side_col+int(horizontal_standard_scaler2*0.60578)])
    info_dict["Verifier Last Name"] = pytesseract.image_to_string(page2[doc_title_top_line+int(vertical_standard_scaler2*4.01842):doc_title_top_line+int(vertical_standard_scaler2*4.17895),left_side_col2+int(horizontal_standard_scaler2*0.00133):left_side_col+int(horizontal_standard_scaler2*0.33822)])
    info_dict["Verifier First Name"] = pytesseract.image_to_string(page2[doc_title_top_line+int(vertical_standard_scaler2*4.01842):doc_title_top_line+int(vertical_standard_scaler2*4.17895),left_side_col2+int(horizontal_standard_scaler2*0.34133):left_side_col+int(horizontal_standard_scaler2*0.67467)])
    info_dict["Verifier Title"] = pytesseract.image_to_string(page2[doc_title_top_line+int(vertical_standard_scaler2*3.72632):doc_title_top_line+int(vertical_standard_scaler2*3.88684),left_side_col2+int(horizontal_standard_scaler2*0.63733):left_side_col+int(horizontal_standard_scaler2*0.99067)])
    info_dict["Business Name"] = pytesseract.image_to_string(page2[doc_title_top_line+int(vertical_standard_scaler2*4.01842):doc_title_top_line+int(vertical_standard_scaler2*4.17895),left_side_col2+int(horizontal_standard_scaler2*0.68089):left_side_col+int(horizontal_standard_scaler2*0.99600)])
    info_dict["Business Street"] = pytesseract.image_to_string(page2[doc_title_top_line+int(vertical_standard_scaler2*4.28684):doc_title_top_line+int(vertical_standard_scaler2*4.47368),left_side_col2+int(horizontal_standard_scaler2*0.00178):left_side_col+int(horizontal_standard_scaler2*0.50533)])
    info_dict["Business City"] = pytesseract.image_to_string(page2[doc_title_top_line+int(vertical_standard_scaler2*4.28684):doc_title_top_line+int(vertical_standard_scaler2*4.47368),left_side_col2+int(horizontal_standard_scaler2*0.50844):left_side_col+int(horizontal_standard_scaler2*0.75511)])
    info_dict["Business State"] = pytesseract.image_to_string(page2[doc_title_top_line+int(vertical_standard_scaler2*4.28684):doc_title_top_line+int(vertical_standard_scaler2*4.47368),left_side_col2+int(horizontal_standard_scaler2*0.75778):left_side_col+int(horizontal_standard_scaler2*0.82133)])
    info_dict["Business Zip"] = pytesseract.image_to_string(page2[doc_title_top_line+int(vertical_standard_scaler2*4.28684):doc_title_top_line+int(vertical_standard_scaler2*4.47368),left_side_col2+int(horizontal_standard_scaler2*0.82667):left_side_col+int(horizontal_standard_scaler2*0.97378)])
    
    
    #Section 3
    info_dict["Date Rehired"] = pytesseract.image_to_string(page2[doc_title_top_line+int(vertical_standard_scaler2*4.93421):doc_title_top_line+int(vertical_standard_scaler2*5.10000),left_side_col2+int(horizontal_standard_scaler2*0.66889):left_side_col+int(horizontal_standard_scaler2*0.97378)])
    info_dict["Reverif. Doc. Type"] = pytesseract.image_to_string(page2[doc_title_top_line+int(vertical_standard_scaler2*5.50526):doc_title_top_line+int(vertical_standard_scaler2*5.67368),left_side_col2+int(horizontal_standard_scaler2*0.00222):left_side_col+int(horizontal_standard_scaler2*0.44622)])
    info_dict["Reverif. Doc. Num."] = pytesseract.image_to_string(page2[doc_title_top_line+int(vertical_standard_scaler2*5.50526):doc_title_top_line+int(vertical_standard_scaler2*5.67368),left_side_col2+int(horizontal_standard_scaler2*0.44978):left_side_col+int(horizontal_standard_scaler2*0.73644)])
    info_dict["Reverif. Doc. Exp."] = pytesseract.image_to_string(page2[doc_title_top_line+int(vertical_standard_scaler2*5.50526):doc_title_top_line+int(vertical_standard_scaler2*5.67368),left_side_col2+int(horizontal_standard_scaler2*0.74000):left_side_col+int(horizontal_standard_scaler2*0.97378)])
    """
    return info_dict


    
