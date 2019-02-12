import json

with open('/var/lib/secrets/secrets.json') as f:
    data = json.load(f)

user = data['secret/chef/jira/jira-reporter']['user']
password = data['secret/chef/jira/jira-reporter']['password']

JIRA_CONFIG = {
    'url':       'https://wikia-inc.atlassian.net',
    'user':      user,
    'password':  password,
    'project':   'ER',
    'fields': {
        'default': {
            'issuetype': {'name': 'Defect'},
            'priority':  {'id': '8'},  # P3
        },
        'custom': {
            'unique_id': 'customfield_13200',
            'url': 'customfield_11405',
            'last_seen': 'customfield_16900',  # ER Date
        },
        'CT': {
            'issuetype': {'name': 'Task'}
        }
    }
}

print(JIRA_CONFIG)
