import datetime , time
from mysql.connector import *
import copy


class Model:
    def __init__(self , configFile):
        self.configFile = configFile
        self.connectionObj = None
        self.cursor = None
        self.tenantUsagesDict = None
        self.database_connection()

    def get_cursor(self):
        return self.cursor

    def set_tenant_usages_dict(self, tenantUsagesDict):
        self.tenantUsagesDict = tenantUsagesDict

########### We Handle it
# select query to table tenants if it doesnt exist we should create a row in table with creation_date and update_date datetime.now
# for each tenant update_date in tenants table should update with datetime.now
###########

    def database_connection(self):
        try:
            self.connectionObj = connect(user=self.configFile.get('database', 'db_username'),
                                             password=self.configFile.get('database', 'db_password'),
                                             host=self.configFile.get('database', 'db_address'),
                                             database=self.configFile.get('database', 'db_name'))

            self.cursor = self.connectionObj.cursor()
        except:
            print "Problem on Database Connection"

    def query_cpu_to_res_usage(self,tenantInstance):
        try:
            cpu = float(tenantInstance['cpu'][0]) * float(tenantInstance['cpu'][1]) / 100
            insert_query = ("INSERT INTO `res_usage` (`tenant_id` , `instance_id`, `meter_name` ,\
                            `from_stamp` , `to_stamp` , `meter_usage` , `bill`) VALUES (\"%s\" ,\"%s\" ,\"%s\" , \"%s\" , \"%s\" , %0.2f , %0.2f)"\
                            %(self.tenantUsagesDict['tenantId'] , tenantInstance['instanceKvmName'] , "cpu_util" ,\
                            self.tenantUsagesDict['fromStamp'] , self.tenantUsagesDict['toStamp'] , cpu , tenantInstance['cpuPrice']))
            return insert_query
        except:
            print "Problem on query cpu res usage"

    def query_download_to_res_usage(self,tenantInstance):
        try:
            insert_query = ("INSERT INTO `res_usage` (`tenant_id` , `instance_id`, `meter_name` ,\
            `from_stamp` , `to_stamp` , `meter_usage` , `bill`) VALUES (\"%s\" ,\"%s\" ,\"%s\" , \"%s\" , \"%s\" , %0.2f , %0.2f)"\
            %(self.tenantUsagesDict['tenantId'] , tenantInstance['instanceKvmName'] , "network.incoming.bytes" ,\
            self.tenantUsagesDict['fromStamp'] , self.tenantUsagesDict['toStamp'] , tenantInstance['download'] , tenantInstance['downloadPrice']))
            return insert_query
        except:
            print "Problem on query download res usage"

    def query_upload_to_res_usage(self,tenantInstance):
        try:
            insert_query = ("INSERT INTO `res_usage` (`tenant_id` , `instance_id`, `meter_name` ,\
            `from_stamp` , `to_stamp` , `meter_usage` , `bill`) VALUES (\"%s\" ,\"%s\" ,\"%s\" , \"%s\" , \"%s\" , %0.2f , %0.2f)"\
            %(self.tenantUsagesDict['tenantId'] , tenantInstance['instanceKvmName'] , "network.outgoing.bytes" ,\
            self.tenantUsagesDict['fromStamp'] , self.tenantUsagesDict['toStamp'] , tenantInstance['upload'] , tenantInstance['uploadPrice']))
            return insert_query
        except:
            print "Problem on query upload res usage"

    def query_ram_to_res_usage(self,tenantInstance):
        try:
            insert_query = ("INSERT INTO `res_usage` (`tenant_id` , `instance_id`, `meter_name` ,\
            `from_stamp` , `to_stamp` , `meter_usage` , `bill`) VALUES (\"%s\" ,\"%s\" ,\"%s\" , \"%s\" , \"%s\" , %0.2f , %0.2f)"\
            %(self.tenantUsagesDict['tenantId'] , tenantInstance['instanceKvmName'] , "memory.usage" ,\
            self.tenantUsagesDict['fromStamp'] , self.tenantUsagesDict['toStamp'] , tenantInstance['ram'] , tenantInstance['ramPrice']))
            return insert_query
        except:
            print "Problem on query ram res usage"

    def query_volume_to_res_usage(self):
        try:
            insert_query = ("INSERT INTO `res_usage` (`tenant_id` , `instance_id`, `meter_name` ,\
            `from_stamp` , `to_stamp` , `meter_usage` , `bill`) VALUES (\"%s\" ,\"%s\" ,\"%s\" , \"%s\" , \"%s\" , %0.2f , %0.2f)"\
            %(self.tenantUsagesDict['tenantId'] , "default" , "volume.size" ,\
            self.tenantUsagesDict['fromStamp'] , self.tenantUsagesDict['toStamp'] , self.tenantUsagesDict['volume'] , self.tenantUsagesDict['volumePrice']))
            return insert_query
        except:
            print "Problem on query volume res usage"

    def query_ip_to_res_usage(self):
        try:
            insert_query = ("INSERT INTO `res_usage` (`tenant_id` , `instance_id`, `meter_name` ,\
            `from_stamp` , `to_stamp` , `meter_usage` , `bill`) VALUES (\"%s\" ,\"%s\" ,\"%s\" , \"%s\" , \"%s\" , %0.2f , %0.2f)"\
            %(self.tenantUsagesDict['tenantId'] , "default" , "ip.floating" ,\
            self.tenantUsagesDict['fromStamp'] , self.tenantUsagesDict['toStamp'] , self.tenantUsagesDict['ip'] , self.tenantUsagesDict['ipPrice']))
            return insert_query
        except:
            print "Problem on query ip res usage"

    def query_subscribtion_to_res_usage(self):
        try:
	    print self.tenantUsagesDict['subscriptionPrice']
            insert_query = ("INSERT INTO `res_usage` (`tenant_id` , `instance_id`, `meter_name` ,\
            `from_stamp` , `to_stamp` , `meter_usage` , `bill`) VALUES (\"%s\" ,\"%s\" ,\"%s\" , \"%s\" , \"%s\" , %0.2f , %0.2f)"\
            %(self.tenantUsagesDict['tenantId'] , "default" , "instance" ,\
            self.tenantUsagesDict['fromStamp'] , self.tenantUsagesDict['toStamp'] , self.tenantUsagesDict['subscriptionPrice'] , self.tenantUsagesDict['subscriptionPrice']))
            return insert_query
        except Exception as e :
    	    print e
    	    print "\n"
            print "Problem on query subscription res usage"

    def execute_insert_query(self , query):
        try:
            self.cursor.execute(query)
            self.connectionObj.commit()
        except:
            print "Problem on execute insert query"

    def execute_select_query(self , query):
        try:
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except:
            print "Problem on excecute select query"

    def disconnect_from_database(self):
        try:
            self.cursor.close()
            self.connectionObj.close()
        except:
            print "Problem on Dissconnect database"

    def insert_to_res_usage_table(self , isPayg):
        try:
            if isPayg:
                self.execute_insert_query(self.query_volume_to_res_usage())
                self.execute_insert_query(self.query_ip_to_res_usage())
                self.execute_insert_query(self.query_subscribtion_to_res_usage())
                for tenantInstance in self.tenantUsagesDict['instances']:
                    self.execute_insert_query(self.query_upload_to_res_usage(tenantInstance))
                    self.execute_insert_query(self.query_download_to_res_usage(tenantInstance))
                    self.execute_insert_query(self.query_cpu_to_res_usage(tenantInstance))
                    self.execute_insert_query(self.query_ram_to_res_usage(tenantInstance))
            else:
                for tenantInstance in self.tenantUsagesDict['instances']:
                    self.execute_insert_query(self.query_upload_to_res_usage(tenantInstance))
                    self.execute_insert_query(self.query_download_to_res_usage(tenantInstance))

        except:
            print "Problem on insert to res usage table"

    def query_for_check_instance_existance_in_tenant_instance_table(self, instanceKvmName):
        try:
            search_query =("SELECT instance_id FROM tenant_instance WHERE instance_id = \"%s\"" % (instanceKvmName))
            return search_query
        except:
            print "Problem on query for check instance existance in tenant_instance table"

    def query_add_instance_to_tenant_instance_table(self , instance):
        try:
            nowTime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            insert_query = ("INSERT INTO `tenant_instance` (`tenant_id` , `instance_id`, `instance_name` ,\
            `creation_date` , `update_date`) VALUES (\"%s\" ,\"%s\" ,\"%s\" , \"%s\" , \"%s\")"\
            %(self.tenantUsagesDict['tenantId'] ,  instance['instanceKvmName'] , instance['instanceName'] ,\
            instance['creationDate'] ,  nowTime ))
            return insert_query
        except:
            print "Problem on query add instance to tenant instance table"

    def query_update_tenant_instance_table(self, instance):
        try:
            nowTime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            update_query = "UPDATE tenant_instance SET update_date=\"%s\" where instance_id =\"%s\"" % (nowTime,instance['instanceKvmName'])
            return update_query
        except:
            print "Problem on query update tenant_instance table"

    def insert_to_tenantinstance_table(self):
        # 1- check if instanse is on table or not
        # 2- if exists update the update_date to datetime.now else add a row
        try:
            for tenantInstance in self.tenantUsagesDict['instances']:
                if len(self.execute_select_query(self.query_for_check_instance_existance_in_tenant_instance_table(tenantInstance['instanceKvmName']))) == 0:
                    # create a row
                    self.execute_insert_query(self.query_add_instance_to_tenant_instance_table(tenantInstance))
                else:
                    #update row
                    self.execute_insert_query(self.query_update_tenant_instance_table(tenantInstance))
        except:
            print "Problem on insert to tenantinstance table"


    def query_for_check_tenant_existance_in_tenants_table(self):
        try:
            search_query ="SELECT id FROM tenants WHERE tenant_id = \"%s\"" % self.tenantUsagesDict['tenantId']
            return search_query
        except:
            print "Problem on query for check tenant existance in tenants table"

    def query_add_tenant_to_tenants_table(self):
        try:
            nowTime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            insert_query = ("INSERT INTO `tenants` (`tenant_id` , `tenant_name`, `user_id` ,\
            `creation_date` , `update_date`) VALUES (\"%s\" ,\"%s\" ,\"%s\" , \"%s\" , \"%s\")"\
            %(self.tenantUsagesDict['tenantId'] ,  self.tenantUsagesDict['tenantName'] , self.tenantUsagesDict['userId'] ,\
            nowTime , nowTime ))
            return insert_query
        except:
            print "Problem on query add tenant to tenants table"

