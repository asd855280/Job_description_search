from urllib.request import urlopen
import json, time, random, jieba
import requests
import os
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
pd.set_option('display.max_columns', 20)


user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36"
headers = {'User-agent' : user_agent}
search_url = 'https://www.104.com.tw/jobs/search/'


def getJobList(job, page):
    '''
    :param job: Specify the job title that to be searched
    :param page: How many pages of searching results to be shown
    :return: a list of searching result consists of job title and its web url
    '''
    os.mkdir('./{}'.format(job))
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
    :param jobList: Input a list of job research result
    :return: return a diction of jobs description(keys: title, company, edu, skill)
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
    :param file_path: specify the file in which we want to classify resulting skills
    :return: no returning object, this function creates another txt file
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



def skillCount(path_file, page_number):
    '''
    :param path_file: Input file path
    :return: no returning object, this function create a new csv file appending boolean table show which skill required for perspective job
    '''
    row_numb = int(page_number) * 20
    df = pd.read_csv(path_file)
    zero_array = np.zeros((row_numb, 22), dtype=int)
    insert_columns = ['python', 'nosql', 'sql', 'r', 'ai', 'r語言', 'mysql', 'mongodb', '資料庫', 'javascript', '機器學習',
                      '深度學習', '資料探勘', '文字探勘', 'linux',
                      '統計學', '資料分析', 'sap', 'sas', 'java', 'c++', 'c#']

    df[insert_columns] = zero_array
    df.to_csv('./skill_count.txt')

    for i in range(len(df)):
        tmp_dict = {}
        skill_list = [item.strip(" '").strip("'") for item in
                      df.loc[i, 'Skills_Requirement'].strip('[').strip(']').split(',')]

        for each in skill_list:
            tmp_dict[each] = int(1)

        updating_df = pd.DataFrame(tmp_dict, index=[i], dtype=int)
        df.update(updating_df)

    df.to_csv('./skill_bool.txt')
    print("Final file completed")

def getSummary(filePath):
    '''
    :param filePath: Input the job searching result dataframe
    :return: creating a txt file, with sorted required skills and its relative counts
    '''
    df = pd.read_csv(filePath)
    skill_list = ['python', 'nosql', 'sql', 'r', 'ai', 'r語言', 'mysql', 'mongodb', '資料庫', 'javascript', '機器學習',
                  '深度學習', '資料探勘', '文字探勘', 'linux',
                  '統計學', '資料分析', 'sap', 'sas', 'java', 'c++', 'c#']
    result = list(df.sum(axis=0, numeric_only=True))
    skills_amount = result[4:]
    output_dict = {}
    output_str = ''
    for i in range(len(skill_list)):
        output_dict[skill_list[i]] = skills_amount[i]

    sorted_one = sorted(output_dict, key=lambda x:output_dict[x], reverse=True)
    print(sorted_one)

    for i in sorted_one:
        output_str += '{} : {}'.format(i, output_dict[i]) + '\n'
    with open('./job_summary.txt','w', encoding='utf-8') as file:
        file.write(output_str)




def execute(searching_key, searching_numb):

    searching_keyword = searching_key
    searching_pages = int(searching_numb)

    getjob = getJobList(searching_keyword, searching_pages)

    description = getJobDescription(getjob)

    saveCSV(description)

    skillClassify('./jobsearch.txt')

    skillCount('./job_skills.txt', searching_numb)

    result_df = pd.read_csv('./skill_bool.txt')

    getSummary('./skill_bool.txt')

    return result_df


if __name__ == '__main__':
    result = execute('資料分析師', 5)









