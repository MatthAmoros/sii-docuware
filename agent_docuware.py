import requests
import json
import datetime
import sys
from urllib.parse import urlencode
from config import DOCUWARE_USERNAME, DOCUWARE_PASSWORD, DOCUWARE_ENDPOINT, DOCUWARE_ORGANIZATION

class AgentDocuware:    
    """ Used to store HTTP session """
    __http_session = ''
    __endpoint = DOCUWARE_ENDPOINT
    __assets = {}

    def __init__(self):
        self.__auth_with_docuware()
        self.__load_assets()

    def __auth_with_docuware(self):
        """ POST login/password and build session """
        self.__http_session = requests.Session()

        """ Basic authentication data """
        data = { 
                "Username": DOCUWARE_USERNAME,
                "Password": DOCUWARE_PASSWORD,
                "LicenseType": "EmailArchivingServer"
                 }

        """ Headers, somehow User-Agent is important """
        h = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "User-Agent": DOCUWARE_ORGANIZATION
             }
        
        """ Build full URL """
        full_url = self.__endpoint + '/Account/Logon'

        """ POST request to our enpoint """
        r = self.__http_session.post(url=full_url, params=data, headers=h)
        print("__auth_with_docuware:: HTTP " + str(r.status_code))

        """ Set authenticated flag """
        self.__http_session.authenticated = r.status_code == 200
        return r.status_code

    def get_organization(self):
        """ Retrives organization information """
        if self.__http_session.authenticated:
            asset = '/Organizations'
            full_url = self.__endpoint + asset
            h = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "User-Agent": DOCUWARE_ORGANIZATION
                }
            """ Send request """
            r = self.__http_session.get(url=full_url, headers=h)

            if r.status_code == 200:
                """ HTTP_OK, continue process """
                organizations = json.loads(r.text)
            else:
                organizations = {"Organization":[{"Links":[{"rel":"filecabinets","href":"/DocuWare/Platform/FileCabinets"},{"rel":"self","href":"/DocuWare/Platform/Organization"},{"rel":"users","href":"/DocuWare/Platform/Organization/Users"},{"rel":"dialogs","href":"/DocuWare/Platform/Organization/Dialogs"},{"rel":"roles","href":"/DocuWare/Platform/Organization/Roles"},{"rel":"groups","href":"/DocuWare/Platform/Organization/Groups"},{"rel":"substitutionLists","href":"/DocuWare/Platform/Organization/SubstitutionLists"},{"rel":"webSettings","href":"/DocuWare/Platform/Organization/WebSettings"},{"rel":"loginToken","href":"/DocuWare/Platform/Organization/LoginToken"},{"rel":"userInfo","href":"/DocuWare/Platform/Organization/UserInfo"},{"rel":"selectListInfos","href":"/DocuWare/Platform/Organization/SelectLists"},{"rel":"workflows","href":"/DocuWare/Platform/Workflows"},{"rel":"controllerWorkflows","href":"/DocuWare/Platform/ControllerWorkflows"},{"rel":"workflowRequests","href":"/DocuWare/Platform/RequestsWorkflows"}],"Name":"Groupe La Blottière","Id":"9719","Guid":"a1f6996f-d29a-411d-bc44-f4c3525ba5d9"}]}
            
            self.__assets['Organizations'] = {}

            organization_k = 0
            for k in organizations['Organization']:
                organization = k
                """ Transform to lighter object, we keep only useful information """
                self.__assets['Organizations'][organization_k] = {'Id': organization['Id'], 'Guid': organization['Guid'], 'Name': organization['Name']}
                organization_k = organization_k + 1
                
        else:
            """ Not logged in """
            print("get_organization:: Not logged in.")

    def get_file_cabinet(self, organization_id=''):
        """ Get organization file cabinets """
        if self.__http_session:
            if len(organization_id) == 0:
                if 'Organizations' in self.__assets:
                    organization_id = self.__assets['Organizations'][0]['Id']
                else:
                    print("get_file_cabinet:: No organization id, and no organization loaded yet.")
                    return

            asset = '/FileCabinets?orgid=' + organization_id
            full_url = self.__endpoint + asset

            h = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "User-Agent": DOCUWARE_ORGANIZATION
                }

            r = self.__http_session.get(url=full_url, headers=h)   
            if r.status_code == 200:
                """ HTTP_OK, continue process """
                file_cabinets = json.loads(r.text)
                self.__assets['Organizations'][0]['FileCabinets'] = file_cabinets
            else:
                print("get_file_cabinet:: HTTP " + str(r.status_code))

    def disconnect(self):
        """ Disconnect from Docuware to free session """
        if self.__http_session.authenticated:
            target = '/Account/Logoff'
            full_url = self.__endpoint + target

            h = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "User-Agent": DOCUWARE_ORGANIZATION
                }

            """ Send request """
            r = self.__http_session.get(url=full_url, headers=h)

            if r.status_code == 200:
                print("disconnect:: HTTP OK")

    def upload_file(self, file_path, docuware_cabinet_id=''):
        """ Upload file to specified cabinet id """
        if self.__http_session.authenticated:
            if len(docuware_cabinet_id) == 0:
                """ Get first cabinet for first organization """
                docuware_cabinet_id = self.__assets['Organizations'][0]['FileCabinets']['FileCabinet'][0]['Id']
            
            target = '/filecabinets/' + docuware_cabinet_id + '/Documents'
            h = {
                "Content-Type": "application/pdf",
                "Accept": "application/json",
                "User-Agent": DOCUWARE_ORGANIZATION
            }

            full_url = self.__endpoint + target
            file_binary = ''

            with open(file_path, 'rb') as f:
                file_binary = f.read()
            
            r = self.__http_session.post(url=full_url, headers=h, data=file_binary)
            if r.status_code == 200:
                print("upload_file:: HTTP OK")

    def __load_assets(self):
        """ Load docuware assets into memory """
        self.get_organization()
        self.get_file_cabinet()

    def print_assets(self):
        print(self.__assets)

if __name__ == '__main__':
    agent = AgentDocuware()
    try:
        agent.print_assets()
        agent.upload_file('C:\\test.pdf', docuware_cabinet_id='XXXXX-XXX-XXXX-XXXXX')
    except:
        agent.disconnect()
    agent.disconnect()
