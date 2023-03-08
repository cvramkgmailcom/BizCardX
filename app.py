import streamlit as st
import easyocr
from PIL import Image
import numpy as np
from streamlit_cropper import st_cropper
import re

state_list=['TamilNadu','Karnataka']
city_list=['Chennai','Erode','Salem','HYDRABAD','Tirupur']

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


mList = []
x=[]
@st.cache_data
def load_model():
    model = easyocr.Reader(['en'])
    return model

def main():
    st.title("Business Card Information Extractor")
    model = load_model()

    # col1, col2, col3, col4 = st.columns((3,1,1,1))
    # with col1:
    uploaded_file = st.file_uploader("Upload an image of a business card", type=["jpg", "jpeg", "png"])
    # with col2:
    if uploaded_file is not None:
        col1, col2, col3= st.columns((1,1,1))
        with col1:
            crop_image = st.checkbox("Crop image?")

        image = Image.open(uploaded_file)

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
        if st.button("Extract Information"):
            with st.spinner('Extracting Information...'):
                result = model.readtext(image_np)
                extracted_info = extract_info(result)
                # display_info(extracted_info)

def extract_info(result):
    extracted_info = {
        "company_name": "",
        "card_holder_name": "",
        "designation": "",
        "mobile_number": "",
        "email_address": "",
        "website_url": "",
        "area": "",
        "city": "",
        "state": "",
        "pin_code": ""
    }


    xx = 0

    website_url_pat = r"(?i)www[\s.][a-z0-9]+\.[a-z]{2,3}"
    mobile_number_pat = r"\+?\d{1,3}-\d{3}-\d{4}"
    email_address_pat = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

    mdel=[]

    for i in result:
        mList.append(i[1])
        
    
    for text in mList:        
        x.append(text)
        ws = re.findall(website_url_pat,text)
        mn = re.findall(mobile_number_pat,text)
        ea = re.findall(email_address_pat,text)

        if xx==0:
            extracted_info["card_holder_name"] = text
            mdel.append(xx)
        if xx==1:
            extracted_info["designation"] = text
            mdel.append(xx)
        if ws:
            extracted_info["website_url"] = "www."+text[4:]
            mdel.append(xx)
        if mn:
            extracted_info["mobile_number"]+=" "+text
            mdel.append(xx)
        if ea:
            extracted_info["email_address"] = text
            mdel.append(xx)
            
        xx=xx+1

    mdel.sort(reverse=True)

    for index in mdel:
        del mList[index]


        extracted_info["company_name"] = "text"
        extracted_info["area"] = "text[.]"
        extracted_info["city"] = "text[.]"
        extracted_info["state"] = "text[.]"
        extracted_info["pin_code"] = "text[.]"

    st.write(mList)
    st.write(mdel)

    # st.write(mdel)
    # st.write(extracted_info["card_holder_name"])
    # st.write(extracted_info["designation"])
    # st.write(extracted_info["website_url"])
    # st.write(extracted_info["mobile_number"])
    # st.write(extracted_info["email_address"])

    col1,col2,col3,col4=st.columns(4)
    row1_col1, row1_col2, row1_col3, row1_col4 = col1, col2, col3, col4
    row2_col1, row2_col2, row2_col3, row2_col4 = col1, col2, col3, col4
    row3_col1, row3_col2, row3_col3, row3_col4 = col1, col2, col3, col4

    if not extracted_info["company_name"]: extracted_info["company_name"]=""

    with row1_col1: x_company_name =st.text_input('Company Name',extracted_info["company_name"])
    with row1_col2: x_card_holder_name =st.text_input('Card Holder Name',extracted_info["card_holder_name"])
    with row1_col3: x_designation =st.text_input('Designation',extracted_info["designation"])
    with row2_col1: x_mobile_number =st.text_input('Mobile Number',extracted_info["mobile_number"])
    with row2_col2: x_email_address =st.text_input('Email Address',extracted_info["email_address"])
    with row2_col3: x_website_URL =st.text_input('WebSite URL',extracted_info["website_url"])
    with row3_col1: x_area =st.text_input('Area',extracted_info["area"])
    with row3_col2: x_city =st.text_input('City',extracted_info["city"])
    with row3_col3: x_state =st.text_input('State',extracted_info["state"])
    with row3_col4: x_pin_code =st.text_input('Pin Code',extracted_info["pin_code"])

    


if __name__ == '__main__':
    main()
