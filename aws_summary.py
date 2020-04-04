import boto3
import datetime
import time
import botocore
import ssl
import os
import json
import pandas as pd
import os.path
from os import path

from botocore.exceptions import ClientError
from boto3 import Session

if 'AWS_ACCESS_KEY_ID' in os.environ:
	AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
if 'AWS_SECRET_ACCESS_KEY' in os.environ:
	AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
if 'AWS_DEFAULT_REGION' in os.environ:
	AWS_DEFAULT_REGION = os.environ['AWS_DEFAULT_REGION']

def describeServiceItems( client , describe_function, key_items, filters="", next_step=""):
	try:
		if (next_step!=""):
			#print("Filters - " + filters)
			filters_to_add = ""
			if filters != "":
				filters_to_add = ", "+filters
			if describe_function=="list_resource_record_sets":
				strfunction = "client."+describe_function+"(StartRecordName='"+next_step+"'"+filters_to_add+")"
			else:
				strfunction = "client."+describe_function+"(NextToken='"+next_step+"'"+filters_to_add+")"
			#print("1 - " + strfunction)
			response = eval(strfunction)
		else:
			strfunction = "client."+describe_function+"("+filters+")"
			#print("2 - " + strfunction)
			response = eval(strfunction)
		listItems = []
		if not key_items in response or len(response[key_items])<=0:
			return False
		else:
			listItems = response[key_items]
		##print("");
		if 'NextToken' in response:
			#print("go 1")
			listItems += describeServiceItems(client, describe_function, key_items, filters, response['NextToken'])
		if 'NextRecordName' in response:
			#print("go 2")
			listItems += describeServiceItems(client, describe_function, key_items, filters, response['NextRecordName'])
		return listItems
	except botocore.exceptions.EndpointConnectionError as e:
		print(e)
		return False
	except ClientError as e:
		print(e)
		return False
		
def isTrueOrFalse( bool_vale ):
	if bool_vale:
		return "True"
	else:
		return "False"


def getExistsValueKey( item, keyname ):
	if keyname in item:
		return item[keyname]
	else:
		return ""


def existsKey( item, keyname ):
	if keyname in item:
		return True
	else:
		return False

def getValueTag( items, keyname ):
	for item in items:
		if item['Key'] == keyname:
			return item['Value']
	return ""
		
def getValueFromArray(items):
	strVO = ""
	for index, item in enumerate(items):
		if index < len(items) and index > 0:
			strVO += ", "
		strVO += item
	return strVO
	
def getRoleFromProfile (item):
	strRole = ""
	if item!="":
		values = item['Arn'].split(":")
		return values[5].split("/")[1]
	else:
		return strRole
		
session = Session(aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_DEFAULT_REGION)


path_folder = "./services"
if not path.exists(path_folder):
	os.mkdir(path_folder)

account_id = boto3.client('sts').get_caller_identity().get('Account')

######################################################################
###################################################################### AMAZON VPC
######################################################################

client = session.client('ec2')

responseVpcs = describeServiceItems(client, "describe_vpcs", "Vpcs")
if responseVpcs:
	dataVpcs = []
	for item in responseVpcs:
		item_service = {}
		item_service['Name'] = getValueTag( getExistsValueKey(item, 'Tags'), "Name")
		item_service['VpcId'] = item['VpcId']
		item_service['State'] = item['State']
		item_service['CidrBlock'] = item['CidrBlock']
		item_service['DhcpOptionsId'] = item['DhcpOptionsId']
		item_service['InstanceTenancy'] = item['InstanceTenancy']
		item_service['IsDefault'] = isTrueOrFalse(item['IsDefault'])
		dataVpcs.append(item_service)
	df = pd.DataFrame(dataVpcs)
	df.to_csv(path_folder+'/vpc_vpcs.csv', index=False)

responseSubnets = describeServiceItems(client, "describe_subnets", "Subnets")
if responseSubnets:
	dataSubnets = []
	for item in responseSubnets:
		item_service = {}
		item_service['Name'] = getValueTag( getExistsValueKey(item, 'Tags'), "Name")
		item_service['SubnetId'] = item['SubnetId']
		item_service['State'] = item['State']
		item_service['VpcId'] = item['VpcId']
		item_service['CidrBlock'] = item['CidrBlock']
		item_service['AvailableIpAddressCount'] = str(item['AvailableIpAddressCount'])
		item_service['AvailabilityZone'] = item['AvailabilityZone']
		item_service['DefaultForAz'] = isTrueOrFalse(item['DefaultForAz'])
		dataSubnets.append(item_service)
	df = pd.DataFrame(dataSubnets)
	df.to_csv(path_folder+'/vpc_subnets.csv', index=False)

######################################################################
###################################################################### AMAZON EC2
######################################################################

