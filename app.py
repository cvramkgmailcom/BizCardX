## Importing necessary libraries
import streamlit as st
import pandas as pd
import easyocr
from PIL import Image
import numpy as np
from streamlit_cropper import st_cropper
import re
import mysql.connector


st.markdown(
    """
    <style>
    .file-uploader {
        border-style: dashed;
        border-width: 2px;
        border-radius: 5px;
        padding: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

#few variables to use as global

mList = []
x=[]

#not sure how it works, while doing google, it seems to have a model is mandatory
@st.cache_data
def load_model():
    model = easyocr.Reader(['en'])
    return model

#data base connection string
def connect_to_database():
    conn = mysql.connector.connect(
        host="localhost",
        user="rk",
        password="rk123",
        database="guvi_bizcardx"
    )
    return conn

#State and city list to identify (as we have name and other informations, hence created it, later we can extract this information from mysql db hence it will be keep updated whenever the user does manually)
state_list=['TamilNadu','Karnataka']
city_list=['Chennai','Erode','Salem','HYDRABAD','Tirupur']

#main controls
def main():
    st.title("Business Card Information Extractor")
    model = load_model()

    # col1, col2, col3, col4 = st.columns((3,1,1,1))
    # with col1:

    ## file uploader
    uploaded_file = st.file_uploader("Upload an image of a business card", type=["jpg", "jpeg", "png"])
    # with col2:
    if uploaded_file is not None:
        col1, col2, col3= st.columns((1,1,1))
        with col1:
            crop_image = st.checkbox("Crop image?")

        image = Image.open(uploaded_file)
        ## after uploading if the user wants to crop the b-card he can select this checkbox and it will enable the cropping feature on the image along with a couple of formatting options 
        if crop_image:
            realtime_update =True
            with col2:    
                box_color = st.color_picker(label="Crop: Box Color", value='#0000FF')
            with col3:
                aspect_choice = st.selectbox(label="Crop: Aspect Ratio", options=["1:1", "16:9", "4:3", "2:3", "Free"])
                aspect_dict = {
                    "1:1": (1, 1),
                    "16:9": (16, 9),
                    "4:3": (4, 3),
                    "2:3": (2, 3),
                    "Free": None
                }
                aspect_ratio = aspect_dict[aspect_choice]


            cropped_image = st_cropper(image, realtime_update=realtime_update, box_color=box_color,aspect_ratio=aspect_ratio)
            # st.image(cropped_image, caption="Cropped business card", use_column_width=None, clamp=True, output_format="auto")
            image_np = np.array(cropped_image)
        else:
            st.image(image, caption="Uploaded business card", use_column_width=None, clamp=True, output_format="auto")
            image_np = np.array(image)
        # this button also enables once the user uploaded the image, and once clicked on this extract information button, the data will be extracted from the uploaded image    
        # if st.button("Extract Information"):
        with st.spinner('Extracting Information...'):
            result = model.readtext(image_np)
            extracted_info = extract_info(result)
            display_info(extracted_info)

#data extraction function stars here
def extract_info(result):
    #defining the necessary variables
    extracted_info = {
        "ei_company_name": "",
        "ei_card_holder_name": "",
        "ei_designation": "",
        "ei_mobile_number": "",
        "ei_email_address": "",
        "ei_website_url": "",
        "ei_area": "",
        "ei_city": "",
        "ei_state": "",
        "ei_pin_code": ""
    }
    
    xx = 0

    # we can identify the following data using regex from the extracted data
    website_url_pat = r"(?i)www[\s.a-z][a-z0-9]+\.[a-z]{2,3}"
    mobile_number_pat = r"\+?\d{1,3}-\d{3}-\d{4}"
    email_address_pat = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    pincode_pat = r"\d{6}"

    mdel=[]

    #only the results are extracted from the result variable, as it will have many other information from easyOCR, hence we need the data only and its available in the every list with in index 1
    for i in result:
        mList.append(i[1])

    #identify and naming the from mList
    for text in mList:        
        x.append(text)
        ws = re.findall(website_url_pat,text)
        mn = re.findall(mobile_number_pat,text)
        ea = re.findall(email_address_pat,text)
        pc = re.findall(pincode_pat,text)

        if xx==0:
            extracted_info["ei_card_holder_name"] = text
            mList[xx] = mList[xx].replace(text,'')
        if xx==1:
            extracted_info["ei_designation"] = text
            mList[xx] = mList[xx].replace(text,'')
        if ws:
            ei_website_url = "www."+ws[0][3:]
            # st.write(mList[xx],"+",ws)
            mList[xx] = mList[xx].replace(ws[0],'')
            extracted_info["ei_website_url"] = ei_website_url.replace('..','.')

        if mn:
            extracted_info["ei_mobile_number"]+=" "+mn[0]
            mList[xx] = mList[xx].replace(mn[0],'')
        if ea:
            extracted_info["ei_email_address"] = ea[0]
            mList[xx] = mList[xx].replace(text,'')
        if pc:
            extracted_info["ei_pin_code"] = pc[0]
            mList[xx] = mList[xx].replace(pc[0],'')
        xx=xx+1

    for state in state_list:
        xx = 0
        for text in mList:
            if state in text:
                extracted_info["ei_state"] = state
                mList[xx] = mList[xx].replace(state,'')
            xx=xx+1
            
    for city in city_list:
        xx = 0
        for text in mList:
            if city in text:
                extracted_info["ei_city"] = city
                mList[xx] = mList[xx].replace(city,'')
            xx=xx+1

        #ei_pin_code = "text[.]"
    # once few of the namings are defined, which can be identify based on the positions, mapping with the available list i.e. state, city, and regex
    # then those texts are removed from the mList, now, we shall check once again for regex, if there are secondary info.
    remainig_text = "".join(mList)
    ws = re.findall(website_url_pat,remainig_text)
    mn = re.findall(mobile_number_pat,remainig_text)
    ea = re.findall(email_address_pat,remainig_text)
    pc = re.findall(pincode_pat,remainig_text)    

    if ws:
        ei_website_url = "www."+ws[0][3:]
        remainig_text = remainig_text.replace(ws[0],'')
        extracted_info["ei_website_url"] = ei_website_url.replace('..','.')

    if mn:
        extracted_info["ei_mobile_number"]+=" "+mn[0]
        remainig_text = remainig_text.replace(mn[0],'')
    if ea:
        extracted_info["ei_email_address"] = ea[0]
        remainig_text = remainig_text.replace(text,'')
    if pc:
        extracted_info["ei_pin_code"] = pc[0]
        remainig_text = remainig_text.replace(pc[0],'')


    # st.write(remainig_text)
    # once the secondary info's are identified, those are also gets removed from the mList and stored in remaining_text from this, we shall split address and company name
    remainig_text_a = remainig_text.split(",")
    ld = len(remainig_text_a)
    # st.write(ld)
    extracted_info["ei_company_name"] = remainig_text_a[ld-1]
    ei_area_a = remainig_text_a[0:ld-1]

    extracted_info["ei_area"] = "".join(ei_area_a)

    #finaly we returns the extracted_info variable from this function
    return extracted_info


    # st.write(mList)
    # st.write(mdel)

    # st.write(mdel)
    # st.write(extracted_info["card_holder_name"])
    # st.write(extracted_info["designation"])
    # st.write(extracted_info["website_url"])
    # st.write(extracted_info["mobile_number"])
    # st.write(extracted_info["email_address"])

#defining a function to show the extracted_info in textboxes for editing option
def display_info(extracted_info):
    col1,col2,col3,col4=st.columns(4)
    row1_col1, row1_col2, row1_col3, row1_col4 = col1, col2, col3, col4
    row2_col1, row2_col2, row2_col3, row2_col4 = col1, col2, col3, col4
    row3_col1, row3_col2, row3_col3, row3_col4 = col1, col2, col3, col4

    text_input_style = """
        <style>
            input[type="text"] {
                background-color: #f5f5f5;
                border: 2px solid #0072b2;
                border-radius: 5px;
                color: #0072b2;
                font-size: 16px;
                padding: 5px;
                width: 100%;
            }
        </style>
    """
    st.write(text_input_style, unsafe_allow_html=True)

    with st.form(key='my_form'):

        x_company_name=""
        x_card_holder_name=""
        x_designation=""
        x_mobile_number=""
        x_email_address=""
        x_website_URL=""
        x_area=""
        x_city=""
        x_state=""
        x_pin_code=""

        with row1_col1: x_company_name =st.text_input('Company Name',extracted_info["ei_company_name"])
        with row1_col2: x_card_holder_name =st.text_input('Card Holder Name',extracted_info["ei_card_holder_name"])
        with row1_col3: x_designation =st.text_input('Designation',extracted_info["ei_designation"])
        with row2_col1: x_mobile_number =st.text_input('Mobile Number',extracted_info["ei_mobile_number"])
        with row2_col2: x_email_address =st.text_input('Email Address',extracted_info["ei_email_address"])
        with row2_col3: x_website_url =st.text_input('WebSite URL',extracted_info["ei_website_url"])
        with row3_col1: x_area =st.text_input('Area',extracted_info["ei_area"])
        with row3_col2: x_city =st.text_input('City',extracted_info["ei_city"])
        with row3_col3: x_state =st.text_input('State',extracted_info["ei_state"])
        with row3_col4: x_pin_code =st.text_input('Pin Code',extracted_info["ei_pin_code"])

        # submit_button = st.form_submit_button(label='Save')

        #storing the data into database
        if st.form_submit_button(label='Save'):
            conn = connect_to_database()
            cursor = conn.cursor()
            query = "INSERT INTO cd (company_name,card_holder_name,designation,mobile_number,email_address,website_url,area,city,state,pin_code) VALUES (%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s ,%s)"
            values = (x_company_name ,x_card_holder_name ,x_designation ,x_mobile_number ,x_email_address ,x_website_url ,x_area ,x_city ,x_state ,x_pin_code)
            cursor.execute(query, values)
            conn.commit()
            conn.close()
            st.success("Data saved successfully!")
            st.experimental_set_query_params(**{"random_param": st.session_state.get("random_param", 0) + 1})
if __name__ == '__main__':
    main()

mydb = mysql.connector.connect(
        host="localhost",
        user="rk",
        password="rk123",
        database="guvi_bizcardx"
    )

df = pd.read_sql("SELECT * FROM cd", mydb)
num_records = len(df)
st.markdown(f"# {num_records} Cards scanned so far")
# st.write("")

# Define custom CSS styles
css = """
<style>
table.dataframe td{
  font-size: 120%;
  color: white; /* Change header font color */    
  border: 1px solid #ccc;
  border-collapse: collapse;
  margin: 1em 0;
  text-align: center;
}

table.dataframe th, table.dataframe td {
  color: white; /* Change header font color */    
  padding: 0.5em;
  border: 1px solid #ccc;
}

table.dataframe th {
  background-color: #000000;
  font-weight: bold;
  color: white; /* Change header font color */    
}
    
</style>
"""

# Add JavaScript libraries for sorting and searching


st.write("""
<script src="https://cdn.datatables.net/1.10.24/js/jquery.dataTables.min.js" crossorigin="anonymous"></script>
<link rel="stylesheet" href="https://cdn.datatables.net/1.10.24/css/jquery.dataTables.min.css" crossorigin="anonymous">
""", unsafe_allow_html=True)

# Initialize DataTables library for sorting and searching
search_script = """
<script>
$(document).ready(function() {
    $('.dataframe').DataTable();
} );
</script>
"""
styled_table = df.style.set_table_attributes('class="dataframe"').set_caption("My Table")

# Display the table using Streamlit
st.markdown(search_script,unsafe_allow_html=True)
st.write(styled_table, unsafe_allow_html=True)

