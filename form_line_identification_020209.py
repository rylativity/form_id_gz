# -*- coding: utf-8 -*-
"""
Created on Fri Dec 14 11:04:04 2018

@author: Ryan Stewart

THIS CODE TESTED ON FORM I-9 02/02/09
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
    start_coefficient = (start_row - 678)/119
    end_coefficient = (end_row - 678)/119
    print(f"Start: address_top_line+int(vertical_standard_scaler*{start_coefficient:.5f})")
    print(f"End: address_top_line+int(vertical_standard_scaler*{end_coefficient:.5f})")

def horizontal_converter(start_col, end_col):
    start_coef = (start_col - 1215)/541
    end_coef = (end_col - 1215)/541
    print(f"Start: middle_sect1_line+int(horizontal_standard_scaler*{start_coef:.5f})")
    print(f"End: middle_sect1_line+int(horizontal_standard_scaler*{end_coef:.5f})")
    
def pyt_converter(start_row, end_row, start_col, end_col):
    start_coefficient = (start_row - 678)/119
    end_coefficient = (end_row - 678)/119
    start_coef = (start_col - 1215)/541
    end_coef = (end_col - 1215)/541
    print(f"pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*{start_coefficient:.5f}):address_top_line+int(vertical_standard_scaler*{end_coefficient:.5f}),middle_sect1_line+int(horizontal_standard_scaler*{start_coef:.5f}):middle_sect1_line+int(horizontal_standard_scaler*{end_coef:.5f})])")
"""

images = []
    
