# A script that fetches the last workflow status from CI systems
# and stores it in Elasticsearch

# Uses the REST API of the CI providers to get the data:
# - Github Action: https://docs.github.com/en/rest/actions/workflow-runs?apiVersion=2022-11-28
# - CircleCI: https://circleci.com/docs/api/v2/index.html

from datetime import datetime, timedelta
import os
import requests
import re
from requests.auth import HTTPBasicAuth
import sys

now = datetime.now()
today_str = now.strftime("%Y-%m-%d")
now_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

github_projects = [
    'gromacs/gromacs',
    'emqx/emqx',
    'SimpleITK/SimpleITK',
    'opencv/opencv',
    'lh3/bwa',
    'nwchemgit/nwchem',
    '3dem/relion',
    'su2code/SU2',
    'ccsb-scripps/AutoDock-Vina',
    'popgenmethods/smcpp',
    'ekg/seqwish',
    'wyp1125/MCScanX',
    'kehrlab/PopIns2',
    'DecodeGenetics/graphtyper',
    'jharno/cubep3m',
    'seaweedfs/seaweedfs',
    'goharbor/harbor-arm',
    'hashicorp/consul',
    'biod/sambamba',
]

circleci_projects = [
    'cloudera/hue'
]

github_headers = {
    'Accept': 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'Authorization': 'Bearer ' + os.getenv('GITHUB_TOKEN'),
}

github_workflow_parameters = {
    # 'created': '>' + (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d"),
    'event': 'push',
    'per_page': 10,
    'status': 'completed',
    'exclude_pull_requests': 'true',
}

github_workflow_jobs_parameters = {
    'filter': 'latest',
}

circleci_headers = {
    'Content-Type': 'application/json',
    'Circle-Token': os.getenv('CIRCLECI_TOKEN'),
}

es_bulk_req_headers = {
    'Content-Type': 'application/x-ndjson'
}

arm64_regex = re.compile(r'arm|aarch', re.IGNORECASE)

es_user = os.getenv('ES_USER')
es_password = os.getenv('ES_PASSWORD')
es_url = os.getenv('ES_URL') # e.g. http://localhost:9200
es_basic_auth = HTTPBasicAuth(es_user, es_password)
es_bulk_command = '{ "index" : { "_index" : "aarch64-ci-status-'+today_str+'" } }\n'

def github(project_name):
    """
    Gets the status of the last completed run of a Github Actions workflow
    for the provided project.
    If there are more than one jobs in the workflow then it tries to find a
    job with ARM64/aarch64 in its name (case insensitive)
    """
    debug('Project name: ' +project_name)
    workflow_url = 'https://api.github.com/repos/' + project_name + '/actions/runs'
    workflow_resp = requests.get(workflow_url, headers=github_headers, params=github_workflow_parameters)
    workflow_json = workflow_resp.json()
    results = []
    try:
        workflows = workflow_json['workflow_runs']
        
        # a list of already seen workflows by name
        # we process only the first (latest executed) one
        seen_workflows = []

        for run in workflows:
            workflow_name = run['name']
            debug("\tWorkflow name: " + workflow_name)
            debug("\tWorkflow created at: " + run['created_at'])

            if workflow_name in seen_workflows:
                continue
            seen_workflows.append(workflow_name)

            is_arm64_workflow = arm64_regex.search(workflow_name)

            jobs_url = run['jobs_url']
            jobs_resp = requests.get(jobs_url, headers=github_headers, params=github_workflow_jobs_parameters)
            jobs_json = jobs_resp.json()

            for job in jobs_json['jobs']:
                job_name = job['name'].replace("\n", " ")
                debug("\t\tJob name: " + job_name)

                runs_on = job['labels']
                runs_on_arm64 = arm64_regex.search("".join(runs_on))
                
                if is_arm64_workflow or runs_on_arm64 or arm64_regex.search(job_name):
                    results.append({
                        "job_name": job_name,
                        "status":   job['conclusion']
                    })

    except BaseException as ex:
        debug('An error occurred while reading the status of Github project "' + project_name + '": ')
        debug(ex)
    return results

def circleci(project_name):
    """
    Gets the status of the last completed run of a Github Actions workflow
    for the provided project.
    If there are more than one jobs in the workflow then it tries to find a
    job with ARM64/aarch64 in its name (case insensitive)
    """
    debug('Project name: ' +project_name)
    pipeline_url = 'https://circleci.com/api/v2/project/gh/' + project_name + '/pipeline'
    pipeline_resp = requests.get(pipeline_url, headers=circleci_headers)
    pipeline_json = pipeline_resp.json()
    # debug(pipeline_json)
    results = []
    try:
        pipelines = pipeline_json['items']
        
        # a list of already seen workflows by name
        # we process only the first (latest executed) one
        seen_workflows = []

        for pipeline in pipelines:
            pipeline_id = pipeline['id']

            workflows_url = 'https://circleci.com/api/v2/pipeline/'+pipeline_id+'/workflow'
            workflows_resp = requests.get(workflows_url, headers=circleci_headers)
            workflows_json = workflows_resp.json()

            for workflow in workflows_json['items']:
                workflow_id = workflow['id']
                workflow_name = workflow['name']
                debug("\tWorkflow name: " + workflow_name)
                debug("\tWorkflow created at: " + workflow['created_at'])
                
                if workflow_name in seen_workflows:
                    continue
                seen_workflows.append(workflow_name)

                is_arm64_workflow = arm64_regex.search(workflow_name)

                jobs_resp = requests.get('https://circleci.com/api/v2/workflow/'+workflow_id+'/job', headers=github_headers)
                jobs_json = jobs_resp.json()

                for job in jobs_json['items']:
                    job_name = job['name'].replace("\n", " ")
                    debug("\t\tJob name: " + job_name)

                    if is_arm64_workflow or arm64_regex.search(job_name):
                        results.append({
                            "job_name": job_name,
                            "status":   job['status']
                        })

    except BaseException as ex:
        debug('An error occurred while reading the status of Github project "' + project_name + '": ')
        debug(ex)
    return results
    
def es_index(bulk_req_body):
    """
    Indexes the statuses of all monitored projects into Elasticsearch index 
    named 'aarch64-ci-status-<DATE>`
    """
    if len(bulk_req_body) > 0:
        resp = requests.post(es_url + '/_bulk/', headers=es_bulk_req_headers, data=bulk_req_body, auth=es_basic_auth, verify=False)
        json = resp.json()
        debug(json)

def bulk_snippet(project_name, ci_jobs, ci_provider):
    result = ''

    for job in ci_jobs:
        result += es_bulk_command
        result += '{ "project_name": "'+project_name+'", "status": "'+ job['status'] +'", "ci_job_name": "'+ job['job_name'] +'", "ci_provider": "'+ ci_provider + '", "timestamp": "'+now_str+'" }\n'

    return result

def main():
    bulk_req_body = ''

    debug("Checking Github Actions based projects...")
    for project_name in github_projects:
        ci_jobs = github(project_name)
        bulk_req_body += bulk_snippet(project_name, ci_jobs, 'github-actions')
        
    debug("\nChecking CircleCI based projects...")
    for project_name in circleci_projects:
        ci_jobs = circleci(project_name)
        bulk_req_body += bulk_snippet(project_name, ci_jobs, 'circleci')

    bulk_req_body += '\n'
    debug(bulk_req_body)
    es_index(bulk_req_body)

def debug(args):
    print(args, file=sys.stderr)
    return True

if __name__ == "__main__":
    main()
