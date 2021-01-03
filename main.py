from bs4 import BeautifulSoup
import requests
import csv
import pandas as pd
import base64
import streamlit as st


def make_initial_request(keywords, location=None):
    result = requests.get('https://panoramafirm.pl/szukaj?k={}&l={}'.format(keywords, location))
    if result.status_code == 200:
        return result.content
    else:
        return False

def make_request(url):
    result = requests.get(url)
    if result.status_code == 200:
        return result.content
    else:
        return False

def get_request_url(keywords, location=None):
    return 'https://panoramafirm.pl/szukaj?k={}&l={}'.format(keywords, location)

def parse_page(soup, label):
    company_names = soup.find_all('a', 'company-name addax addax-cs_hl_hit_company_name_click')
    content = soup.find_all('div', 'row company-bottom-content border-top')
    companies = []
    for item, company_name in zip(content, company_names):
        company = {}

        content = item.div.div
        tel = content.find('a', 'icon-telephone addax addax-cs_hl_phonenumber_click')
        if tel:
            tel = tel.get('title')
        else:
            tel = 'None'
        website = content.find('a', 'icon-website addax addax-cs_hl_hit_homepagelink_click')
        if website:
            website = website.get('href')
        else:
            website = 'None'
        email = content.find('a', class_='ajax-modal-link icon-envelope cursor-pointer addax addax-cs_hl_email_submit_click')
        if email:
            email = email.get('data-company-email')
        else:
            email = 'None'

        company_name = company_name.next.strip()
        company['Name'] = company_name
        company['Phone 1 - Value'] = tel
        company['Organization 1 - Title'] = website
        company['E-mail 1 - Value'] = email
        company['Group Membership'] = '{}::: * myContacts'.format(label)

        companies.append(company)
    return companies

def get_next_page_url(soup):
    paginator = soup.find('a', 'text-dark py-1 addax addax-cs_hl_nextpage')
    if paginator:
        next_page_url = paginator.get('href')
        return next_page_url

def flat_list(list):
    flat_list = [item for sublist in list for item in sublist]
    return flat_list

def scrape(url, label):
    result = []
    while url:
        content = make_request(url)
        if content:
            soup = BeautifulSoup(content, 'lxml')
            companies = parse_page(soup, label)
            url = get_next_page_url(soup)
            result.append(companies)
    result = flat_list(result)
    return result

def save_to_csv(toCSV):
    keys = toCSV[0].keys()
    with open('people.csv', 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(toCSV)

def download_link(object_to_download, download_filename, download_link_text):
    """
    Generates a link to download the given object_to_download.

    object_to_download (str, pd.DataFrame):  The object to be downloaded.
    download_filename (str): filename and extension of file. e.g. mydata.csv, some_txt_output.txt
    download_link_text (str): Text to display for download link.

    Examples:
    download_link(YOUR_DF, 'YOUR_DF.csv', 'Click here to download data!')
    download_link(YOUR_STRING, 'YOUR_STRING.txt', 'Click here to download your text!')

    """
    if isinstance(object_to_download,pd.DataFrame):
        object_to_download = object_to_download.to_csv(index=False)

    # some strings <-> bytes conversions necessary here
    b64 = base64.b64encode(object_to_download.encode()).decode()

    return f'<a href="data:file/txt;base64,{b64}" download="{download_filename}">{download_link_text}</a>'


if __name__ == "__main__":
    keyword = st.text_input('Podaj szukaną frazę: ')
    location = st.text_input('Podaj lokalizację: ')

    if st.button('Szukaj'):
        label = keyword + '-' + location
        url = get_request_url(keyword, location)
        results = scrape(url, label)
        df = pd.DataFrame(results)
        st.dataframe(df)
        tmp_download_link = download_link(df, '{}.csv'.format(label), 'Kliknij aby pobrać w csv')
        st.markdown(tmp_download_link, unsafe_allow_html=True)


