import copy
class PriceCalc():

    def __init__(self):
        self.cpuPrice = 0
        self.ramPrice = 0
        self.volumePrice = 0
        self.ipPrice = 0
        self.subscriptionPrice = 0
        self.unitPrice = None
        self.discount = None
        self.billingConfig = None
        self.uploadPrice = None
        self.downloadPrice = None
        self.sla = None

    def set_unit_price(self , unit):
        self.unitPrice = unit

    def set_billing_conf(self, billingConfig):
        self.billingConfig = billingConfig

    def set_discount(self , discount):
        self.discount = (100 - discount) / 100

    def set_sla(self,sla):
        if sla == 0 :
            self.sla = float(self.unitPrice.get('sla', 'economy'))
        elif sla == 1:
            self.sla = float(self.unitPrice.get('sla', 'business'))
        elif sla == 2:
            self.sla = float(self.unitPrice.get('sla', 'first_class'))

    def calc_cpu_price(self,cpuUsage):
    # this function gets a dictionary contains instances name and number of cpu
    # should calculate final price for that amount of cpu and retrun as a dict
    # contains of instances name and cpu prices
        try:
            tempCpuUsageDict = copy.deepcopy(cpuUsage)  # use temp because this is pass by refrence and we dont want to change the main dict
            cpuUnitPrice = float(self.unitPrice.get('price', 'CPU_uint_Price'))
            for instance in tempCpuUsageDict.keys():
                if tempCpuUsageDict[instance][0] < 1 :
                    usageMultiply = 16
                elif tempCpuUsageDict[instance][0] >= 1 and tempCpuUsageDict[instance][0] <= 10:
                    usageMultiply = 10
                else:
                    usageMultiply = 1
                tempCpuUsageDict[instance] = ((tempCpuUsageDict[instance][0] * tempCpuUsageDict[instance][1] * cpuUnitPrice)* float(self.unitPrice.get('price', 'payg_multiply')) * usageMultiply * self.discount) / ( 31 * 24 * float(self.billingConfig.get('default', 'unit_hour')) * 100 )
            self.cpuPrice = tempCpuUsageDict
        except Exception as e:
            print " Problem on calc cpu price : " + str(e)

    def calc_ram_price(self,ramUsage):
    # this function gets a dictionary contains instances name and number of ram
    # should calculate final price for that amount of ram and retrun as a dict
    # contains of instances name and ram prices
        try:
            ramUnitPrice = float(self.unitPrice.get('price', 'RAM_uint_Price'))
            tempRamUsageDict = copy.deepcopy(ramUsage) # use temp because this is pass by refrence and we dont want to change the main dict
            for instance in tempRamUsageDict.keys():
                tempRamUsageDict[instance] = ((tempRamUsageDict[instance] * ramUnitPrice) * self.discount * float(self.unitPrice.get('price', 'payg_multiply'))) / ( 31 * 24 * float(self.billingConfig.get('default', 'unit_hour')) )
            self.ramPrice = tempRamUsageDict
        except Exception as s:
            print " Problem on calc ram price : " + str(e)


    def calc_volume_price(self,volumeTotal):
        try:
            self.volumePrice = (float(self.unitPrice.get('price', 'VOLUME_uint_Price')) * volumeTotal * self.discount * float(self.unitPrice.get('price', 'payg_multiply'))) / ( 31 * 24 * float(self.billingConfig.get('default', 'unit_hour')))
        except Exception as e:
            print " Problem on calc volume price : " + str(e)

    def calc_ip_price(self,numberOfIp):
        try:
            self.ipPrice = (float(self.unitPrice.get('price', 'IP_uint_Price')) * numberOfIp * self.discount ) / ( 31 * 24 * float(self.billingConfig.get('default', 'unit_hour')))
        except Exception as e:
            print " Problem on calc ip price : " + str(e)

    def calc_subscription_price(self,quotaList,isAvgForSubscription):
        # this if and else is because of meter_usage and bill have the same values and we cant get specific
        # amount of volume,cpu,ram because we just save final price of subscription in database
        try:
            if isAvgForSubscription:
                self.subscriptionPrice = quotaList
            else:
                self.subscriptionPrice = ((( float(self.unitPrice.get('price', 'CPU_uint_Price')) * quotaList[0] )
                + ( float(self.unitPrice.get('price', 'RAM_uint_Price')) * quotaList[1]) +
                ( float(self.unitPrice.get('price', 'VOLUME_uint_Price')) * quotaList[2] ) * self.discount) / 31 / 24 / float(self.billingConfig.get('default', 'unit_hour'))) * 0.05
        except Exception as e:
            print " Problem on calc subscription price : " + str(e)

    def calc_upload_price(self,upload):
        try:
            tempUploadDict = copy.deepcopy(upload)  # use temp because this is pass by refrence and we dont want to change the main dict
            for instance in tempUploadDict.keys():
                tempUploadDict[instance] = 0
            self.uploadPrice = tempUploadDict
        except Exception as e:
            print " Problem on calc upload price : " + str(e)


    def calc_download_price(self,download):
        try:
            tempDownloadDict = copy.deepcopy(download)  # use temp because this is pass by refrence and we dont want to change the main dict
            for instance in tempDownloadDict.keys():
                tempDownloadDict[instance] = 0
            self.downloadPrice = tempDownloadDict
        except Exception as e:
            print " Problem on calc download price : " + str(e)

    def apply_sla_multiply(self,isPayg):
        for instance in self.uploadPrice.keys():
            if isPayg:
                self.cpuPrice[instance] = float(float(self.cpuPrice[instance]) * self.sla)
                self.ramPrice[instance] = float(self.ramPrice[instance]) * self.sla
            self.uploadPrice[instance] = float(self.uploadPrice[instance]) * self.sla
            self.downloadPrice[instance] = float(self.downloadPrice[instance]) * self.sla
        self.subscriptionPrice = float(self.subscriptionPrice) * self.sla
        self.ipPrice = float(self.ipPrice) * self.sla
        self.volumePrice = float(self.volumePrice) * self.sla

    def get_cpu_price(self):
        return self.cpuPrice

    def get_ram_price(self):
        return self.ramPrice

    def get_volume_price(self):
        return self.volumePrice

    def get_ip_price(self):
        return self.ipPrice

    def get_subscription_price(self):
        return self.subscriptionPrice

    def get_upload_price(self):
        return self.uploadPrice

    def get_download_price(self):
        return self.downloadPrice
