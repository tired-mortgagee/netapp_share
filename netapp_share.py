#! /usr/bin/python

#########################################################################################
#########################################################################################
##
## NetApp Share Provisioning Script - Similar to Share Provisioning in OpenStack Manila
##
## tired.mortgagee@gmail.com
## v0.3 2019.07.11
## change log at bottom of this file
##
## current limitations
## - only create, list, delete, access_allow, extend, shrink, quota_show, and show commands
## - selects the first suitable aggregate only
## - only nfs
##


###
### imports / includes
###

from NaServer import *
import argparse
import getpass
import uuid
import sys
import re

#####
##### procedure connect_svm
#####

def connect_svm(in_args):

   # type and syntax checking on command line args
   obj_regexp = re.compile(r'^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$|^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9](\.[a-zA-Z0-9\-]{2,}){0,6}$')
   if (not(obj_regexp.match(in_args.svm))):
      sys.exit("error: the svm parameter must be either an IP address or a hostname")

   # connect to svm
   obj_svm = NaServer(in_args.svm, 1, 3)
   obj_svm.set_transport_type('HTTPS')
   if(in_args.cert is None):
      obj_svm.set_style('LOGIN')
      string_username = raw_input("login as: ")
      string_password = getpass.getpass()  
      obj_svm.set_admin_user(string_username,string_password)
   else:
      result = obj_svm.set_style('CERTIFICATE')
      obj_svm.set_server_cert_verification(0)
      obj_svm.set_client_cert_and_key(in_args.cert[0],in_args.cert[1])

   # check that the api is reachable
   result = obj_svm.invoke("system-get-version")
   if(result.results_status() == "failed"):
      sys.exit("error: cannot connect to filer; " + result.results_reason())

   return obj_svm

#####
##### procedure list_share
#####

def list_share(in_args):

   obj_svm = connect_svm(in_args)

   # retrive details for all volumes
   obj_volume_get = NaElement("volume-get-iter")
   obj_volume_get.child_add_string("max-records","10000")
   result = obj_svm.invoke_elem(obj_volume_get)
   if(result.results_status() == "failed"):
      sys.exit("error: api request failed; " + result.results_reason())
   if(result.child_get_int("num-records")<2):
      sys.exit("no shares found")
   print "+----------------------------------------------+----------------+-----------+"
   print "| ID                                           | Name           | Size      |"
   print "+----------------------------------------------+----------------+-----------+"
   for volume in result.child_get("attributes-list").children_get():
      if(volume.child_get("volume-state-attributes").child_get_string("is-vserver-root") == "false"):
         string_output = "| "
         string_output += volume.child_get("volume-id-attributes").child_get_string("name") + (" " * (45-len(str(volume.child_get("volume-id-attributes").child_get_string("name"))))) + "| "
         string_output += volume.child_get("volume-id-attributes").child_get_string("comment") + (" " * (15-len(str(volume.child_get("volume-id-attributes").child_get_string("comment"))))) + "| "
         string_output += str(volume.child_get("volume-space-attributes").child_get_int("size")/1024/1024/1024) + (" " * (10-len(str(volume.child_get("volume-space-attributes").child_get_int("size")/1024/1024/1024)))) + "|"
         print string_output
   print "+----------------------------------------------+----------------+-----------+"

#####
##### procedure allow_access_share
#####

def access_allow_share(in_args):

   obj_svm = connect_svm(in_args)

   # type and syntax checking on command line args
   obj_regexp = re.compile(r'[ \*#"><\|\?\\]')
   if (obj_regexp.search(in_args.name)):
      sys.exit("error: the name parameter cannot contain the characters ' *#\"><|?\\'")
   if ((len(in_args.name)<1) or (len(in_args.name)>255)):
      sys.exit("error: the name parameter must contain between 1 and 255 characters")
   obj_regexp = re.compile(r'^ip$')
   if (not(obj_regexp.match(in_args.access_type))):
      sys.exit("error: the access_type parameter must be ip")
   obj_regexp = re.compile(r'^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}(/[0-9]{1,2})?$')
   if (not(obj_regexp.match(in_args.access_to))):
      sys.exit("error: the access_to parameter must be an IP address with an optional subnet mask bits suffix")

   obj_svm = connect_svm(in_args)

   # check that the volume with the correct share name exists
   obj_volume_get = NaElement("volume-get-iter")
   obj_desired_attributes = NaElement("query")
   obj_volume_attributes = NaElement("volume-attributes")
   obj_volume_id_attributes = NaElement("volume-id-attributes")
   obj_volume_id_attributes.child_add_string("comment",in_args.name)
   obj_volume_attributes.child_add(obj_volume_id_attributes)
   obj_desired_attributes.child_add(obj_volume_attributes)
   obj_volume_get.child_add(obj_desired_attributes)
   obj_volume_get.child_add_string("max-records","10000")
   result = obj_svm.invoke_elem(obj_volume_get)
   if(result.results_status() == "failed"):
      sys.exit("error: cannot execute api; " + result.results_reason())
   if(result.child_get_int("num-records")<1):
      sys.exit("error: share with name " + in_args.name + " is not found")
   if(result.child_get_int("num-records")>1):
      sys.exit("error: more than one share with name " + in_args.name + " is found")

   # create the export rule in the policy matching the volume name
   for volume in result.child_get("attributes-list").children_get():
      obj_export_rule_create = NaElement("export-rule-create")
      obj_export_rule_create.child_add_string("policy-name",volume.child_get("volume-id-attributes").child_get_string("name").replace("-","_").replace("share_",""))
      obj_export_rule_create.child_add_string("client-match",in_args.access_to)
      obj_rorule = NaElement("ro-rule")
      obj_rorule.child_add_string("security-flavor","sys")
      obj_rwrule = NaElement("rw-rule")
      obj_rwrule.child_add_string("security-flavor","sys")
      obj_secrule = NaElement("super-user-security")
      obj_secrule.child_add_string("security-flavor","sys")
      obj_export_rule_create.child_add(obj_rorule)
      obj_export_rule_create.child_add(obj_rwrule)
      obj_export_rule_create.child_add(obj_secrule)
      result = obj_svm.invoke_elem(obj_export_rule_create)
      if(result.results_status() == "failed"):
         sys.exit("error: cannot execute api; " + result.results_reason())

   # format and print the successful output
   print "+--------------+--------------------------------------+"
   print "| Property     | Value                                |"
   print "+--------------+--------------------------------------+"
   string_output = "| share_id     | " + str(volume.child_get("volume-id-attributes").child_get_string("name").replace("share_","")) + (" " * (37-len(str(volume.child_get("volume-id-attributes").child_get_string("name").replace("share_",""))))) + "|"
   print string_output
   print "| access_type  | ip                                   |"
   string_output = "| access_to    | " + str(in_args.access_to) + (" " * (37-len(str(in_args.access_to)))) + "|"
   print string_output
   print "| access_level | rw                                   |"
   print "| state        | new                                  |"
   print "+--------------+--------------------------------------+"

