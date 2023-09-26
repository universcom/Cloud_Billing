import os
#dirpath = os.getcwd()
dirpath = "/usr/local/bin/billing-scripts"
activate_this = dirpath + "/env/bin/activate_this.py"
execfile(activate_this, dict(__file__=activate_this))

import sys
import ConfigParser
from openstack import connection

class Initializer():

    def __init__(self):
        self.tenantsInfo = [] # dict key is tenant id and value is a array contains ( tenantId:{'userId':userId ,'discountPercentage': ,'sla': , 'isPayg': }} )
        self.openstackAuth = None
        self.config = None
        self.prices = None
        self.config_file_parser()
        self.price_file_parser()
        self.tenants_file_parser()
        self.openstack_auth()

    def config_file_parser(self):
        # this function parse configs from config file
        if os.path.isfile('./billing.conf'):
            #conf_path = os.getcwd()
            conf_path = "/usr/local/bin/billing-scripts"
            configParser = ConfigParser.RawConfigParser()
            configFilePath = conf_path + "/billing.conf"
            configParser.read(configFilePath)
            self.config = configParser
        else:
            print "Problem on opening Config File"
            sys.exit()
            # Send Email


    def price_file_parser(self):
        # this function parse prices from price file
        if os.path.isfile('./price.conf'):
            #conf_path = os.getcwd()
            conf_path = "/usr/local/bin/billing-scripts"
            priceParser = ConfigParser.RawConfigParser()
            priceFilePath = conf_path + "/price.conf"
            priceParser.read(priceFilePath)
            self.prices = priceParser
        else:
            print "Problem on opening Price File"
            sys.exit()
            # Send Email

    def tenants_file_parser(self):
        # this function parse project list file which filled by site
        try:
            os.system("scp root@xaas.ir:/tmp/payg_project_list.txt /usr/local/bin/billing-scripts")
            allTenantsInfo = open("/usr/local/bin/billing-scripts/payg_project_list.txt" , "r")
            for tenantInfo in allTenantsInfo:
                tenantInfo = tenantInfo.split()
                # self.tenantsInfo.append({tenantInfo[0]:{'userId':tenantInfo[1],'discountPercentage':tenantInfo[2]}})
                self.tenantsInfo.append({tenantInfo[0]:{'userId':tenantInfo[1],'discountPercentage':tenantInfo[2],'sla':tenantInfo[3],'isPayg':tenantInfo[4]}})
        except IOError:
                print "Problem on tenants file parser"
                #Send Email

    def openstack_auth(self):
        # this function create openstack connection Object
        try:
            configs = self.config
            self.openstackAuth = connection.Connection(auth_url = configs.get('openstack_auth', 'auth_url'),
                                                 project_name = configs.get('openstack_auth', 'project_name'),
                                                 username = configs.get('openstack_auth', 'username'),
                                                 password = configs.get('openstack_auth', 'password'),
                                                 user_domain_id = configs.get('openstack_auth', 'user_domain_id'),
                                                 project_domain_id = configs.get('openstack_auth', 'project_domain_id'),
                                                 region_name = configs.get('openstack_auth', 'region_name'),
                                                 identity_api_version = configs.get('openstack_auth', 'identity_api_version'),
                                                 volume_api_version = configs.get('openstack_auth', 'volume_api_version')
                                                 )
        except Exception as e:
            print " Problem on Openstack Auth : " + str(e)
            # Send email

    def get_openstack_auth(self):
        return self.openstackAuth

    def get_tenant_info_list(self):
        return self.tenantsInfo

    def get_config_file_contents(self):
        return self.config

    def get_prices(self):
        return self.prices
