import datetime
from ceilometerclient import client
from time import gmtime, strftime
import time
import threading
import json
from keystoneauth1 import session
from keystoneauth1 import identity
from novaclient import client as novaclient
from Bandwith import bandwith


class OpenstackResource:

    def __init__(self , tenantId , openstackConnectionObj,modelObj,mutex,log_mgmt):
        self.tenantId = tenantId
        self.openstackConnectionObj = openstackConnectionObj
        self.numberOfIP = None
        self.totalVolume = None
        self.subscription = None
        self.numberOfUsedCPU = None
        self.amountOfRam = None
        self.tenantInfo = {}
        self.instanceInfo = {}
        self.modelObj = modelObj
        self.limitOfRecordsForAvg = 1
        self.isAvg = False # this become true when there is problem on getting data of usage from ceilometer or openstack
        self.isAvgForSubscription = False # it is just like isAvg but this is for subscription because it has two way of calculation in noraml way and average way
        self.instancesStatus = None
        self.upload = None
        self.download = None
        self.mutex = mutex
        #self.log_mgmt = log_mgmt

    def calculate_all_resources(self,isPayg):
        self.status_of_tenant_instances()
        self.tenant_info()
        if isPayg:
            self.calc_number_of_ip()
            self.calc_total_volume()
            self.calc_subscription()
            self.calc_number_of_cpu()
            self.calc_amount_of_ram()
        self.calc_upload()
        self.calc_download()

    def status_of_tenant_instances(self):
        instanceStatusDict = {}
        try:
            tenantInstances = self.openstackConnectionObj.compute.servers(details=True, all_projects=True, project_id=self.tenantId)
            for instance in tenantInstances:
                instanceID = instance.id
                server = self.openstackConnectionObj.compute.get_server(instanceID)
                if server.status == "ACTIVE" and server.power_state == 1:
                    instanceStatusDict[instanceID] = 1
                elif server.status == "PAUSED" and server.power_state == 3:
                    instanceStatusDict[instanceID] = 2
                elif server.status == "SHUTOFF" and server.power_state == 4:
                    instanceStatusDict[instanceID] = 3
                elif server.status == "SUSPENDED" and server.power_state == 4:
                    instanceStatusDict[instanceID] = 4
                elif server.status == "ERROR":
                    instanceStatusDict[instanceID] = 0
                else:
                    instanceStatusDict[instanceID] = 5
            self.instancesStatus = instanceStatusDict
        except Exception as e:
            print "Problem on status_of_tenant_instances : " + str(e)

    def check_project_existance(self):
        if self.openstackConnectionObj.identity.find_project(self.tenantId) == None:
            #self.log_mgmt.info("tenant %s is not exists" %(self.tenantId))
            return False
        else:
            #self.log_mgmt.info("tenant %s is exists" %(self.tenantId))
            return True


    def calc_number_of_ip(self):
        try:
            projectFloatIp = self.openstackConnectionObj.network.ips(project_id=self.tenantId)
            ipCounter = 0
            for floatIp in projectFloatIp:
                ipCounter += 1
            self.numberOfIP = ipCounter
            #self.log_mgmt.info("tenant %s have %s IPs" %(self.tenantId ,str(self.numberOfIP)))
        except :
            #self.log_mgmt.info("connection to openstack refused for calculate number of IP ( Use Average of latest usage)")
            ''' read avg from pervious vlauses'''
            self.numberOfIP = self.calc_average_of_past_values("ip.floating","default")
            #self.log_mgmt.info("tenant %s have %s IPs that get from AVG mode" %(self.tenantId ,str(self.numberOfIP)))


    def calc_total_volume(self):
        try:
            volumes = self.openstackConnectionObj.block_storage.volumes(details=True , all_projects=True , project_id=self.tenantId)
            totalVolumesSize = 0
            for volume in volumes:
                totalVolumesSize += int(volume.size)
                #self.log_mgmt.info("tenant %s volume is %s GB" %(self.tenantId ,str(volume.size)))
            self.totalVolume = totalVolumesSize
            #self.log_mgmt.info("tenant %s have %s GB used Volume" %(self.tenantId ,str(self.totalVolume)))
        except:
            #self.log_mgmt.info("connection to openstack refused for calculate total volume ( Use Average of latest usage)")
            ''' read avg from pervious vlauses'''
            self.totalVolume = self.calc_average_of_past_values("volume.size","default")
            #self.log_mgmt.info("tenant %s have %s GB used Volume , get from AVG mode" %(self.tenantId ,str(self.totalVolume)))

    def calc_average_of_past_values(self,meterName,instanceId):
        # self.mutex.acquire()
        try:
            select_query ="SELECT AVG(meter_usage) FROM (SELECT meter_usage FROM res_usage WHERE meter_name = \"%s\" AND instance_id = \"%s\" ORDER BY id DESC LIMIT %s) as usages " % (meterName,instanceId,str(self.limitOfRecordsForAvg))
            self.modelObj.get_cursor().execute(select_query)
            # self.mutex.release()
            return self.modelObj.get_cursor().fetchall()[0][0]
        except Exception as e:
            print str(e)
            return 0

    def get_latest_value_from_database(self,meterName,instanceId):
        # self.mutex.acquire()
        try:
            select_query ="SELECT meter_usage FROM res_usage WHERE meter_name = \"%s\" AND instance_id = \"%s\" AND tenant_id = \"%s\" ORDER BY id DESC LIMIT 1 "% (meterName,instanceId,self.tenantId)
            self.modelObj.get_cursor().execute(select_query)
            # self.mutex.release()
            return self.modelObj.get_cursor().fetchall()[0][0]
        #except IndexError:
        except Exception as e :
            print str(e)
            return 0
    def calc_subscription(self):
        #instance
        #SELECT AVG(meter_usage) FROM `res_usage` WHERE `meter_name` = 'cpu_util'

        try:
            serversResources = self.openstackConnectionObj.get_compute_quotas(self.tenantId)
            cpu = serversResources.cores
            #self.log_mgmt.info("tenant %s have %s saled CPU" %(self.tenantId ,serversResources.cores))
            ram = float(serversResources.ram / 1024)
            #self.log_mgmt.info("tenant %s have %s saled RAM" %(self.tenantId ,str(ram)))
            serversStorage = self.openstackConnectionObj.get_volume_quotas(self.tenantId)
            volume = serversStorage.gigabytes
            #self.log_mgmt.info("tenant %s have %s saled Volume" %(self.tenantId ,str(volume)))
            self.subscription = [cpu , ram , volume]
        except:
            print "connection to openstack refused in calc subscription ( Use Average of latest usage)"
            ''' read avg from pervious vlauses'''
            self.isAvgForSubscription = True
            self.subscription = self.calc_average_of_past_values("instance","default")

    def calc_number_of_cpu(self):
        instanceCpuDict = {}
        try:
            print 1
            projectInstances = self.openstackConnectionObj.compute.servers(details=True, all_projects=True, project_id=self.tenantId)
            print 2
            for instance in projectInstances:
                NumberOfCpu = self.openstackConnectionObj.compute.get_flavor(instance.flavor['id']).vcpus
                print "number of instance is : " +  str(NumberOfCpu)
                instanceID = instance.id
                print "instance id is : " + str(instanceID)
                # first fill cpu var with avg of past values because of times that ceilometer didnt get data from hosts and it retrun nothing (0)
                cpu = self.calc_average_of_past_values("cpu_util",str(self.convert_instanceId_to_instanceKVMname(instanceID)))
                print "pervois cpu usage : " + str(cpu)
                #cpu = 0
                if cpu == None:
                    cpu = 0
                cpu_temp = self.calc_cpu_usage(instanceID)
                print "now cpu usage : " + str(cpu_temp)
                # this is just a temp solution for some 0 in diagram
                if cpu_temp != 0:
                    cpu = cpu_temp

                if self.isAvg:
                    if self.instancesStatus[instanceID] == 1 or self.instancesStatus[instanceID] == 2:
                        # print "AVG TRUE CPU "
                        cpu_pervios = float(cpu) * 100 / float(NumberOfCpu)
                        # print cpu_pervios
                        #instanceCpuDict[instanceID] = cpu
                        instanceCpuDict[instanceID] = [cpu_pervios , NumberOfCpu]
                    else:
                        instanceCpuDict[instanceID] = [0,0] #[cpu , NumberOfCpu]
                        # print "AVG TRUE CPU BUT INSTANCE IS NOT ACTIVE OR PAUSED"
                else:
                    #instanceCpuDict[instanceID] = (cpu * NumberOfCpu)/100
                    if self.instancesStatus[instanceID] == 1 or self.instancesStatus[instanceID] == 2:
                        instanceCpuDict[instanceID] = [cpu , NumberOfCpu]
                    else:
                        instanceCpuDict[instanceID] = [0,0]

            self.numberOfUsedCPU = instanceCpuDict
        except Exception as e :
            print "connection to openstack refused for calc cpu dict ( Use Average of latest usage)\n " + str(e)
        #     ''' read avg from pervious vlauses'''
        # print instanceCpuDict

    def calc_amount_of_ram(self):
        print (self.isAvg)
        instanceRamDict = {}
        try:
            projectInstances = self.openstackConnectionObj.compute.servers(details=True, all_projects=True, project_id=self.tenantId)
            for instance in projectInstances:
                instanceID = instance.id
                # first fill ram var with avg of past values because of times that ceilometer didnt get data from hosts and it retrun nothing (0)
                ram = self.calc_average_of_past_values("memory.usage",str(self.convert_instanceId_to_instanceKVMname(instanceID)))
                if ram == None:
                    ram = 0
                else:
                    ram = ram * 1024

                ram_temp = self.calc_ram_usage(instance.id)

                # this is just a temp solution for some 0 in diagram
                if float(ram_temp) != 0:
                    ram = ram_temp
                    # print ram

                if self.isAvg:
                    if self.instancesStatus[instanceID] == 1 or self.instancesStatus[instanceID] == 2 or self.instancesStatus[instanceID] == 4:
                        # print "AVG TRUE RAM "
                        # print ram
                        instanceRamDict[instanceID] = float(ram) / 1024
                    else:
                        instanceRamDict[instanceID] = 0
                        # print "AVG TRUE RAM BUT INSTANCE IS NOT ACTIVE OR PAUSED OR SUSPEND"
                else:
                    if self.instancesStatus[instanceID] == 1 or self.instancesStatus[instanceID] == 2 or self.instancesStatus[instanceID] == 4:
                        instanceRamDict[instanceID] = float(ram)/1024
                    else:
                        instanceRamDict[instanceID] = 0

            self.amountOfRam = instanceRamDict
        except Exception as e:
            print "connection to openstack refused for calc ram dict" + str(e)
        # print instanceRamDict


    def calc_cpu_usage(self , instanceId):
        try:
            cclient = client.get_client("2", os_username="admin", os_password="password, os_tenant_name="admin", os_auth_url="http://controller:5000/v2.0/")
            #nowGMTime = datetime.datetime.strptime(time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()), '%Y-%m-%dT%H:%M:%S')
            GMTime = datetime.datetime.strptime(time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()), '%Y-%m-%dT%H:%M:%S')
            nowGMTime = GMTime - datetime.timedelta(minutes=10)
            perviousGMTime = nowGMTime - datetime.timedelta(minutes=10)
            nowGMTime = nowGMTime.strftime("%Y-%m-%dT%H:%M:%S")
            perviousGMTime = perviousGMTime.strftime("%Y-%m-%dT%H:%M:%S")
            queryCPU = [dict(field='resource', op='eq', value=instanceId), dict(field='meter',op='eq',value='cpu_util'), dict(field='timestamp',op='le',value=nowGMTime) , dict(field='timestamp',op='ge',value=perviousGMTime)]
            cpuSamples = cclient.new_samples.list(q=queryCPU, limit=10)
            cpuSampleValueSum = 0
            cpuSampleCounter = 0
            cpuSampleAvg = 0
            for cpuSample in cpuSamples:
                print cpuSample.volume
                cpuSampleValueSum += cpuSample.volume
                cpuSampleCounter += 1
            if cpuSampleCounter == 0:
                cpuSampleCounter = 1
            cpuSampleAvg = cpuSampleValueSum / cpuSampleCounter
            #self.log_mgmt.info("total CPU used is : %s for instance : %s in tenant : %s " %(cpuSampleAvg , instanceId , self.tenantId ))
            return cpuSampleAvg
        except Exception as e:
            print str(e)
            self.isAvg = True
            #self.log_mgmt.info("connection to ceilometer refused for calc CPU usage  ( Use Average of latest usage)")
            cpuSample = self.calc_average_of_past_values("cpu_util",str(self.convert_instanceId_to_instanceKVMname(instanceId)))
            #self.log_mgmt.info("CPU used is : %s for instance : %s in tenant : %s get from AVG mode" %(cpuSample , instanceId , self.tenantId ))
            return cpuSample

    def calc_ram_usage(self , instanceId):
        try:
            cclient = client.get_client("2", os_username="admin", os_password="password", os_tenant_name="admin", os_auth_url="http://controller:5000/v2.0/")
            #nowGMTime = datetime.datetime.strptime(time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()), '%Y-%m-%dT%H:%M:%S')
            GMTime = datetime.datetime.strptime(time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()), '%Y-%m-%dT%H:%M:%S')
            nowGMTime = GMTime - datetime.timedelta(minutes=10)
            perviousGMTime = nowGMTime - datetime.timedelta(minutes=10)
            nowGMTime = nowGMTime.strftime("%Y-%m-%dT%H:%M:%S")
            perviousGMTime = perviousGMTime.strftime("%Y-%m-%dT%H:%M:%S")
            queryMemory = [dict(field='resource', op='eq', value=instanceId), dict(field='meter',op='eq',value='memory.usage'), dict(field='timestamp',op='le',value=nowGMTime) , dict(field='timestamp',op='ge',value=perviousGMTime)]
            memorySamples = cclient.new_samples.list(q=queryMemory, limit=10)
            memorySampleValueSum = 0
            memorySampleCounter = 0
            memorySampleAvg = 0
            for memorySample in memorySamples:
                memorySampleValueSum += memorySample.volume
                memorySampleCounter += 1
            if memorySampleCounter == 0:
                memorySampleCounter = 1
            memorySampleAvg = memorySampleValueSum / memorySampleCounter
            #self.log_mgmt.info("RAM used is : %s for instance : %s in tenant : %s " %(memorySampleAvg , instanceId , self.tenantId ))
            return memorySampleAvg
        except:
            self.isAvg = True
            #self.log_mgmt.info("connection to ceilometer refused for calc RAM usage ( Use Average of latest usage)")
            memorySample = self.calc_average_of_past_values("memory.usage",str(self.convert_instanceId_to_instanceKVMname(instanceId)))
            #self.log_mgmt.info("RAM used is : %s for instance : %s in tenant : %s get from AVG mode" %(memorySample , instanceId , self.tenantId ))
            return memorySample

    def calc_upload(self):
        uploadObj = bandwith("admin" , "password" , "admin" , "default" , "default" ,
                             "http://endpoint:5000")
        uploadObj.add_label(neutronClinetAPIObj = uploadObj.auth_to_neutron() , tenantId = self.tenantId)
        uploadLabelId = uploadObj.get_upload_tenant_lable_id(neutronClinetAPIObj = uploadObj.auth_to_neutron() ,
                                                             tenantId = self.tenantId)
        self.upload = uploadObj.get_tenant_usage(ceilometerClinetAPIObj=uploadObj.auth_to_ceilometer() ,
                                                  lableId=uploadLabelId)
        print "upload = " + str(self.upload)


    def get_cumulative_value(self , meter):
        if meter == "upload":
            return self.upload + self.get_latest_value_from_database("network.outgoing.bytes" , "default")
        if meter == "download":
            return self.download + self.get_latest_value_from_database("network.incoming.bytes" , "default")

    def calc_download(self):
        downloadObj = bandwith("admin", "password", "admin", "default", "default",
                             "http://endpoint:5000")
        downloadObj.add_label(neutronClinetAPIObj=downloadObj.auth_to_neutron(), tenantId=self.tenantId)
        downloadLabelId = downloadObj.get_download_tenant_lable_id(neutronClinetAPIObj=downloadObj.auth_to_neutron(),
                                                             tenantId=self.tenantId)
        self.download = downloadObj.get_tenant_usage(ceilometerClinetAPIObj=downloadObj.auth_to_ceilometer(),
                                                  lableId=downloadLabelId)
        print "download = " + str(self.download)

    def tenant_info(self):
        try:
            tenantName = self.openstackConnectionObj.get_project(self.tenantId)['name']
            #self.log_mgmt.info("Tenant %s name is : %s" %(self.tenantId ,tenantName))
            self.tenantInfo['tenantName'] = tenantName
            # print self.tenantInfo['tenantName']
        except:
            pass
            #self.log_mgmt.info("connection to openstack refused for get tenant info")

    def convert_instanceId_to_instanceKVMname(self,instanceId):
        try:
            instance = self.openstackConnectionObj.compute.get_server(instanceId)
            #self.log_mgmt.info("In tenant %s instance %s converted to %s KVM name" %(self.tenantId , instanceId , instance.instance_name))
            return instance.instance_name
        except Exception as e:
            pass
            #self.log_mgmt.info("In tenant %s for instance %s Problem on converting Instanceid to Instance KVM Name : %s " %(self.tenantId , instanceId ,str(e)))

    def set_instance_info(self , instance_id):
        try:
            filter = {"project_id" : self.tenantId}
            instance = self.openstackConnectionObj.get_server(name_or_id=instance_id, filters=filter ,all_projects=True)
            instaneName = instance.name
            instanceKvmName = instance.instance_name
            instanceCreatedDate = instance.created
            self.instanceInfo['name'] = instaneName
            self.instanceInfo['kvmName'] = instanceKvmName
            self.instanceInfo['createdDate'] = datetime.datetime.strptime(instanceCreatedDate, '%Y-%m-%dT%H:%M:%SZ').strftime("%Y-%m-%d %H:%M:%S")
        except:
            print "connection to openstack refused for get instance info"


    def get_number_of_ip(self):
        return self.numberOfIP

    def get_total_volume(self):
        return self.totalVolume

    def get_subscription(self):
        return self.subscription

    def get_number_of_cpu(self):
        return self.numberOfUsedCPU

    def get_amount_of_ram(self):
        return self.amountOfRam

    def get_tenant_info(self):
        return self.tenantInfo

    def get_instance_info(self):
        return self.instanceInfo

    def get_isAvg(self):
        return self.isAvg

    def get_isAvgForSubscription(self):
        return self.isAvgForSubscription

    def get_upload(self):
        return self.upload

    def get_download(self):
        return self.download

    def get_instance_status(self):
        return self.instancesStatus