#####
##### procedure delete_share
#####

def delete_share(in_args):

   # type and syntax checking on command line args
   obj_regexp = re.compile(r'[ \*#"><\|\?\\]')
   if (obj_regexp.search(in_args.name)):
      sys.exit("error: the name parameter cannot contain the characters ' *#\"><|?\\'")
   if ((len(in_args.name)<1) or (len(in_args.name)>255)):
      sys.exit("error: the name parameter must contain between 1 and 255 characters")

   obj_svm = connect_svm(in_args)

   # check that the volume with the correct share name exists
   obj_volume_get = NaElement("volume-get-iter")
   obj_desired_attributes = NaElement("query")
   obj_volume_attributes = NaElement("volume-attributes")
   obj_volume_id_attributes = NaElement("volume-id-attributes")
   obj_volume_id_attributes.child_add_string("comment",in_args.name)
   obj_volume_attributes.child_add(obj_volume_id_attributes)
   obj_desired_attributes.child_add(obj_volume_attributes)
   obj_volume_get.child_add(obj_desired_attributes)
   obj_volume_get.child_add_string("max-records","10000")
   result = obj_svm.invoke_elem(obj_volume_get)
   if(result.results_status() == "failed"):
      sys.exit("error: cannot execute api; " + result.results_reason())
   if(result.child_get_int("num-records")<1):
      sys.exit("error: share with name " + in_args.name + " is not found")
   if(result.child_get_int("num-records")>1):
      sys.exit("error: more than one share with name " + in_args.name + " is found")
   string_export_policy = (result.child_get("attributes-list").children_get())[0].child_get("volume-export-attributes").child_get_string("policy")

   # unmount, offline, and delete the volume
   for volume in result.child_get("attributes-list").children_get():
      obj_volume_unmount = NaElement("volume-unmount")
      obj_volume_unmount.child_add_string("volume-name",volume.child_get("volume-id-attributes").child_get_string("name"))
      obj_volume_offline = NaElement("volume-offline")
      obj_volume_offline.child_add_string("name",volume.child_get("volume-id-attributes").child_get_string("name"))
      obj_volume_destroy = NaElement("volume-destroy")
      obj_volume_destroy.child_add_string("name",volume.child_get("volume-id-attributes").child_get_string("name"))
      result2 = obj_svm.invoke_elem(obj_volume_unmount)
      if (result2.results_status() == "failed"):
         sys.exit("error: cannot execute api; " + result2.results_reason())
      result2 = obj_svm.invoke_elem(obj_volume_offline)
      if (result2.results_status() == "failed"):
         sys.exit("error: cannot execute api; " + result2.results_reason())
      result2 = obj_svm.invoke_elem(obj_volume_destroy)
      if (result2.results_status() == "failed"):
         sys.exit("error: cannot execute api; " + result2.results_reason())

   # delete export-policy
   obj_export_policy_destroy = NaElement("export-policy-destroy")
   obj_export_policy_destroy.child_add_string("policy-name",string_export_policy)
   result = obj_svm.invoke_elem(obj_export_policy_destroy)
   if(result.results_status() == "failed"):
      sys.exit("error: cannot execute api; " + result.results_reason())

   print "share deleted successfully"
   
#####
##### procedure create_share
#####

