# A script that fetches the last workflow status from CI systems
# and stores it in Elasticsearch

# Uses the REST API of the CI providers to get the data:
# - Github Action: https://docs.github.com/en/rest/actions/workflow-runs?apiVersion=2022-11-28

from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth
import sys

github_projects = [
    'martin-g/bioconda-utils',
    'apache/wicket',
    'apache/avro',
]

circleci_projects = [
]

github_headers = {
    'Accept': 'application/vnd.github+json',
    'X-GitHub-Api-Version' :'2022-11-28'
}

github_parameters = {
    'per_page': 1,
    'status': 'completed',
    'exclude_pull_requests': 'true'
}

es_bulk_req_headers = {
    'Content-Type': 'application/x-ndjson'
}

now = datetime.now()
today_str = now.strftime("%Y-%m-%d")
now_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

bulk_command = '{ "index" : { "_index" : "aarch64-ci-status-'+today_str+'" } }\n'

basic_auth = HTTPBasicAuth('elastic', 'C1VzGS4gm679Z0GTcPpA')

def github(project):
    """
    Gets the status of the last completed run of a Github Actions workflow
    for the provided project
    """
    url = 'https://api.github.com/repos/' + project + '/actions/runs'
    resp = requests.get(url, headers=github_headers, params=github_parameters)
    json = resp.json()
    # debug(json)
    status = 'unknown'
    try:
        status = json['workflow_runs'][0]['conclusion']
    except e:
        debug('An error occurred while reading the status of Github project "' + projectName + '": ' + e)
    return status

def circleci(projectName):
    return 'TODO'
    
def es_index(bulk_req_body):
    """
    Indexes the statuses of all monitored projects into Elasticsearch index 
    named 'aarch64-ci-status-<DATE>`
    """
    url = 'http://localhost:9200/_bulk/'
    resp = requests.post(url, headers=es_bulk_req_headers, data=bulk_req_body, auth=basic_auth)
    json = resp.json()
    debug(json)

def bulk_snippet(projectName, status, ci_provider):
    bulk_snippet = bulk_command
    bulk_snippet += '{ "projectName": "'+projectName+'", "status": "'+status+'", "ci_provider": "'+ ci_provider + '", "timestamp": "'+now_str+'" }\n'
    return bulk_snippet

def main():
    bulk_req_body = ''

    for projectName in github_projects:
        status = github(projectName)
        bulk_req_body += bulk_snippet(projectName, status, 'github-actions')
        
    for projectName in circleci_projects:
        status = circleci(projectName)
        bulk_req_body += bulk_snippet(projectName, status, 'circleci')

    bulk_req_body += '\n'
    debug(bulk_req_body)
    es_index(bulk_req_body)

def debug(text):
    print(text, file=sys.stderr)

if __name__ == "__main__":
    main()
