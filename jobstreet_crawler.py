import requests # for web requests
from bs4 import BeautifulSoup # a powerful HTML parser
from selenium.webdriver import Chrome
import pandas as pd # for .csv file read and write
import re # for regular regression handling
from requests_html import HTMLSession
session = HTMLSession()

headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'}
path = r"C:/Users/naela/AppData/Local/Programs/Python/chromedriver.exe"
driver = Chrome(path)
driver.implicitly_wait(2)

""" get all position <a> tags for the list of job roles, results stored in a dictionary
<a> tag example:
<a class="position-title-link" id="position_title_3" href="https://www.jobstreet.com.sg/en/job/data-analyst-python-sas-sqlbank-35k-to-5k-gd-bonus5-days-west-6111488?fr=21"
target="_blank" title="View Job Details - Data Analyst (Python / SAS / SQL)(BANK / $3.5K to $5K + GD BONUS / 5 Days / West)" data-track="sol-job" data-job-id="6111488"
data-job-title="Data Analyst (Python / SAS / SQL)(BANK / $3.5K to $5K + GD BONUS / 5 Days / West)" data-type="organic" data-rank="3" data-page="1" data-posting-country="SG">
<h2 itemprop="title">Data Analyst (Python / SAS / SQL)(BANK / $3.5K to $5K + GD BONUS / 5 Days / West)</h2></a>"""
def linksByKeys(keys):
    ## keys: a list of job roles
    ## return: a dictionary of links

    links_dic = dict()
    # scrape key words one by one
    for key in keys:
        print('Scraping position: ', key, ' ...')
        links_dic[key] = linksByKey(key)
        print('{} {} positions found!'.format(len(links_dic[key]),key))
    return links_dic


""" get all position <a> tags for a single job role, triggered by linksByKeys function """
def linksByKey(key):
    ## key: a job role
    ## return: a list of links

    # parameters passed to  http get/post function
    base_url = 'https://www.jobstreet.com.my/en/job-search/job-vacancy.php'
    pay_load = {'key':'','area':1,'option':1,'pg':None,'classified':1,'src':16,'srcr':12}
    pay_load['key'] = key

    # page number
    pn = 1

    position_links = []
    loaded = True
    while loaded:
        print('Loading page {} ...'.format(pn))
        pay_load['pg'] = pn
        r = requests.get(base_url, headers=headers, params=pay_load)

        # extract position <a> tags
        soup = BeautifulSoup(r.text,'html.parser')
        links = soup.find_all('a',{'class':'position-title-link','data-job-id':re.compile(r'.*')})

        # if return nothing, means the function reach the last page, return results
        if not len(links):
            loaded = False
        else:
            position_links += links
            pn += 1
    return position_links


""" parse HTML strings for the list of roles
<a> tag example:
<a class="position-title-link" id="position_title_3" href="https://www.jobstreet.com.sg/en/job/data-analyst-python-sas-sqlbank-35k-to-5k-gd-bonus5-days-west-6111488?fr=21"
target="_blank" title="View Job Details - Data Analyst (Python / SAS / SQL)(BANK / $3.5K to $5K + GD BONUS / 5 Days / West)" data-track="sol-job" data-job-id="6111488"
data-job-title="Data Analyst (Python / SAS / SQL)(BANK / $3.5K to $5K + GD BONUS / 5 Days / West)" data-type="organic" data-rank="3" data-page="1" data-posting-country="SG">"""
def parseLinks(links_dic):
    ## links_dic: a dictionary of links
    ## return: print parsed results to .csv file

    for key in links_dic:
        jobs = []
        for link in links_dic[key]:
            jobs.append([key] + parseLink(link))

        # transfrom the result to a pandas.DataFrame
        result = pd.DataFrame(jobs,columns=['key_word','job_id','job_title','country','job_link','company','company_region','company_industry','company_size','experience_requirement','working_location','salary','description'])

        # add a column denoting if the position is posted by a recuriter company
        result['postedByHR'] = True #result.company_industry.apply(lambda x:True if x and x.find('Human Resources')>-1 else False)

        # save result,
        file_name = key+'.csv'
        result.to_csv(file_name,index=False)


""" parse a single <a> tag, extract the information, triggered by parseLinks function """
def parseLink(link):
	## link: a single position <a> tag
	## return: information of a single position

	# unique id assigned to a position
	job_id = link['data-job-id'].strip()
	# job title
	job_title = link['data-job-title'].strip()
	# posted country
	country = link['data-posting-country'].strip()
	# the web address towards to the post detail page
	job_href = link['href']
	# go to post detail page, and fetch information
	other_detail = getJobDetail(job_href)
	return [job_id,job_title,country,job_href] + other_detail


""" extract details from post detail page """
def getJobDetail(job_href):
    ## job_href: a post url
    ## retun: post details from the detail page

    print('Scraping ',job_href,'...')
    driver.get(job_href)
	
    try:
        company_name=driver.find_element_by_id("company_name").text
    except:
        company_name = None
    try:
        years_of_experience=driver.find_element_by_id("years_of_experience").text
    except:
        years_of_experience = None
    try:
        company_location=driver.find_element_by_id("single_work_location").text
    except:
        company_location = None
    try:
        company_industry=driver.find_element_by_id("company_industry").text
    except:
        company_industry = None
    try:
        job_location=driver.find_element_by_id("address").text
    except:
        job_location = None
    try:
        company_size=driver.find_element_by_id("company_size").text
    except:
        company_size = None
    try:
        salary=driver.find_element_by_id("salary_range").text
    except:
        salary = None
    try:
        job_description=driver.find_element_by_id("job_description").text
    except:
        job_description = None
    return [company_name,company_location,company_industry,company_size,years_of_experience,job_location,salary,job_description]

def main():

    # a list of job roles to be crawled
    key_words = ['crop']
    s = requests.session()
    links_dic = linksByKeys(key_words)
    parseLinks(links_dic)

if __name__ == '__main__':
	main()