def create_share(in_args):

   # type and syntax checking on command line args
   obj_regexp = re.compile(r'[ \*#"><\|\?\\]')
   if (obj_regexp.search(in_args.name)):
      sys.exit("error: the name parameter cannot contain the characters ' *#\"><|?\\'")
   if ((len(in_args.name)<1) or (len(in_args.name)>255)):
      sys.exit("error: the name parameter must contain between 1 and 255 characters")
   try:
      int(in_args.size)
   except:
      sys.exit("error: the size parameter must be an integer")
   if ((int(in_args.size)<1) or (int(in_args.size)>104857600)):
      sys.exit("error: the size paramater must be between 1 and 104857600")
   obj_regexp = re.compile(r'^capacity$|^value$')
   if (not(obj_regexp.match(in_args.type))):
      sys.exit("error: the type parameter must be either value | capacity")

   obj_svm = connect_svm(in_args)

   # retrive existing manila quota
   result = obj_svm.invoke("volume-get-root-name")
   if(result.results_status() == "failed"):
      sys.exit("error: api request failed; " + result.results_reason())
   obj_volume_get = NaElement("volume-get-iter")
   obj_desired_attributes = NaElement("query")
   obj_volume_attributes = NaElement("volume-attributes")
   obj_volume_id_attributes = NaElement("volume-id-attributes")
   obj_volume_id_attributes.child_add_string("name",result.child_get_string("volume"))
   obj_volume_attributes.child_add(obj_volume_id_attributes)
   obj_desired_attributes.child_add(obj_volume_attributes)
   obj_volume_get.child_add(obj_desired_attributes)
   result = obj_svm.invoke_elem(obj_volume_get)
   if(result.child_get_int("num-records") != 1):
      sys.exit("error: could not read tenant quota value")
   if(len((result.child_get("attributes-list").children_get())[0].child_get("volume-id-attributes").child_get_string("comment")) == 0):
      int_quota = 1000000000
   else:
      int_quota = (int)((result.child_get("attributes-list").children_get())[0].child_get("volume-id-attributes").child_get_string("comment"))

   # find the sum of the size of all non root volumes
   obj_volume_get = NaElement("volume-get-iter")
   obj_volume_get.child_add_string("max-records","10000")
   result = obj_svm.invoke_elem(obj_volume_get)
   int_provisioned_size = 0
   for volume in result.child_get("attributes-list").children_get():
      if(volume.child_get("volume-state-attributes").child_get_string("is-vserver-root") == "false"):
         int_provisioned_size = int_provisioned_size + volume.child_get("volume-space-attributes").child_get_int("size")

   # abort if quota will be exceeded
   if((int_provisioned_size / 1024 /1024 / 1024) + int(in_args.size) > int_quota):
      sys.exit("error: tenant quota of " + str(int_quota) + "GB will be exceeded")

   # check that the share, volume, or junction path does not already exist
   string_uuid = str(uuid.uuid1()).strip()
   obj_volume_get = NaElement("volume-get-iter")
   obj_volume_get.child_add_string("max-records","10000")
   result = obj_svm.invoke_elem(obj_volume_get)
   if(result.results_status() == "failed"):
      sys.exit("error: api request failed; " + result.results_reason())
   for volume in result.child_get("attributes-list").children_get():
      if (volume.child_get("volume-id-attributes").child_get_string("name").strip() == string_uuid):
         sys.exit("error: volume UUID clash; already exists")
      if (volume.child_get("volume-state-attributes").child_get_string("is-junction-active")):
         if (volume.child_get("volume-id-attributes").child_get_string("junction-path").strip().replace("/","") == in_args.name.strip()):
            sys.exit("error: share name already exists as junction path")
      if (volume.child_get("volume-id-attributes").child_get_string("comment") == in_args.name):
         sys.exit("error: share name already exists")


   # select the appropriate aggregate
   if (in_args.type == "value"):
      obj_regexp = re.compile(r'.*_val$')
   else:
      obj_regexp = re.compile(r'.*_cap$')
   array_candidates = []
   result = obj_svm.invoke("vserver-get-iter")
   if(result.results_status() == "failed"):
      sys.exit("error: api request failed; " + result.results_reason())
   for svm in result.child_get("attributes-list").children_get():
      if (svm.child_get("vserver-aggr-info-list")):
         for aggr in svm.child_get("vserver-aggr-info-list").children_get():
            if (obj_regexp.match(aggr.child_get_string("aggr-name"))):
               array_candidates.append(aggr.child_get_string("aggr-name"))
      else:
         sys.exit("error: no suitable data aggregates for share provisioning")
   if (len(array_candidates)<1):
      sys.exit("error: no aggregates matching the " + in_args.type + " tier")
   if(in_args.type == "value"):
      string_aggregate = "value tier"
   else:
      string_aggregate = "capacity tier"

   # create the export-policy
   obj_export_policy_create = NaElement("export-policy-create")
   obj_export_policy_create.child_add_string("policy-name",string_uuid.replace("-","_"))
   result = obj_svm.invoke_elem(obj_export_policy_create)
   if(result.results_status() == "failed"):
      sys.exit("error: api request failed; " + result.results_reason())

   # create the volume
   obj_volume_create = NaElement("volume-create")
   obj_volume_create.child_add_string("volume","share_"+string_uuid.replace("-","_"))
   obj_volume_create.child_add_string("containing-aggr-name",array_candidates[0])
   obj_volume_create.child_add_string("size",in_args.size+"g")
   obj_volume_create.child_add_string("junction-path","/"+string_uuid)
   obj_volume_create.child_add_string("snapshot-policy","none")
   obj_volume_create.child_add_string("space-reserve","none")
   obj_volume_create.child_add_string("unix-permissions","0777")
