import json

with open('/var/lib/secrets/secrets.json') as f:
    data = json.load(f)

user = data['secret/app/prod/jira-reporter']['user_email']
password = data['secret/app/prod/jira-reporter']['api_key']

JIRA_CONFIG = {
    'url':       'https://fandom.atlassian.net',
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
