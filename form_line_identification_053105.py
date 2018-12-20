# -*- coding: utf-8 -*-
"""
Created on Fri Dec 14 11:04:04 2018

@author: Ryan Stewart

THIS CODE TESTED ON FORM I-9 05/31/05
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

def vertical_converter(start_row, end_row):
    start_coefficient = (start_row - 623)/106
    end_coefficient = (end_row - 623)/106
    print(f"Start: address_top_line+int(vertical_standard_scaler*{start_coefficient:.5f})")
    print(f"End: address_top_line+int(vertical_standard_scaler*{end_coefficient:.5f})")

def horizontal_converter(start_col, end_col):
    start_coef = (start_col - 1215)/541
    end_coef = (end_col - 1215)/541
    print(f"Start: left_form_edge+int(horizontal_standard_scaler*{start_coef:.5f})")
    print(f"End: left_form_edge+int(horizontal_standard_scaler*{end_coef:.5f})")
    
def pyt_converter(start_row, end_row, start_col, end_col):
    start_coefficient = (start_row - 623)/106
    end_coefficient = (end_row - 623)/106
    start_coef = (start_col - 128)/1599
    end_coef = (end_col - 128)/1599
    print(f"pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*{start_coefficient:.5f}):address_top_line+int(vertical_standard_scaler*{end_coefficient:.5f}),left_form_edge+int(horizontal_standard_scaler*{start_coef:.5f}):left_form_edge+int(horizontal_standard_scaler*{end_coef:.5f})])")
"""

images = []
    
#loop through PDF files and convert them to PNG
with Image(filename="C:\\Users\\Ryan Stewart\\Desktop\\repos\\data\\i-9_05-31-05(Filled).pdf", resolution = 300) as img:
    #find the filename
    filename = "C:\\Users\\Ryan Stewart\\Desktop\\repos\\i-9_05-31-05(Filled).pdf"
    
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