responseInstances = describeServiceItems(client, "describe_instances", "Reservations")
if responseInstances:
	dataInstances = []
	for reservation in responseInstances:
		for instance in reservation['Instances']:
			item_service = {}
			item_service['State'] = instance['State']['Name']
			item_service['InstanceId'] = instance['InstanceId']
			item_service['Name'] = getValueTag( getExistsValueKey(instance, 'Tags'), "Name")
			item_service['InstanceType'] = instance['InstanceType']
			item_service['IamInstanceProfile'] = getRoleFromProfile(getExistsValueKey(instance, 'IamInstanceProfile'))
			item_service['KeyName'] = getExistsValueKey(instance, 'KeyName')
			if getExistsValueKey(instance,'Platform').lower()=="windows":
				item_service['Platform'] = "Windows"
			else:
				item_service['DefaultForAz'] = "Linux"
			item_service['EbsOptimized'] = isTrueOrFalse(instance['EbsOptimized'])
			item_service['PrivateIpAddress'] = str(instance['PrivateIpAddress'])
			item_service['PublicIpAddress'] = getExistsValueKey(instance, 'PublicIpAddress')
			item_service['SubnetId'] = str(instance['SubnetId'])
			item_service['VpcId'] = str(instance['VpcId'])
			dataInstances.append(item_service)
	df = pd.DataFrame(dataInstances)
	df.to_csv(path_folder+'/ec2_instances.csv', index=False)

responseVolumes = describeServiceItems(client, "describe_volumes", "Volumes")
if responseVolumes:
	dataVolumes = []
	for item in responseVolumes:
		item_service = {}
		item_service['VolumeId'] = item['VolumeId']
		item_service['VolumeType'] = item['VolumeType']
		item_service['Size'] = str(item['Size'])
		item_service['Device'] = getExistsValueKey(item['Attachments'][0], 'Device')
		item_service['Encrypted'] = isTrueOrFalse(item['Encrypted'])
		item_service['DeleteOnTermination'] = isTrueOrFalse(getExistsValueKey(item['Attachments'][0], 'DeleteOnTermination'))
		item_service['State'] = isTrueOrFalse(getExistsValueKey(item['Attachments'][0], 'State'))
		responseVolumeSnapshots = describeServiceItems(client, "describe_snapshots", "Snapshots", " Filters = [{ 'Name' : 'volume-id', 'Values' : [ '"+item['VolumeId']+"' ] }]")
		if responseVolumeSnapshots:
			item_service['Snapshots'] = len(responseVolumeSnapshots)
			current_time = time.mktime(datetime.datetime.utcnow().timetuple())
			max_time_snapshot = 0
			max_date_string = ""
			difference_time = 0
			for itemS in responseVolumeSnapshots:
				started_time = time.mktime(itemS['StartTime'].timetuple())
				if started_time>max_time_snapshot:
					max_time_snapshot = started_time
					max_date_string = itemS['StartTime'].strftime("%Y-%m-%d %H:%m")
					difference_time = current_time - started_time
			item_service['LastSnapshot'] = max_date_string
		else:
			item_service['Snapshots'] = 0
			item_service['LastSnapshot'] = ""
		dataVolumes.append(item_service)
	df = pd.DataFrame(dataVolumes)
	df.to_csv(path_folder+'/ec2_volumes.csv', index=False)


responseSnapshots = describeServiceItems(client, "describe_snapshots", "Snapshots", " Filters = [{ 'Name' : 'owner-id', 'Values' : [ '"+account_id+"' ] }]")
if responseSnapshots:
	dataSnapshots = []
	for item in responseSnapshots:
		item_service = {}
		item_service['SnapshotId'] = item['SnapshotId']
		item_service['StartTime'] = item['StartTime'].strftime("%Y-%m-%d %H:%m")
		item_service['State'] = item['State']
		item_service['Progress'] = item['Progress']
		item_service['VolumeId'] = item['VolumeId']
		item_service['VolumeSize'] = item['VolumeSize']
		item_service['Description'] = item['Description']
		item_service['Encrypted'] = item['Encrypted']
		dataSnapshots.append(item_service)
	df = pd.DataFrame(dataSnapshots)
	df.to_csv(path_folder+'/ec2_snapshots.csv', index=False)