############################### start policy queries ############################################
    def query_add_cpu_to_policy_table(self):
        try:
            insert_query = ("INSERT INTO `user_policy` (`user_id`, `type` ,\
            `policy_id` , `policy_order`) VALUES (\"%s\" ,\"%s\" ,\"%s\" , \"%s\")"\
            %(self.tenantUsagesDict['tenantId'] ,  "tenant" , "3" ,\
            "1" ))
            return insert_query
        except:
            print "Problem on query add cpu to policy table"

    def query_add_cpu_to_policy_table(self):
        try:
            insert_query = ("INSERT INTO `user_policy` (`user_id`, `type` ,\
            `policy_id` , `policy_order`) VALUES (\"%s\" ,\"%s\" ,\"%s\" , \"%s\")"\
            %(self.tenantUsagesDict['tenantId'] ,  "tenant" , "3" ,\
            "1" ))
            return insert_query
        except:
            print "Problem on query add cpu to policy table"

    def query_add_ram_to_policy_table(self):
        try:
            insert_query = ("INSERT INTO `user_policy` (`user_id`, `type` ,\
            `policy_id` , `policy_order`) VALUES (\"%s\" ,\"%s\" ,\"%s\" , \"%s\")"\
            %(self.tenantUsagesDict['tenantId'] ,  "tenant" , "5" ,\
            "1" ))
            return insert_query
        except:
            print "Problem on query add ram to policy table"

    def query_add_volume_to_policy_table(self):
        try:
            insert_query = ("INSERT INTO `user_policy` (`user_id`, `type` ,\
            `policy_id` , `policy_order`) VALUES (\"%s\" ,\"%s\" ,\"%s\" , \"%s\")"\
            %(self.tenantUsagesDict['tenantId'] ,  "tenant" , "7" ,\
            "1" ))
            return insert_query
        except:
            print "Problem on query add volume to policy table"

    def query_add_ip_to_policy_table(self):
        try:
            insert_query = ("INSERT INTO `user_policy` (`user_id`, `type` ,\
            `policy_id` , `policy_order`) VALUES (\"%s\" ,\"%s\" ,\"%s\" , \"%s\")"\
            %(self.tenantUsagesDict['tenantId'] ,  "tenant" , "9" ,\
            "1" ))
            return insert_query
        except:
            print "Problem on query add ip to policy table"

    def query_add_download_to_policy_table(self):
        try:
            insert_query = ("INSERT INTO `user_policy` (`user_id`, `type` ,\
            `policy_id` , `policy_order`) VALUES (\"%s\" ,\"%s\" ,\"%s\" , \"%s\")"\
            %(self.tenantUsagesDict['tenantId'] ,  "tenant" , "11" ,\
            "1" ))
            return insert_query
        except:
            print "Problem on query add download to policy table"

    def query_add_subscribtion_to_policy_table(self):
        try:
            insert_query = ("INSERT INTO `user_policy` (`user_id`, `type` ,\
            `policy_id` , `policy_order`) VALUES (\"%s\" ,\"%s\" ,\"%s\" , \"%s\")"\
            %(self.tenantUsagesDict['tenantId'] ,  "tenant" , "13" ,\
            "1" ))
            return insert_query
        except:
            print "Problem on query add subscription to policy table"

    def query_add_upload_to_policy_table(self):
        try:
            insert_query = ("INSERT INTO `user_policy` (`user_id`, `type` ,\
            `policy_id` , `policy_order`) VALUES (\"%s\" ,\"%s\" ,\"%s\" , \"%s\")"\
            %(self.tenantUsagesDict['tenantId'] ,  "tenant" , "15" ,\
            "1" ))
            return insert_query
        except:
            print "Problem on query add upload to policy table"