def process_I9_05_31_05(page):  
    
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
    dark_rows = [i for i,x in enumerate(page1) if sum(x) <width*.15686] ### 
    row_groups = [tuple(group) for group in mit.consecutive_groups(dark_rows)]
    rows = [np.max(group) for group in row_groups]
    name_top_line, address_top_line = rows[3], rows[4]
    vertical_standard_scaler = address_top_line - name_top_line


    #can use this value to define distance. Won't depend on scale of scanned document
    vertical_standard_scaler = address_top_line - name_top_line
   
    
    
    #Identify vertical dark columns (form edges) and use them to create horizontal scaler for distance
    dark_columns = [i for i,x in enumerate(zip(*page1)) if sum(x) < height*.80] ### 
    side_col_groups = [tuple(group) for group in mit.consecutive_groups(dark_columns)]
    side_cols = [np.min(group) for group in side_col_groups]
    left_form_edge, right_sect1_line = side_cols[0], side_cols[-1]
    horizontal_standard_scaler = right_sect1_line - left_form_edge
    
    
     ### Data extraction
    date_pyt_config = "-c tessedit_char_whitelist=0123456789/- -psm 6"
    # Section 1
    # pull name, address, dob, ss, and contact out by using pytess
    info_dict = {}
    info_dict["First Name"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*-0.64151):address_top_line+int(vertical_standard_scaler*-0.03774),left_form_edge+int(horizontal_standard_scaler*0.49593):left_form_edge+int(horizontal_standard_scaler*0.74797)])
    info_dict["Last Name"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*-0.64151):address_top_line+int(vertical_standard_scaler*-0.03774),left_form_edge+int(horizontal_standard_scaler*-0.00500):left_form_edge+int(horizontal_standard_scaler*0.42026)])
    info_dict["MI"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*-0.64151):address_top_line+int(vertical_standard_scaler*-0.03774),left_form_edge+int(horizontal_standard_scaler*0.82989):left_form_edge+int(horizontal_standard_scaler*0.99812)], config = "-psm 10")
    info_dict["Maiden Name"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*-0.64151):address_top_line+int(vertical_standard_scaler*-0.03774),left_form_edge+int(horizontal_standard_scaler*1.00375):left_form_edge+int(horizontal_standard_scaler*1.44465)])
    info_dict["Street"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*0.40566):address_top_line+int(vertical_standard_scaler*0.97170),left_form_edge+int(horizontal_standard_scaler*-0.00500):left_form_edge+int(horizontal_standard_scaler*0.74797)])
    info_dict["Apt"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*0.40566):address_top_line+int(vertical_standard_scaler*0.97170),left_form_edge+int(horizontal_standard_scaler*0.82989):left_form_edge+int(horizontal_standard_scaler*0.99812)])
    info_dict["DOB"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*0.42453):address_top_line+int(vertical_standard_scaler*0.97170),left_form_edge+int(horizontal_standard_scaler*1.00375):left_form_edge+int(horizontal_standard_scaler*1.44465)])
    info_dict["City"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*1.33075):address_top_line+int(vertical_standard_scaler*1.90566),left_form_edge+int(horizontal_standard_scaler*-0.00500):left_form_edge+int(horizontal_standard_scaler*0.43590)])
    info_dict["State"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*1.33962):address_top_line+int(vertical_standard_scaler*1.90566),left_form_edge+int(horizontal_standard_scaler*0.45779):left_form_edge+int(horizontal_standard_scaler*0.74797)])
    info_dict["Zip"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*1.33962):address_top_line+int(vertical_standard_scaler*1.90566),left_form_edge+int(horizontal_standard_scaler*0.82989):left_form_edge+int(horizontal_standard_scaler*0.99812)])
    info_dict["SSN"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*1.33962):address_top_line+int(vertical_standard_scaler*1.90566),left_form_edge+int(horizontal_standard_scaler*1.00375):left_form_edge+int(horizontal_standard_scaler*1.44465)])
    
    
    
    ### Reviewing the Check Boxes
      
    #there are 4 check box options on this version of the form
    boxes = 4
    #resize image
    data2 = page1[address_top_line+int(vertical_standard_scaler*2.33962):address_top_line+int(vertical_standard_scaler*3.98113),left_form_edge+int(horizontal_standard_scaler*0.74547):left_form_edge+int(horizontal_standard_scaler*0.77048)]
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
            info_dict["work authorization"] = "US National"
        elif box == "box3":
            info_dict["work authorization"] = "Lawful Perm. Resident"
            info_dict["Alien Reg. # / USCIS #"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*3.11321):address_top_line+int(vertical_standard_scaler*3.51887),left_form_edge+int(horizontal_standard_scaler*1.16635):left_form_edge+int(horizontal_standard_scaler*1.45216)])
        elif box == "box4":
            info_dict["work authorization"] = "Auth. Alien"
            info_dict["Alien Reg. # / USCIS #"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*3.98113):address_top_line+int(vertical_standard_scaler*4.30189),left_form_edge+int(horizontal_standard_scaler*1.01313):left_form_edge+int(horizontal_standard_scaler*1.45091)])
            info_dict["Alien auth. expiration"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*3.53774):address_top_line+int(vertical_standard_scaler*3.93396),left_form_edge+int(horizontal_standard_scaler*1.09193):left_form_edge+int(horizontal_standard_scaler*1.24578)])
        else:   
            info_dict["work authorization"] = "No Box Checked"
    
    info_dict["Perparer/Transl. Name"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*6.87736):address_top_line+int(vertical_standard_scaler*7.26415),left_form_edge+int(horizontal_standard_scaler*0.73984):left_form_edge+int(horizontal_standard_scaler*1.32333)])
    info_dict["Perparer/Transl. Address"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*7.65094):address_top_line+int(vertical_standard_scaler*8.21698),left_form_edge+int(horizontal_standard_scaler*-0.01001):left_form_edge+int(horizontal_standard_scaler*0.99812)])
    #Section 2
    
    info_dict["List A Document"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*10.09434):address_top_line+int(vertical_standard_scaler*10.67925),left_form_edge+int(horizontal_standard_scaler*0.14634):left_form_edge+int(horizontal_standard_scaler*0.45591)])
    info_dict["List B Document"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*10.09434):address_top_line+int(vertical_standard_scaler*10.65094),left_form_edge+int(horizontal_standard_scaler*0.52971):left_form_edge+int(horizontal_standard_scaler*0.89493)])
    info_dict["List C Document"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*10.09434):address_top_line+int(vertical_standard_scaler*10.67925),left_form_edge+int(horizontal_standard_scaler*1.03627):left_form_edge+int(horizontal_standard_scaler*1.44903)])
     
    info_dict["Iss. Authority (A)"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*10.73585):address_top_line+int(vertical_standard_scaler*11.38679),left_form_edge+int(horizontal_standard_scaler*0.16448):left_form_edge+int(horizontal_standard_scaler*0.45591)])
    info_dict["Iss. Authority (B)"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*10.73585):address_top_line+int(vertical_standard_scaler*11.38679),left_form_edge+int(horizontal_standard_scaler*0.52971):left_form_edge+int(horizontal_standard_scaler*0.89493)])
    info_dict["Iss. Authority (C)"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*10.73585):address_top_line+int(vertical_standard_scaler*11.38679),left_form_edge+int(horizontal_standard_scaler*1.03627):left_form_edge+int(horizontal_standard_scaler*1.44903)])
     
    info_dict["Doc. # (A)"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*11.48113):address_top_line+int(vertical_standard_scaler*12.04717),left_form_edge+int(horizontal_standard_scaler*0.14634):left_form_edge+int(horizontal_standard_scaler*0.45341)])
    info_dict["Doc. # (B)"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*11.48113):address_top_line+int(vertical_standard_scaler*12.09434),left_form_edge+int(horizontal_standard_scaler*0.52971):left_form_edge+int(horizontal_standard_scaler*0.89493)])
    info_dict["Doc. # (C)"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*11.48113):address_top_line+int(vertical_standard_scaler*12.09434),left_form_edge+int(horizontal_standard_scaler*1.03627):left_form_edge+int(horizontal_standard_scaler*1.44903)])
    
    
    info_dict["Doc. Expir. (A)"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*12.18868):address_top_line+int(vertical_standard_scaler*12.80189),left_form_edge+int(horizontal_standard_scaler*0.28268):left_form_edge+int(horizontal_standard_scaler*0.45528)], config=date_pyt_config)
    info_dict["Doc. Expir. (B)"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*12.18868):address_top_line+int(vertical_standard_scaler*12.80189),left_form_edge+int(horizontal_standard_scaler*0.52971):left_form_edge+int(horizontal_standard_scaler*0.89493)], config=date_pyt_config)
    info_dict["Doc. Expir. (C)"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*12.18868):address_top_line+int(vertical_standard_scaler*12.80189),left_form_edge+int(horizontal_standard_scaler*1.03627):left_form_edge+int(horizontal_standard_scaler*1.44903)], config=date_pyt_config)
    
    info_dict["Employ. Start Date"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*15.50000):address_top_line+int(vertical_standard_scaler*15.82075),left_form_edge+int(horizontal_standard_scaler*0.55660):left_form_edge+int(horizontal_standard_scaler*0.70294)], config=date_pyt_config)
    info_dict["Verifier Name"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*17.15094):address_top_line+int(vertical_standard_scaler*17.66981),left_form_edge+int(horizontal_standard_scaler*0.53471):left_form_edge+int(horizontal_standard_scaler*1.01376)])
    info_dict["Verifier Title"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*17.15094):address_top_line+int(vertical_standard_scaler*17.66981),left_form_edge+int(horizontal_standard_scaler*1.01939):left_form_edge+int(horizontal_standard_scaler*1.44903)])
    info_dict["Business Name"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*18.11321):address_top_line+int(vertical_standard_scaler*18.90566),left_form_edge+int(horizontal_standard_scaler*-0.01251):left_form_edge+int(horizontal_standard_scaler*0.31707)])
    info_dict["Verifier Addr."] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*18.11321):address_top_line+int(vertical_standard_scaler*18.90566),left_form_edge+int(horizontal_standard_scaler*0.40213):left_form_edge+int(horizontal_standard_scaler*1.01376)])
    #Section 3
    info_dict["New Name"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*20.04717):address_top_line+int(vertical_standard_scaler*20.65094),left_form_edge+int(horizontal_standard_scaler*-0.01251):left_form_edge+int(horizontal_standard_scaler*0.91119)])
    info_dict["Date Rehired"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*20.12264):address_top_line+int(vertical_standard_scaler*20.65094),left_form_edge+int(horizontal_standard_scaler*0.91682):left_form_edge+int(horizontal_standard_scaler*1.44841)])
    info_dict["Reverif. Doc. Type"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*21.33019):address_top_line+int(vertical_standard_scaler*21.99057),left_form_edge+int(horizontal_standard_scaler*0.27330):left_form_edge+int(horizontal_standard_scaler*0.41276)])
    info_dict["Reverif. Doc. Num."] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*21.33019):address_top_line+int(vertical_standard_scaler*22.01887),left_form_edge+int(horizontal_standard_scaler*0.63977):left_form_edge+int(horizontal_standard_scaler*0.77924)])
    info_dict["Reverif. Doc. Exp."] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*21.33019):address_top_line+int(vertical_standard_scaler*22.01887),left_form_edge+int(horizontal_standard_scaler*1.02439):left_form_edge+int(horizontal_standard_scaler*1.16635)], config=date_pyt_config)
    
    return info_dict