responseReservedInstances = describeServiceItems(client, "describe_reserved_instances", "ReservedInstances")
if responseReservedInstances:
	dataReservedInstances = []
	for item in responseReservedInstances:
		item_service = {}
		ri_scope = item['Scope']
		if existsKey(item, 'AvailabilityZone'):
			ri_scope = ri_scope + " - " + item['AvailabilityZone']
		item_service['ReservedInstancesId'] = str(item['ReservedInstancesId'])
		item_service['InstanceCount'] = str(item['InstanceCount'])
		item_service['InstanceType'] = item['InstanceType']
		item_service['Scope'] = ri_scope
		item_service['State'] = item['State']
		item_service['Duration'] = str(item['Duration']/60/60/24)
		item_service['OfferingClass'] = item['OfferingClass']
		item_service['OfferingType'] = item['OfferingType']
		item_service['Start'] = item['Start'].strftime("%Y-%m-%d %H:%m")
		item_service['End'] = item['End'].strftime("%Y-%m-%d %H:%m")
		item_service['ProductDescription'] = item['ProductDescription']
		item_service['UsagePrice'] = item['UsagePrice']
		item_service['CurrencyCode'] = str(item['CurrencyCode'])
		item_service['FixedPrice'] = item['FixedPrice']
		str_charge = ''
		c = 0
		for charge in item['RecurringCharges']:
			if c < len(item['RecurringCharges']) and c > 0:
				str_charge += " | "
			str_charge = str_charge + "Amount:" + str(charge['Amount']) + ' _ ' + "Frequency" + charge['Frequency']
			c = c +1
		item_service['RecurringCharges'] = str_charge
		dataReservedInstances.append(item_service)
	df = pd.DataFrame(dataReservedInstances)
	df.to_csv(path_folder+'/ec2_reserved_instances.csv', index=False)

######################################################################
###################################################################### AMAZON RDS
######################################################################

client = session.client('rds')

responseDBInstances = describeServiceItems(client, "describe_db_instances", "DBInstances")
if responseDBInstances:
	dataDBInstances = []
	for item in responseDBInstances:
		item_service = {}
		item_service['DBInstanceIdentifier'] = item["DBInstanceIdentifier"]
		item_service['DBName'] = getExistsValueKey(item, "DBName")
		item_service['MasterUsername'] = item["MasterUsername"]
		item_service['Engine'] = item["Engine"]
		item_service['EngineVersion'] = item["EngineVersion"]
		item_service['LicenseModel'] = item["LicenseModel"]
		item_service['MultiAZ'] = isTrueOrFalse(item["MultiAZ"])
		item_service['AvailabilityZone'] = item["AvailabilityZone"]
		item_service['PubliclyAccessible'] = isTrueOrFalse(item["PubliclyAccessible"])
		item_service['DBInstanceClass'] = item["DBInstanceClass"]
		item_service['StorageType'] = item["StorageType"]
		item_service['AllocatedStorage'] = str(item["AllocatedStorage"])
		item_service['StorageEncrypted'] = isTrueOrFalse(item["StorageEncrypted"])
		item_service['BackupRetentionPeriod'] = str(item["BackupRetentionPeriod"])
		item_service['InstanceCreateTime'] = str(item["InstanceCreateTime"])
		if "Endpoint" in item:
			item_service['Endpoint'] = item["Endpoint"]["Address"]
			item_service['Port'] = str(item["Endpoint"]["Port"])
		else:
			item_service['Endpoint'] = ''
			item_service['Port'] = ''
		dataDBInstances.append(item_service)
	df = pd.DataFrame(dataDBInstances)
	df.to_csv(path_folder+'/rds_instances.csv', index=False)


responseReservedDBInstances = describeServiceItems(client, "describe_reserved_db_instances", "ReservedDBInstances")
if responseReservedDBInstances:
	dataReservedDBInstances = []
	for item in responseReservedDBInstances:
		item_service = {}
		item_service['DBInstanceCount'] = item["DBInstanceCount"]
		item_service['DBInstanceClass'] = item["DBInstanceClass"]
		item_service['StartTime'] = item["StartTime"].strftime("%Y-%m-%d %H:%m")
		item_service['Duration'] = item["Duration"]
		item_service['FixedPrice'] = item["FixedPrice"]
		item_service['UsagePrice'] = item["UsagePrice"]
		item_service['CurrencyCode'] = item["CurrencyCode"]
		item_service['ProductDescription'] = item["ProductDescription"]
		item_service['OfferingType'] = item["OfferingType"]
		item_service['MultiAZ'] = isTrueOrFalse(item["MultiAZ"])
		item_service['State'] = item["State"]
		item_service['LeaseId'] = item["LeaseId"]
		str_charge = ''
		c = 0
		for charge in item['RecurringCharges']:
			if c < len(item['RecurringCharges']) and c > 0:
				str_charge += " | "
			str_charge = str_charge + "Amount:" + str(charge['RecurringChargeAmount']) + ' _ ' + "Frequency" + charge['RecurringChargeFrequency']
			c = c +1
		item_service['RecurringCharges'] = str_charge
		dataDBInstances.append(item_service)
	df = pd.DataFrame(dataReservedDBInstances)
	df.to_csv(path_folder+'/rds_reserved_instances.csv', index=False)