#   obj_volume_create.child_add_string("export-policy","open")
   obj_volume_create.child_add_string("export-policy",string_uuid.replace("-","_"))
   obj_volume_create.child_add_string("percentage-snapshot-reserve",0)
   obj_volume_create.child_add_string("volume-comment",in_args.name)
   result = obj_svm.invoke_elem(obj_volume_create)
   if(result.results_status() == "failed"):
      sys.exit("error: api request failed; " + result.results_reason())

   # retrieve all lifs capable of serving nfs for output
   obj_net_interface_get = NaElement("net-interface-get-iter")
   obj_desired_attributes = NaElement("query")
   obj_net_interface_info = NaElement("net-interface-info")
   obj_data_protocol = NaElement("data-protocols")
   obj_data_protocol.child_add_string("data-protocol","nfs")
   obj_net_interface_info.child_add(obj_data_protocol)
   obj_desired_attributes.child_add(obj_net_interface_info)
   obj_net_interface_get.child_add(obj_desired_attributes)
   result = obj_svm.invoke_elem(obj_net_interface_get)
   if(result.results_status() == "failed"):
      sys.exit("error: cannot execute api; " + result.results_reason())

   # format and print the successful output
   print "+------------------------------------+----------------------------------------------------------------------------------+"
   print "| Property                           | Value                                                                            |"
   print "+------------------------------------+----------------------------------------------------------------------------------+"
   print "| status                             | available                                                                        |"
   bool_first_time = True
   for interface in result.child_get("attributes-list").children_get():
      if (bool_first_time):
         string_padding = " " * (72-len(interface.child_get_string("address"))-len(string_uuid))
         print "| export_locations                   | path = " + interface.child_get_string("address") + ":/" + string_uuid + string_padding + "|"
         bool_first_time = False
      else:
         string_padding = " " * (72-len(interface.child_get_string("address"))-len(string_uuid))
         print "|                                    | path = " + interface.child_get_string("address") + ":/" + string_uuid + string_padding + "|"
   string_padding = " " * (61-len(str(string_uuid)))
   print "|                                    | share_instance_id = " + str(string_uuid) + string_padding + "|"
   string_padding = " " * (81-len(str(in_args.size)))
   print "| size                               | " + str(in_args.size) + string_padding + "|"
   string_padding = " " * (81-len(str(in_args.name)))
   print "| name                               | " + str(in_args.name) + string_padding + "|"
   string_padding = " " * (81-len(string_aggregate)-7)
   print "| extra-specs                        | tier = " + string_aggregate + string_padding + "|"
   print "+------------------------------------+----------------------------------------------------------------------------------+"

#####
##### procedure extend_share
#####

def extend_share(in_args):

   # type and syntax checking on command line args
   obj_regexp = re.compile(r'[ \*#"><\|\?\\]')
   if (obj_regexp.search(in_args.name)):
      sys.exit("error: the name parameter cannot contain the characters ' *#\"><|?\\'")
   if ((len(in_args.name)<1) or (len(in_args.name)>255)):
      sys.exit("error: the name parameter must contain between 1 and 255 characters")
   try:
      int(in_args.size)
   except:
      sys.exit("error: the size parameter must be an integer")
   if ((int(in_args.size)<1) or (int(in_args.size)>104857600)):
      sys.exit("error: the size paramater must be between 1 and 104857600")

   obj_svm = connect_svm(in_args)

   # find the current share and size
   obj_volume_get = NaElement("volume-get-iter")
   obj_desired_attributes = NaElement("query")
   obj_volume_attributes = NaElement("volume-attributes")
   obj_volume_id_attributes = NaElement("volume-id-attributes")
   obj_volume_id_attributes.child_add_string("comment",in_args.name)
   obj_volume_attributes.child_add(obj_volume_id_attributes)
   obj_desired_attributes.child_add(obj_volume_attributes)
   obj_volume_get.child_add(obj_desired_attributes)
   obj_volume_get.child_add_string("max-records","10000")
   result = obj_svm.invoke_elem(obj_volume_get)
   if(result.results_status() == "failed"):
      sys.exit("error: cannot execute api; " + result.results_reason())
   if(result.child_get_int("num-records")<1):
      sys.exit("error: share with name " + in_args.name + " is not found")
   if(result.child_get_int("num-records")>1):
      sys.exit("error: more than one share with name " + in_args.name + " is found")
   if((result.child_get("attributes-list").children_get())[0].child_get("volume-space-attributes").child_get_int("size")/1024/1024/1024 >= int(in_args.size)):
      sys.exit("error: existing size of share is already greater than or equal to requested new size")
   int_current_size = (result.child_get("attributes-list").children_get())[0].child_get("volume-space-attributes").child_get_int("size")/1024/1024/1024

   # retrive existing manila quota
   result = obj_svm.invoke("volume-get-root-name")
   if(result.results_status() == "failed"):
      sys.exit("error: api request failed; " + result.results_reason())
   obj_volume_get = NaElement("volume-get-iter")
   obj_desired_attributes = NaElement("query")
   obj_volume_attributes = NaElement("volume-attributes")
   obj_volume_id_attributes = NaElement("volume-id-attributes")
   obj_volume_id_attributes.child_add_string("name",result.child_get_string("volume"))
   obj_volume_attributes.child_add(obj_volume_id_attributes)
   obj_desired_attributes.child_add(obj_volume_attributes)
   obj_volume_get.child_add(obj_desired_attributes)
   result = obj_svm.invoke_elem(obj_volume_get)
   if(result.child_get_int("num-records") != 1):
      sys.exit("error: could not read tenant quota value")
   if(len((result.child_get("attributes-list").children_get())[0].child_get("volume-id-attributes").child_get_string("comment")) == 0):
      int_quota = 1000000000
   else:
      int_quota = (int)((result.child_get("attributes-list").children_get())[0].child_get("volume-id-attributes").child_get_string("comment"))

   # find the sum of the size of all non root volumes
   obj_volume_get = NaElement("volume-get-iter")
   obj_volume_get.child_add_string("max-records","10000")
   result = obj_svm.invoke_elem(obj_volume_get)
   int_provisioned_size = 0
   for volume in result.child_get("attributes-list").children_get():
      if(volume.child_get("volume-state-attributes").child_get_string("is-vserver-root") == "false"):
         int_provisioned_size = int_provisioned_size + volume.child_get("volume-space-attributes").child_get_int("size")

   # abort if quota will be exceeded
   if((int_provisioned_size / 1024 /1024 / 1024) + int(in_args.size) - int_current_size > int_quota):
      sys.exit("error: tenant quota of " + str(int_quota) + "GB will be exceeded")

   # resize the share
   obj_volume_get = NaElement("volume-get-iter")
   obj_desired_attributes = NaElement("query")
   obj_volume_attributes = NaElement("volume-attributes")
   obj_volume_id_attributes = NaElement("volume-id-attributes")
   obj_volume_id_attributes.child_add_string("comment",in_args.name)
   obj_volume_attributes.child_add(obj_volume_id_attributes)
   obj_desired_attributes.child_add(obj_volume_attributes)
   obj_volume_get.child_add(obj_desired_attributes)
   obj_volume_get.child_add_string("max-records","10000")
   result = obj_svm.invoke_elem(obj_volume_get)
   if(result.results_status() == "failed"):
      sys.exit("error: cannot execute api; " + result.results_reason())
   obj_volume_size = NaElement("volume-size")
   obj_volume_size.child_add_string("volume",(result.child_get("attributes-list").children_get())[0].child_get("volume-id-attributes").child_get_string("name"))
   obj_volume_size.child_add_string("new-size",in_args.size+"g")
   result = obj_svm.invoke_elem(obj_volume_size)
   if(result.results_status() == "failed"):
      sys.exit("error: cannot execute api; " + result.results_reason())
   
   print "share resized succesfully"