################################ end policy queries #############################################

    def query_update_tenants_table(self):
        try:
            nowTime = datetime.datetime.now()
            update_query = "UPDATE tenants SET update_date=\"%s\" where tenant_id =\"%s\"" % (str(nowTime),self.tenantUsagesDict['tenantId'])
            return update_query
        except:
            print "Problem on query update tenants table"

    def insert_to_tenants_table(self):
        # 1- check if instanse is on table or not
        # 2- if exists update the update_date to datetime.now else add a row
        try:
            if len(self.execute_select_query(self.query_for_check_tenant_existance_in_tenants_table())) == 0:
                # create a row
                self.execute_insert_query(self.query_add_tenant_to_tenants_table())
                self.insert_to_user_policy_table()
            else:
                #update row
                self.execute_insert_query(self.query_update_tenants_table())
        except:
            print "Problem on insert to tenants table"

    def insert_to_user_policy_table(self):
        try:
            self.execute_insert_query(self.query_add_cpu_to_policy_table())
            self.execute_insert_query(self.query_add_ram_to_policy_table())
            self.execute_insert_query(self.query_add_volume_to_policy_table())
            self.execute_insert_query(self.query_add_ip_to_policy_table())
            self.execute_insert_query(self.query_add_download_to_policy_table())
            self.execute_insert_query(self.query_add_subscribtion_to_policy_table())
            self.execute_insert_query(self.query_add_upload_to_policy_table())
        except:
            print "Problem on insert to user policy table"