#loop through PDF files and convert them to PNG
with Image(filename="C:\\Users\\Ryan Stewart\\Desktop\\repos\\data\\i-9_02-02-09(Filled).pdf", resolution = 300) as img:
    #find the filename
    filename = "C:\\Users\\Ryan Stewart\\Desktop\\repos\\i-9_02-02-09(Filled).pdf"
    
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
    dark_rows = [i for i,x in enumerate(page1) if sum(x) <400] ### 
    row_groups = [tuple(group) for group in mit.consecutive_groups(dark_rows)]
    rows = [np.max(group) for group in row_groups]
    name_top_line, address_top_line = rows[3], rows[4]
    vertical_standard_scaler = address_top_line - name_top_line


    #can use this value to define distance. Won't depend on scale of scanned document
    vertical_standard_scaler = address_top_line - name_top_line
   
    
    
    #Identify vertical dark columns (form edges) and use them to create horizontal scaler for distance
    dark_columns = [i for i,x in enumerate(zip(*page1)) if sum(x) < 2650] ### 
    side_col_groups = [tuple(group) for group in mit.consecutive_groups(dark_columns)]
    side_cols = [np.max(group) for group in side_col_groups]
    middle_sect1_line, right_sect1_line = side_cols[-2], side_cols[-1]
    horizontal_standard_scaler = right_sect1_line - middle_sect1_line
    
    
    ### Data extraction
    # Section 1
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
    if maiden:
        info_dict["maiden"] = maiden
    
    
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
    
    #Section 2
    
    info_dict["List A Document"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*9.86555):address_top_line+int(vertical_standard_scaler*10.51261),middle_sect1_line+int(horizontal_standard_scaler*-1.53235):middle_sect1_line+int(horizontal_standard_scaler*-0.61553)])
    info_dict["List B Document"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*9.86555):address_top_line+int(vertical_standard_scaler*10.51261),middle_sect1_line+int(horizontal_standard_scaler*-0.40481):middle_sect1_line+int(horizontal_standard_scaler*0.67652)])
    info_dict["List C Document"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*9.86555):address_top_line+int(vertical_standard_scaler*10.51261),middle_sect1_line+int(horizontal_standard_scaler*1.10351):middle_sect1_line+int(horizontal_standard_scaler*2.18299)])
     
    info_dict["Iss. Authority (A)"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*10.57143):address_top_line+int(vertical_standard_scaler*11.06723),middle_sect1_line+int(horizontal_standard_scaler*-1.47689):middle_sect1_line+int(horizontal_standard_scaler*-0.61738)])
    info_dict["Iss. Authority (B)"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*10.57143):address_top_line+int(vertical_standard_scaler*11.06723),middle_sect1_line+int(horizontal_standard_scaler*-0.39926):middle_sect1_line+int(horizontal_standard_scaler*0.68207)])
    info_dict["Iss. Authority (C)"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*10.57143):address_top_line+int(vertical_standard_scaler*11.06723),middle_sect1_line+int(horizontal_standard_scaler*1.10721):middle_sect1_line+int(horizontal_standard_scaler*2.18854)])
     
    info_dict["Doc. # (A)"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*11.11765):address_top_line+int(vertical_standard_scaler*11.59664),middle_sect1_line+int(horizontal_standard_scaler*-1.59519):middle_sect1_line+int(horizontal_standard_scaler*-0.61738)])
    info_dict["Doc. # (B)"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*11.11765):address_top_line+int(vertical_standard_scaler*11.59664),middle_sect1_line+int(horizontal_standard_scaler*-0.39926):middle_sect1_line+int(horizontal_standard_scaler*0.68207)])
    info_dict["Doc. # (C)"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*11.11765):address_top_line+int(vertical_standard_scaler*11.59664),middle_sect1_line+int(horizontal_standard_scaler*1.10721):middle_sect1_line+int(horizontal_standard_scaler*2.18854)])
    
    info_dict["Doc. Expir. (A)"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*11.64706):address_top_line+int(vertical_standard_scaler*12.13445),middle_sect1_line+int(horizontal_standard_scaler*-1.15896):middle_sect1_line+int(horizontal_standard_scaler*-0.61553)])
    info_dict["Doc. Expir. (B)"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*11.64706):address_top_line+int(vertical_standard_scaler*12.13445),middle_sect1_line+int(horizontal_standard_scaler*-0.39926):middle_sect1_line+int(horizontal_standard_scaler*0.68207)])
    info_dict["Doc. Expir. (C)"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*11.64706):address_top_line+int(vertical_standard_scaler*12.13445),middle_sect1_line+int(horizontal_standard_scaler*1.10721):middle_sect1_line+int(horizontal_standard_scaler*2.18854)])
    
    info_dict["Employ. Start Date"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*13.94958):address_top_line+int(vertical_standard_scaler*14.41176),middle_sect1_line+int(horizontal_standard_scaler*-1.47505):middle_sect1_line+int(horizontal_standard_scaler*-0.96488)])
    info_dict["Verifier Name"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*15.15126):address_top_line+int(vertical_standard_scaler*15.81513),middle_sect1_line+int(horizontal_standard_scaler*-0.38632):middle_sect1_line+int(horizontal_standard_scaler*1.03882)])
    info_dict["Verifier Title"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*15.15126):address_top_line+int(vertical_standard_scaler*16.57143),middle_sect1_line+int(horizontal_standard_scaler*1.04806):middle_sect1_line+int(horizontal_standard_scaler*2.17745)])
    info_dict["Business Name/Addr."] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*16.10084):address_top_line+int(vertical_standard_scaler*16.68067),middle_sect1_line+int(horizontal_standard_scaler*-1.96858):middle_sect1_line+int(horizontal_standard_scaler*1.03882)])
    
    #Section 3
    info_dict["Date Rehired"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*17.52941):address_top_line+int(vertical_standard_scaler*18.04202),middle_sect1_line+int(horizontal_standard_scaler*0.64325):middle_sect1_line+int(horizontal_standard_scaler*2.48614)])
    info_dict["Reverif. Doc. Type"] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*18.45378):address_top_line+int(vertical_standard_scaler*19.00840),middle_sect1_line+int(horizontal_standard_scaler*0.27542):middle_sect1_line+int(horizontal_standard_scaler*0.94085)])
    info_dict["Reverif. Doc. Num."] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*18.45378):address_top_line+int(vertical_standard_scaler*19.00840),middle_sect1_line+int(horizontal_standard_scaler*0.27542):middle_sect1_line+int(horizontal_standard_scaler*0.94085)])
    info_dict["Reverif. Doc. Exp."] = pytesseract.image_to_string(page1[address_top_line+int(vertical_standard_scaler*18.45378):address_top_line+int(vertical_standard_scaler*19.00000),middle_sect1_line+int(horizontal_standard_scaler*1.63031):middle_sect1_line+int(horizontal_standard_scaler*2.19224)])
    
    return info_dict
