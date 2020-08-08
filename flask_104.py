from flask import Flask, request

import job_search_104 as jb

app = Flask(__name__)

@app.route('/job', methods=['GET','POST'])
def jobSearch():

    #ob_title = request.form.get('job_title')
    #pages = request.form.get('pages')
    if request.method == 'GET':
        outStr="""
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width">
                <title>Job_Search_104</title>
                <link href="style.css" rel="stylesheet" type="text/css" />
            </head>
            <body>
                <h1>Welcome to 104 Job Search!!</h1>
                <form action="./job" method="post">
                    <label>Searching Job Title: </label>
                    <input name="job_title" type="text">
                    <br>
                    <label>Pages(<15): </label>
                    <input name="pages" type="number">  
                    <br>
                    <button type="submit">Submit</button> 
                </form>
                <script src="script.js"></script>
            </body>
            </html>"""
        return outStr

    elif request.method == 'POST':
        job_title = request.form.get('job_title')
        pagenumb = request.form.get('pages')
        result = jb.execute(job_title, pagenumb)
        return result




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)