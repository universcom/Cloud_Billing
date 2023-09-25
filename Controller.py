import os
import thread
import threading
#dirpath = os.getcwd()
dirpath = "/usr/local/bin/billing-scripts"
activate_this = dirpath + "/env/bin/activate_this.py"
execfile(activate_this, dict(__file__=activate_this))

from Initializer import Initializer
from OpenstackResource import OpenstackResource
from PriceCalc import PriceCalc
from Model import Model
import datetime , time
from time import gmtime
from filelock import FileLock
import logging



class Controller:
    def __init__(self):
        self.initializer = Initializer()
        # self.openstackResource = None
        # self.priceCalc = None
        # self.model = None
        self.tenantInfoList = None # array
        self.mutex = threading.Lock()
        self.numberOfThreads = 10
        # self.dict = {}

        # self.dict = {'fromStamp': '2019-09-24 10:20:33', 'toStamp': '2019-09-24 10:21:33', 'ip': 3, 'volumePrice': 55.34274193548387, 'subscriptionPrice': 10.013440860215056, 'userId': '7d802ba1a4cb252e515b04d17ba7c516', 'tenantId': 'dd8c5b29ae9241698c5ed9740b2f42d5', 'volume': 183, 'tenantName': u'VPC_hamid.karampour@vwideas.com', 'updateDate': '2019-09-24 10:20:33', 'insatnces': [{'cpuPrice': 97.57134693741588, 'insatnceId': u'fd38469e-aea8-46ee-b25b-ade6086b1d82', 'ram': 7.0205078125, 'updateDate': '2019-09-24 10:20:42', 'instacneName': u'db1-server_new', 'instacneKvmName': u'instance-00003a44', 'creationDate': '2019-08-26 20:44:24', 'cpu': 0.6481525189414055, 'ramPrice': 58.976040091565864}, {'cpuPrice': 21.248557376221527, 'insatnceId': u'9082c3d9-c822-4658-b304-aa3de52610dd', 'ram': 3.5673828125, 'updateDate': '2019-09-24 10:20:47', 'instacneName': u'web1-server', 'instacneKvmName': u'instance-00003a40', 'creationDate': '2019-08-26 20:04:23', 'cpu': 0.14115113114204297, 'ramPrice': 29.967933572748656}], 'ipPrice': 10.080645161290322}

    def log_management(self):
        try:
            logFile = self.initializer.get_config_file_contents().get('default', 'log_file')
            debugMode = self.initializer.get_config_file_contents().get('default', 'debug_mode')
            if self.debug_mode(debugMode) :
                logging.basicConfig(filename=logFile, filemode='aw', format='%(asctime)s - %(levelname)s : %(message)s', datefmt='%d-%b-%y %H:%M:%S' , level=logging.INFO)
                print "debug mode enabled"
            else:
                logging.basicConfig(filename=logFile, filemode='aw', format='%(asctime)s : %(message)s', datefmt='%d-%b-%y %H:%M:%S' , level=logging.WARNING)
                print "info mode enabled"
            return logging
        except Exception as e:
            print "cann`t read config file : " + str(e)


    def main_proccess_for_each_tenant(self,tenantInfo,openstackConnectionObj,log_mgmt):
        dict = {}
        tenantId = tenantInfo.keys()[0]
        # print tenantId
        tenantSla = int(tenantInfo[tenantInfo.keys()[0]]['sla'])
        isTenantPayg = tenantInfo[tenantInfo.keys()[0]]['isPayg']
        if isTenantPayg == '0':
            isTenantPayg = False
            log_mgmt.info("tenant %s is not PAYG" %(tenantInfo.keys()[0]))
        else:
            isTenantPayg = True
            log_mgmt.info("tenant %s is a PAYG" %(tenantInfo.keys()[0]))
        model = Model(self.initializer.get_config_file_contents())
        log_mgmt.info("openstack fualty database model get config for tenant %s and initialized" %(tenantInfo.keys()[0]))
        openstackResource = OpenstackResource(tenantId,openstackConnectionObj,model,self.mutex,log_mgmt)
        log_mgmt.info("openstack resource initialized for tenant %s" %(tenantInfo.keys()[0]))
        if openstackResource.check_project_existance():
            openstackResource.calculate_all_resources(isTenantPayg)
            log_mgmt.info("openstack resource calculated for tenant %s" %(tenantInfo.keys()[0]))
            priceCalc = PriceCalc()
            log_mgmt.info("resource price initialized for tenant %s" %(tenantInfo.keys()[0]))
            self.calculate_prices(tenantInfo[tenantInfo.keys()[0]]['discountPercentage'],isTenantPayg,tenantSla,openstackResource,priceCalc)
            log_mgmt.info("resource price calculated for tenant %s" %(tenantInfo.keys()[0]))
            dict = self.fill_dict(tenantInfo,isTenantPayg,dict,openstackResource,priceCalc)
            model.disconnect_from_database()
            log_mgmt.info("openstack fualty database model was closed for tenant %s" %(tenantInfo.keys()[0]))
            model = Model(self.initializer.get_config_file_contents())
            log_mgmt.info("database model get config for tenant %s and initialized" %(tenantInfo.keys()[0]))
            model.set_tenant_usages_dict(dict)
            log_mgmt.info("usage tenant dist established for tenant %s" %(tenantInfo.keys()[0]))
            model.insert_to_tenants_table()
            log_mgmt.info("tenant usege add to tenants table for tenant %s" %(tenantInfo.keys()[0]))
            model.insert_to_tenantinstance_table()
            log_mgmt.info("tenant instance usege add to tenants instance table for tenant %s" %(tenantInfo.keys()[0]))
            model.insert_to_res_usage_table(isTenantPayg)
            log_mgmt.info("resorce usage add to resusge for tenant %s" %(tenantInfo.keys()[0]))
            model.disconnect_from_database()
            log_mgmt.info("database model was closed for tenant %s" %(tenantInfo.keys()[0]))
            log_mgmt.info("opration done for tenant %s" %(tenantInfo.keys()[0]))
        else:
            log_mgmt.info("tenant %s is not exists" %(tenantInfo.keys()[0]))
            print "project not exsit"

    def main_proccess(self):
        log_mgmt = self.log_management()
        log_mgmt.warning("############## billing started ##############")

        self.tenantInfoList = self.initializer.get_tenant_info_list()
        log_mgmt.info("tenants list initialized.")

        openstackConnectionObj = self.initializer.get_openstack_auth()
        log_mgmt.info("openstack object conncetion initialized")

        threads_list = []
        log_mgmt.info("start add tenants to threads")
        threadNumberCounter = 0
        for tenantInfo in self.tenantInfoList:
            threads_list.append(threading.Thread( target = self.main_proccess_for_each_tenant, args = (tenantInfo,openstackConnectionObj,log_mgmt)))
            threadNumberCounter+=1
            log_mgmt.info("tenant %s add to thread" %(tenantInfo.keys()[0]))
            if threadNumberCounter == self.numberOfThreads:
                for thread in threads_list:
                    thread.start()
                for thread in threads_list:
                    thread.join()
                threads_list = []
                threadNumberCounter = 0

        # these lines for those project at the end of file that didnt come in group of 10
        for thread in threads_list:
            thread.start()
        for thread in threads_list:
            thread.join()



            # self.dict={'fromStamp': '2019-09-24 13:46:31', 'toStamp': '2019-09-24 13:47:31', 'ip': 3, 'volumePrice': 55.34274193548387, 'subscriptionPrice': 10.013440860215056, 'userId': '7d802ba1a4cb252e515b04d17ba7c516', 'tenantId': 'dd8c5b29ae9241698c5ed9740b2f42d5', 'volume': 183, 'tenantName': u'VPC_hamid.karampour@vwideas.com', 'updateDate': '2019-09-24 13:46:31', 'instances': [{'cpuPrice': 0.0, 'insatnceId': u'fd38469e-aea8-46ee-b25b-ade6086b1d82', 'ram': 0.009765625, 'updateDate': '2019-09-24 13:47:13', 'instanceName': u'db1-server_new', 'instanceKvmName': u'instance-00003a44', 'creationDate': '2019-08-26 20:44:24', 'cpu': 0, 'ramPrice': 0.0820365003360215}, {'cpuPrice': 0.0, 'insatnceId': u'9082c3d9-c822-4658-b304-aa3de52610dd', 'ram': 0.009765625, 'updateDate': '2019-09-24 13:47:51', 'instanceName': u'web1-server', 'instanceKvmName': u'instance-00003a40', 'creationDate': '2019-08-26 20:04:23', 'cpu': 0, 'ramPrice': 0.0820365003360215}], 'ipPrice': 10.080645161290322}


    def fill_dict(self,tenantInfo,isPayg,dict,openstackResource,priceCalc):
        # this function fill project inforamtion dictionary for passing to Model Class
        try:
            tenantId = tenantInfo.keys()[0]
            dict['tenantId'] = tenantId
            dict['tenantName'] = openstackResource.get_tenant_info()['tenantName']
            dict['userId'] = tenantInfo[tenantId]['userId']
            dict['updateDate'] = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            startTime =  datetime.datetime.fromtimestamp(time.time()) - datetime.timedelta(hours=3 , minutes=30)
            dict['fromStamp'] = startTime.strftime('%Y-%m-%d %H:%M:%S')
            #self.dict['fromStamp'] = startTime.strptime(time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()), '%Y-%m-%dT%H:%M:%S')
            dict['toStamp'] = (startTime + datetime.timedelta(seconds=int(self.initializer.get_config_file_contents().get('default','interval')))).strftime('%Y-%m-%d %H:%M:%S')
            dict['instances'] = self.fill_instance_array(isPayg,openstackResource,priceCalc)
            if isPayg:
                dict['subscriptionPrice'] = priceCalc.get_subscription_price()
                dict['ip'] = openstackResource.get_number_of_ip()
                dict['ipPrice'] = priceCalc.get_ip_price()
                dict['volume'] = openstackResource.get_total_volume()
                dict['volumePrice'] = priceCalc.get_volume_price()

            # print self.dic
            return dict

        except Exception as e:
            print "problem in fill dict : " + str(e)
            return dict

    def fill_instance_array(self,isPayg,openstackResource,priceCalc):
        try:
            ### Fill instances
            uploadPriceOfInstanceDict = priceCalc.get_upload_price()
            uploadOfInstanceDict = openstackResource.get_upload()
            downloadPriceOfInstanceDict = priceCalc.get_download_price()
            downloadOfInstanceDict = openstackResource.get_download()
            if isPayg:
                numberOfCpuInstanceDict = openstackResource.get_number_of_cpu()
                numberOfCpuPriceInstanceDict = priceCalc.get_cpu_price()
                numberOfRamInstanceDict = openstackResource.get_amount_of_ram()
                numberOfRamPriceInstanceDict = priceCalc.get_ram_price()

            instancesArray = []
            for instanceId in uploadOfInstanceDict.keys():
                openstackResource.set_instance_info(instanceId)
                instanceName = openstackResource.get_instance_info()['name']
                instanceKvmName = openstackResource.get_instance_info()['kvmName']
                uploadOfInstance = uploadOfInstanceDict[instanceId]
                uploadPriceOfInstance = uploadPriceOfInstanceDict[instanceId]
                downloadOfInstance = downloadOfInstanceDict[instanceId]
                downloadPriceOfInstance = downloadPriceOfInstanceDict[instanceId]
                creationDate = openstackResource.get_instance_info()['createdDate']
                updateDate = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

                if isPayg:
                    numberOfRamInstance = numberOfRamInstanceDict[instanceId]
                    numberOfRamPriceInstance = numberOfRamPriceInstanceDict[instanceId]
                    numberOfCpuInstance = numberOfCpuInstanceDict[instanceId]
                    numberOfCpuPriceInstance = numberOfCpuPriceInstanceDict[instanceId]
                    instancesArray.append({'instanceName':instanceName,'instanceKvmName':instanceKvmName,'instanceId':instanceId
                    ,'creationDate': creationDate,'updateDate':updateDate,'cpu':numberOfCpuInstance
                    ,'cpuPrice':numberOfCpuPriceInstance,'ram':numberOfRamInstance
                    ,'ramPrice':numberOfRamPriceInstance,'upload':uploadOfInstance,'uploadPrice':uploadPriceOfInstance
                    ,'download':downloadOfInstance,'downloadPrice':downloadPriceOfInstance
                    })
                else:
                    instancesArray.append({'instanceName':instanceName,'instanceKvmName':instanceKvmName,'instanceId':instanceId
                    ,'creationDate': creationDate,'updateDate':updateDate
                    ,'upload':uploadOfInstance,'uploadPrice':uploadPriceOfInstance
                    ,'download':downloadOfInstance,'downloadPrice':downloadPriceOfInstance
                    })
            return instancesArray
        except Exception as e:
            print "problem in fill instance array : " + str(e)
            return None

    def calculate_prices(self ,discount ,isPayg, tenantSla, openstackResource, priceCalc):
        try:
            priceCalc.set_billing_conf(self.initializer.get_config_file_contents())
            priceCalc.set_unit_price(self.initializer.get_prices())
            priceCalc.set_discount(float(discount))
            priceCalc.set_sla(tenantSla)
            priceCalc.calc_upload_price(openstackResource.get_upload())
            priceCalc.calc_download_price(openstackResource.get_download())
            if isPayg:
                priceCalc.calc_cpu_price(openstackResource.get_number_of_cpu())
                priceCalc.calc_ram_price(openstackResource.get_amount_of_ram())
                priceCalc.calc_ip_price(openstackResource.get_number_of_ip())
                priceCalc.calc_subscription_price(openstackResource.get_subscription(),openstackResource.get_isAvgForSubscription())
                priceCalc.calc_volume_price(openstackResource.get_total_volume())
            priceCalc.apply_sla_multiply(isPayg)
        except Exception as e:
            print "problem on calc_price : " + str(e)

    def debug_mode(self , mode):
        if mode in ['true' , 'True' , 'TRUE' , '1']:
            return True
        else:
            return False

lock_path = "billing.lock"
lock = FileLock(lock_path, timeout=1)
with lock:
    obj = Controller()
    obj.main_proccess()