#####
##### procedure shrink_share
#####

def shrink_share(in_args):

   # type and syntax checking on command line args
   obj_regexp = re.compile(r'[ \*#"><\|\?\\]')
   if (obj_regexp.search(in_args.name)):
      sys.exit("error: the name parameter cannot contain the characters ' *#\"><|?\\'")
   if ((len(in_args.name)<1) or (len(in_args.name)>255)):
      sys.exit("error: the name parameter must contain between 1 and 255 characters")
   try:
      int(in_args.size)
   except:
      sys.exit("error: the size parameter must be an integer")
   if ((int(in_args.size)<1) or (int(in_args.size)>104857600)):
      sys.exit("error: the size paramater must be between 1 and 104857600")

   obj_svm = connect_svm(in_args)

   # find the current share and size
   obj_volume_get = NaElement("volume-get-iter")
   obj_desired_attributes = NaElement("query")
   obj_volume_attributes = NaElement("volume-attributes")
   obj_volume_id_attributes = NaElement("volume-id-attributes")
   obj_volume_id_attributes.child_add_string("comment",in_args.name)
   obj_volume_attributes.child_add(obj_volume_id_attributes)
   obj_desired_attributes.child_add(obj_volume_attributes)
   obj_volume_get.child_add(obj_desired_attributes)
   obj_volume_get.child_add_string("max-records","10000")
   result = obj_svm.invoke_elem(obj_volume_get)
   if(result.results_status() == "failed"):
      sys.exit("error: cannot execute api; " + result.results_reason())
   if(result.child_get_int("num-records")<1):
      sys.exit("error: share with name " + in_args.name + " is not found")
   if(result.child_get_int("num-records")>1):
      sys.exit("error: more than one share with name " + in_args.name + " is found")
   if((result.child_get("attributes-list").children_get())[0].child_get("volume-space-attributes").child_get_int("size")/1024/1024/1024 <= int(in_args.size)):
      sys.exit("error: existing size of share is already smaller or equal to the requested new size")
   if((result.child_get("attributes-list").children_get())[0].child_get("volume-space-attributes").child_get_int("size-used")/1024/1024/1024 > int(in_args.size)):
      sys.exit("error: existing used capacity in the share is greater than the requested new size")

   # resize the share
   obj_volume_get = NaElement("volume-get-iter")
   obj_desired_attributes = NaElement("query")
   obj_volume_attributes = NaElement("volume-attributes")
   obj_volume_id_attributes = NaElement("volume-id-attributes")
   obj_volume_id_attributes.child_add_string("comment",in_args.name)
   obj_volume_attributes.child_add(obj_volume_id_attributes)
   obj_desired_attributes.child_add(obj_volume_attributes)
   obj_volume_get.child_add(obj_desired_attributes)
   obj_volume_get.child_add_string("max-records","10000")
   result = obj_svm.invoke_elem(obj_volume_get)
   if(result.results_status() == "failed"):
      sys.exit("error: cannot execute api; " + result.results_reason())
   obj_volume_size = NaElement("volume-size")
   obj_volume_size.child_add_string("volume",(result.child_get("attributes-list").children_get())[0].child_get("volume-id-attributes").child_get_string("name"))
   obj_volume_size.child_add_string("new-size",in_args.size+"g")
   result = obj_svm.invoke_elem(obj_volume_size)
   if(result.results_status() == "failed"):
      sys.exit("error: cannot execute api; " + result.results_reason())
   
   print "share resized succesfully"
  
#####
##### procedure quota_show
#####

