from urllib.request import urlopen
import json, time, random, jieba
import requests
import os
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import ssl
import matplotlib.pyplot as plt
from collections import Counter
import matplotlib
import seaborn as sns
ssl._create_default_https_context = ssl._create_unverified_context
pd.set_option('display.max_columns', 20)


user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36"
headers = {'User-agent' : user_agent}
search_url = 'https://www.104.com.tw/jobs/search/'


def getJobList(job, page):
    '''
    Collecting all job posts url
    :param job: String, Specify the job title that to be searched
    :param page: Integer, How many pages of searching results to be shown
    :return: a list of searching result consists of job title and its web url
    '''
    try:
        os.mkdir('./{}'.format(job))
    except Exception as error_name:
        print(error_name)
        pass

    job_list = []
    ss = requests.session()
    total_html = ''

    # For loop is to visit multiple searching result pages
    for i in range(page):
        query_str = '''ro: 0
        kwop: 7
        keyword: {}
        jobcatExpansionType: 0
        order: 14
        asc: 0
        page: {}
        mode: s
        jobsource: 2018indexpoc'''.format(job, i + 1)

        param_data = {}
        for each_line in query_str.split('\n'):
            param_data[each_line.split(': ')[0]] = each_line.split(': ')[1]

        response = ss.get(url=search_url, params=param_data, headers=headers)
        total_html += response.text

    # Adding follow-on pages html into a big string
    soup = BeautifulSoup(total_html, 'html.parser')

    job_titles = soup.select('h2.b-tit')
    for each_job in job_titles:
        job = each_job.select('a')
        for item in job:
            url = 'https:' + item['href']
            title = item.text
            job_list.append('{}: {}'.format(title, url))

    return job_list


def getJobDescription(jobList):
    '''
    Extracting job description details from each recruitment post
    :param jobList: List, input a list of job research result
    :return description_dict: Dictionary, return a dictionary of jobs description {keys: [title, company, edu, skill]}
    '''
    # 104 blocking users from locating the tag by using bs4, therefore, I found that they provide a json file when execute a GET request
    # to a certain url, with headers including referer


    description_dict = {}
    index = 1
    for job in jobList:
        job_title = job.split(": ")[0]
        job_id = job.split(': ')[1].split('?')[0].split('/')[4]
        job_url = 'https://www.104.com.tw/job/ajax/content/{}'.format(job_id)
        headers = {
            "Referer": "https://www.104.com.tw/job/{}".format(job_id),
        }
        response = requests.get(url=job_url, headers=headers)
        time.sleep(random.randrange(1,3))
        job_details = json.loads(response.text)

        company_name = job_details['data']['header']['custName']
        job_content = job_details['data']['jobDetail']['jobDescription']
        specialty = job_details['data']['condition']['specialty']
        skill = job_details['data']['condition']['other']
        education = job_details['data']['condition']['edu']

        description_dict[str(index)] = {'title': job_title, 'company': company_name, 'description' : job_content, 'edu': education, 'skill': str(job_content) + str(specialty) + skill}
        index += 1

    print("Online Job searching completed")
    return description_dict


def saveCSV(job_dict):
    '''
    :param job_dict: Input a dictionary of job searching result
    :return: no return object, this function creates a csv file
    '''
    description = job_dict
    columns = ['No.', 'Job_Company', 'Job_Title', 'Job_Description', 'Education_level', 'Skills_Requirement']
    data = []
    for n, key in enumerate(description):
        data.append([n+1, description[key]['company'], description[key]['title'], description[key]['description'], description[key]['edu'], description[key]['skill']])
    df = pd.DataFrame(columns=columns, data=data)
    df.to_csv('./jobsearch.txt', index=True)
    print("Job searching result saved into CSV file")


def skillClassify(file_path):
    '''

    :param file_path: String, specify the file in which we want to classify resulting skills
    :return: no returning object, this function creates another txt file, contains skills counts.
    '''

    df = pd.read_csv(file_path)
    all_skills = df.loc[:, 'Skills_Requirement']

    skill_set = {'python', 'nosql', 'sql', 'r', 'ai', 'r語言', 'mysql', 'mongodb', '資料庫', 'javascript', '機器學習', '深度學習',
                 '資料探勘', '文字探勘', 'linux',
                 '統計學', '資料庫', '資料分析', 'sap', 'sas', 'java', 'c++', 'c#'}
    jieba.load_userdict('./mydict.txt')

    keyword_list = []
    new_columns = []

    for i in range(len(all_skills)):
        s = str(all_skills[i])
        clean = s.strip('\r\n')
        s_3 = '|'.join(jieba.cut(clean))
        keyword_list = [i for i in s_3.split('|') if len(i) > 1]

        current_set = set([i.lower() for i in keyword_list])
        new_columns.append(list(skill_set.intersection(current_set)))


    df['Skills_Requirement'] = new_columns
    df.to_csv('./job_skills.txt')
    print("Required Job skills categorized")


def result_plot():


    # setting Chinese font
    plt.rcParams['font.sans-serif'] = ['SimSun']

    df = pd.read_csv('./job_skills.txt')
    skills_set = []
    for item in df.loc[:, 'Skills_Requirement']:
        if len(item) > 0:
            for each in (item.strip('[').strip(']').replace("'", '').replace(' ', '')).split(','):
                if len(each) > 0:
                    skills_set.append(each)
    count_result = Counter(skills_set)
    skills_dict = dict(count_result.most_common())

    skills_name = list(skills_dict.keys())
    skills_data = list(skills_dict.values())

    fig, ax = plt.subplots(figsize=(16, 8))
    ax.barh(skills_name, skills_data)
    plt.savefig('./image/資料分析師需求技能.png')
    plt.show(block=True)


def execute(searching_key, searching_numb):
    '''

    :param searching_key:
    :param searching_numb:
    :return:
    '''

    searching_keyword = searching_key
    searching_pages = int(searching_numb)

    getjob = getJobList(searching_keyword, searching_pages)

    description = getJobDescription(getjob)

    saveCSV(description)

    skillClassify('./jobsearch.txt')

    result_plot()


if __name__ == '__main__':
    result = execute('資料分析師', 5)