def quota_show(in_args):

   obj_svm = connect_svm(in_args)

   # retrive existing manila quota
   result = obj_svm.invoke("volume-get-root-name")
   if(result.results_status() == "failed"):
      sys.exit("error: api request failed; " + result.results_reason())
   obj_volume_get = NaElement("volume-get-iter")
   obj_desired_attributes = NaElement("query")
   obj_volume_attributes = NaElement("volume-attributes")
   obj_volume_id_attributes = NaElement("volume-id-attributes")
   obj_volume_id_attributes.child_add_string("name",result.child_get_string("volume"))
   obj_volume_attributes.child_add(obj_volume_id_attributes)
   obj_desired_attributes.child_add(obj_volume_attributes)
   obj_volume_get.child_add(obj_desired_attributes)
   result = obj_svm.invoke_elem(obj_volume_get)
   if(result.child_get_int("num-records") != 1):
      sys.exit("error: could not read tenant quota value")
   
   print "current tenant quota is " + (result.child_get("attributes-list").children_get())[0].child_get("volume-id-attributes").child_get_string("comment") + "GB"   

#####
##### procedure show_share
#####

def show_share(in_args):

   # type and syntax checking on command line args
   obj_regexp = re.compile(r'[ \*#"><\|\?\\]')
   if (obj_regexp.search(in_args.name)):
      sys.exit("error: the name parameter cannot contain the characters ' *#\"><|?\\'")
   if ((len(in_args.name)<1) or (len(in_args.name)>255)):
      sys.exit("error: the name parameter must contain between 1 and 255 characters")

   obj_svm = connect_svm(in_args)

   # find the share
   obj_volume_get = NaElement("volume-get-iter")
   obj_desired_attributes = NaElement("query")
   obj_volume_attributes = NaElement("volume-attributes")
   obj_volume_id_attributes = NaElement("volume-id-attributes")
   obj_volume_id_attributes.child_add_string("comment",in_args.name)
   obj_volume_attributes.child_add(obj_volume_id_attributes)
   obj_desired_attributes.child_add(obj_volume_attributes)
   obj_volume_get.child_add(obj_desired_attributes)
   obj_volume_get.child_add_string("max-records","10000")
   result = obj_svm.invoke_elem(obj_volume_get)
   if(result.results_status() == "failed"):
      sys.exit("error: cannot execute api; " + result.results_reason())
   if(result.child_get_int("num-records")<1):
      sys.exit("error: share with name " + in_args.name + " is not found")
   if(result.child_get_int("num-records")>1):
      sys.exit("error: more than one share with name " + in_args.name + " is found")
   volume = (result.child_get("attributes-list").children_get())[0]
   string_aggregate = "unknown"
   obj_regexp = re.compile(r'.*_val$')
   if(obj_regexp.match(volume.child_get("volume-id-attributes").child_get_string("containing-aggregate-name"))):
      string_aggregate = "value tier"   
   obj_regexp = re.compile(r'.*_cap$')
   if(obj_regexp.match(volume.child_get("volume-id-attributes").child_get_string("containing-aggregate-name"))):
      string_aggregate = "capacity tier"
   string_size = str(volume.child_get("volume-space-attributes").child_get_int("size")/1024/1024/1024)
   string_junction_path = volume.child_get("volume-id-attributes").child_get_string("junction-path")
	  
   # retrieve all lifs capable of serving nfs for output
   obj_net_interface_get = NaElement("net-interface-get-iter")
   obj_desired_attributes = NaElement("query")
   obj_net_interface_info = NaElement("net-interface-info")
   obj_data_protocol = NaElement("data-protocols")
   obj_data_protocol.child_add_string("data-protocol","nfs")
   obj_net_interface_info.child_add(obj_data_protocol)
   obj_desired_attributes.child_add(obj_net_interface_info)
   obj_net_interface_get.child_add(obj_desired_attributes)
   result = obj_svm.invoke_elem(obj_net_interface_get)
   if(result.results_status() == "failed"):
      sys.exit("error: cannot execute api; " + result.results_reason())

   # format and print the successful output
   print "+------------------------------------+----------------------------------------------------------------------------------+"
   print "| Property                           | Value                                                                            |"
   print "+------------------------------------+----------------------------------------------------------------------------------+"
   print "| status                             | available                                                                        |"
   bool_first_time = True
   for interface in result.child_get("attributes-list").children_get():
      if (bool_first_time):
         string_padding = " " * (72-len(interface.child_get_string("address"))-len(string_junction_path)+1)
         print "| export_locations                   | path = " + interface.child_get_string("address") + ":" + string_junction_path + string_padding + "|"
         bool_first_time = False
      else:
         string_padding = " " * (72-len(interface.child_get_string("address"))-len(string_junction_path)+1)
         print "|                                    | path = " + interface.child_get_string("address") + ":" + string_junction_path + string_padding + "|"
   #string_padding = " " * (61-len(str(string_junction_path)))
   #print "|                                    | share_instance_id = " + string_junction_path + string_padding + "|"
   string_padding = " " * (81-len(string_size))
   print "| size                               | " + string_size + string_padding + "|"
   string_padding = " " * (81-len(str(in_args.name)))
   print "| name                               | " + str(in_args.name) + string_padding + "|"
   string_padding = " " * (81-len(str(string_aggregate))-7)
   print "| extra-specs                        | tier = " + string_aggregate + string_padding + "|"
   print "+------------------------------------+----------------------------------------------------------------------------------+"

#####
##### procedure access_list
#####

def access_list_share(in_args):

   # type and syntax checking on command line args
   obj_regexp = re.compile(r'[ \*#"><\|\?\\]')
   if (obj_regexp.search(in_args.name)):
      sys.exit("error 0x901: the name parameter cannot contain the characters ' *#\"><|?\\'")
   if ((len(in_args.name)<1) or (len(in_args.name)>255)):
      sys.exit("error 0x902: the name parameter must contain between 1 and 255 characters")

   obj_svm = connect_svm(in_args)

   # find the share
   obj_volume_get = NaElement("volume-get-iter")
   obj_desired_attributes = NaElement("query")
   obj_volume_attributes = NaElement("volume-attributes")
   obj_volume_id_attributes = NaElement("volume-id-attributes")
   obj_volume_id_attributes.child_add_string("comment",in_args.name)
   obj_volume_attributes.child_add(obj_volume_id_attributes)
   obj_desired_attributes.child_add(obj_volume_attributes)
   obj_volume_get.child_add(obj_desired_attributes)
   obj_volume_get.child_add_string("max-records","10000")
   result = obj_svm.invoke_elem(obj_volume_get)
   if(result.results_status() == "failed"):
      sys.exit("error 0x903: cannot execute api; " + result.results_reason())
   if(result.child_get_int("num-records")<1):
       sys.exit("error 0x904: share with name " + in_args.name + " is not found")
   if(result.child_get_int("num-records")>1):
      sys.exit("error 0x905: more than one share with name " + in_args.name + " is found")
   volume = (result.child_get("attributes-list").children_get())[0]
   if(volume.child_get("volume-export-attributes").child_get_string("policy") is None):
      sys.exit("error 0x906: export-policy object could not be found")

   #print "DEBUG policy name: " + volume.child_get("volume-export-attributes").child_get_string("policy")
   
   obj_rule_get = NaElement("export-rule-get-iter")
   obj_desired_attributes = NaElement("query")
   obj_policy_attributes = NaElement("export-rule-info")
   obj_policy_attributes.child_add_string("policy-name",volume.child_get("volume-export-attributes").child_get_string("policy"))
   obj_desired_attributes.child_add(obj_policy_attributes)
   obj_rule_get.child_add(obj_desired_attributes)
   obj_rule_get.child_add_string("max-records","10000")
   result = obj_svm.invoke_elem(obj_rule_get)
   if(result.results_status() == "failed"):
      sys.exit("error 0x907: cannot execute api; " + result.results_reason())
   if(result.child_get_int("num-records")<1):
      sys.exit("error 0x908: export-policy with name " + volume.child_get("volume-id-attributes").child_get_string("name") + " is not found")

   #print "DEBUG number of rules: " + str(result.child_get_int("num-records"))

   print "+----------+-------------+--------------------+--------------+--------+"
   print "| id       | access_type | access_to          | access_level | state  |"
   print "+----------+-------------+--------------------+--------------+--------+"
   for rule in result.child_get("attributes-list").children_get():
      sys.stdout.write("| " + str(rule.child_get_int("rule-index")) + (9-len(str(rule.child_get_int("rule-index"))))*" ")
      sys.stdout.flush()
      sys.stdout.write("| ip          | " + rule.child_get_string("client-match") + (19-len(rule.child_get_string("client-match")))*" ")
      sys.stdout.flush()
      sys.stdout.write("| rw           | active |")
      print ""
   print "+----------+-------------+--------------------+--------------+--------+"
  
#####
##### procedure access_deny
#####

def access_deny_share(in_args):

   # type and syntax checking on command line args
   obj_regexp = re.compile(r'[ \*#"><\|\?\\]')
   if (obj_regexp.search(in_args.name)):
      sys.exit("error 0xA01: the name parameter cannot contain the characters ' *#\"><|?\\'")
   if ((len(in_args.name)<1) or (len(in_args.name)>255)):
      sys.exit("error 0xA02: the name parameter must contain between 1 and 255 characters")
   try:
      int(in_args.id)
   except:
      sys.exit("error 0xA03: the id parameter must be an integer")

   obj_svm = connect_svm(in_args)

   # find the share 
   obj_volume_get = NaElement("volume-get-iter")
   obj_desired_attributes = NaElement("query")
   obj_volume_attributes = NaElement("volume-attributes")
   obj_volume_id_attributes = NaElement("volume-id-attributes")
   obj_volume_id_attributes.child_add_string("comment",in_args.name)
   obj_volume_attributes.child_add(obj_volume_id_attributes)
   obj_desired_attributes.child_add(obj_volume_attributes)
   obj_volume_get.child_add(obj_desired_attributes)
   obj_volume_get.child_add_string("max-records","10000")
   result = obj_svm.invoke_elem(obj_volume_get)
   if(result.results_status() == "failed"):
      sys.exit("error 0xA04: cannot execute api; " + result.results_reason())
   if(result.child_get_int("num-records")<1):
      sys.exit("error 0xA05: share with name " + in_args.name + " is not found")
   if(result.child_get_int("num-records")>1):
      sys.exit("error 0xA06: more than one share with name " + in_args.name + " is found")
   volume = (result.child_get("attributes-list").children_get())[0]
   if(volume.child_get("volume-export-attributes").child_get_string("policy") is None):
      sys.exit("error 0xA07: export-policy object could not be found")

   # find the export-policy and rule
   obj_rule_get = NaElement("export-rule-destroy")
   #obj_desired_attributes = NaElement("query")
   #obj_policy_attributes = NaElement("export-rule-info")
   #obj_policy_attributes.child_add_string("policy-name",volume.child_get("volume-export-attributes").child_get_string("policy"))
   #obj_policy_attributes.child_add_string("rule-index",str(in_args.id))
   #obj_desired_attributes.child_add(obj_policy_attributes)
   #obj_rule_get.child_add(obj_desired_attributes)
   obj_rule_get.child_add_string("policy-name",volume.child_get("volume-export-attributes").child_get_string("policy"))
   obj_rule_get.child_add_string("rule-index",str(in_args.id))

   result = obj_svm.invoke_elem(obj_rule_get)
   if(result.results_status() == "failed"):
      sys.exit("error 0xA08: cannot execute api; " + result.results_reason())
   

#####
##### main
#####

def pair(value):
    rv = value.split(',')
    if len(rv) != 2:
        raise argparse.ArgumentParser()
    return rv
parser = argparse.ArgumentParser()
def pair(value):
   rv = value.split(',')
   if len(rv) != 2:
      raise parse.ArgumentParser()
   return rv
subparsers = parser.add_subparsers()
create_parser = subparsers.add_parser("create")
create_parser.add_argument("name", help="the name of the new share")
create_parser.add_argument("size", help="the size of the share in GB")
create_parser.add_argument("type", help="the service level; value | capacity")
create_parser.add_argument("svm", help="the hostname or IP address of the NetApp SVM")
create_parser.add_argument("-cert","--cert",nargs='?',type=pair,metavar='cert_file,key_file',help="(optional) pem and key file for cert-based auth")
create_parser.set_defaults(func=create_share)
delete_parser = subparsers.add_parser("delete")
delete_parser.add_argument("name", help="the name of the share to delete")
delete_parser.add_argument("svm", help="the hostname or the IP address of the NetApp SVM")
delete_parser.add_argument("-cert","--cert",nargs='?',type=pair,metavar='cert_file,key_file',help="(optional) pem and key file for cert-based auth")
delete_parser.set_defaults(func=delete_share)
list_parser = subparsers.add_parser("list")
list_parser.add_argument("svm", help="the hostname or the IP address of the NetApp SVM")
list_parser.add_argument("-cert","--cert",nargs='?',type=pair,metavar='cert_file,key_file',help="(optional) pem and key file for cert-based auth")
list_parser.set_defaults(func=list_share)
access_allow_parser = subparsers.add_parser("access_allow")
access_allow_parser.add_argument("name", help="the name of the share to modify access on")
access_allow_parser.add_argument("access_type", help="the protocol type for this access list entry; ip")
access_allow_parser.add_argument("access_to", help="the address range for this access list entry; <address>[/suffix]")
access_allow_parser.add_argument("svm", help="the hostname or the IP address of the NetApp SVM")
access_allow_parser.add_argument("-cert","--cert",nargs='?',type=pair,metavar='cert_file,key_file',help="(optional) pem and key file for cert-based auth")
access_allow_parser.set_defaults(func=access_allow_share)
extend_parser = subparsers.add_parser("extend")
extend_parser.add_argument("name", help="the name of the existing share")
extend_parser.add_argument("size", help="the new size of the share in GB")
extend_parser.add_argument("svm", help="the hostname or IP address of the NetApp SVM")
extend_parser.add_argument("-cert","--cert",nargs='?',type=pair,metavar='cert_file,key_file',help="(optional) pem and key file for cert-based auth")
extend_parser.set_defaults(func=extend_share)
shrink_parser = subparsers.add_parser("shrink")
shrink_parser.add_argument("name", help="the name of the existing share")
shrink_parser.add_argument("size", help="the new size of the share in GB")
shrink_parser.add_argument("svm", help="the hostname or IP address of the NetApp SVM")
shrink_parser.add_argument("-cert","--cert",nargs='?',type=pair,metavar='cert_file,key_file',help="(optional) pem and key file for cert-based auth")
shrink_parser.set_defaults(func=shrink_share)
quota_show_parser = subparsers.add_parser("quota_show")
quota_show_parser.add_argument("svm", help="the hostname or the IP address of the NetApp SVM")
quota_show_parser.add_argument("-cert","--cert",nargs='?',type=pair,metavar='cert_file,key_file',help="(optional) pem and key file for cert-based auth")
quota_show_parser.set_defaults(func=quota_show)
show_share_parser = subparsers.add_parser("show")
show_share_parser.add_argument("name", help="the name of the existing share")
show_share_parser.add_argument("svm", help="the hostname or the IP address of the NetApp SVM")
show_share_parser.add_argument("-cert","--cert",nargs='?',type=pair,metavar='cert_file,key_file',help="(optional) pem and key file for cert-based auth")
show_share_parser.set_defaults(func=show_share)
access_list_parser = subparsers.add_parser("access_list")
access_list_parser.add_argument("name", help="the name of the existing share")
access_list_parser.add_argument("svm", help="the hostname or the IP address of the NetApp SVM")
access_list_parser.add_argument("-cert","--cert",nargs='?',type=pair,metavar='cert_file,key_file',help="(optional) pem and key file for cert-based auth")
access_list_parser.set_defaults(func=access_list_share)
access_deny_parser = subparsers.add_parser("access_deny")
access_deny_parser.add_argument("name", help="the name of the existing share")
access_deny_parser.add_argument("id", help="the access rule to be deleted")
access_deny_parser.add_argument("svm", help="the hostname or the IP address of the NetApp SVM")
access_deny_parser.add_argument("-cert","--cert",nargs='?',type=pair,metavar='cert_file,key_file',help="(optional) pem and key file for cert-based auth")
access_deny_parser.set_defaults(func=access_deny_share)

ns_args = parser.parse_args()
ns_args.func(ns_args)

#########################################################################################
#########################################################################################
##
## Change Log
##
## 2019.04.10   Initial release
## 2019.04.15   Added list, delete, and allow_access commands
##              Changed create command to begin with no access
## 2019.07.11   Added cert-based auth option on all commands
##              Changed syntax for interactive auth
##              Added extend, shrink, quota_show, and show commands
##              Added tenant quota function
##              Updated delete command to remove export-policies
##
