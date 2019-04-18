#! /usr/bin/python

#########################################################################################
#########################################################################################
##
## NetApp Share Provisioning Script - Similar to Share Provisioning in OpenStack Manila
##
## tired.mortgagee@gmail.com
## v0.2 15.04.2019
## change log at bottom of this file
##
## current limitations
## - only create, list, delete, and access_allow commands
## - selects the first suitable aggregate only
## - only nfs
## - password can only be entered interactively
##


###
### imports / includes
###

import argparse
import re
import sys
from NaServer import *
import uuid
import getpass

#####
##### procedure list_share
#####

def list_share(in_args):

   # type and syntax checking on command line args
   obj_regexp = re.compile(r'[a-z_][a-zA-Z0-9_-]*')
   if (not(obj_regexp.match(in_args.username))):
      sys.exit("error: the username must only contain alphanumeric characters or an underscore, and must not start with a number ")
   obj_regexp = re.compile(r'^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$|^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$')
   if (not(obj_regexp.match(in_args.svm))):
      sys.exit("error: the svm parameter must be either an IP address or a hostname")

   # connect to filer
   obj_svm = NaServer(in_args.svm, 1, 3)
   result = obj_svm.set_transport_type('HTTPS')
   if(result and (result.results_errno() != 0)) :
      sys.exit("error: connection to filer failed; " + result.results_reason())
   result = obj_svm.set_style('LOGIN')
   if(result and (result.results_errno() != 0)):
      sys.exit("error: connection to filer failed; " + result.results_reason())
   result = obj_svm.set_admin_user(in_args.username,getpass.getpass())

   # check that the api is reachable
   result = obj_svm.invoke("system-get-version")
   if(result.results_status() == "failed"):
      sys.exit("error: cannot connect to filer; " + result.results_reason())

   # retrive details for all volumes
   result = obj_svm.invoke("volume-get-iter")
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

   # type and syntax checking on command line args
   obj_regexp = re.compile(r'[a-z_][a-zA-Z0-9_-]*')
   if (not(obj_regexp.match(in_args.username))):
      sys.exit("error: the username must only contain alphanumeric characters or an underscore, and must not start with a number ")
   obj_regexp = re.compile(r'[ \*#"><\|\?\\]')
   if (obj_regexp.search(in_args.name)):
      sys.exit("error: the name parameter cannot contain the characters ' *#\"><|?\\'")
   if ((len(in_args.name)<1) or (len(in_args.name)>255)):
      sys.exit("error: the name parameter must contain between 1 and 255 characters")
   obj_regexp = re.compile(r'^ip$')
   if (not(obj_regexp.match(in_args.access_type))):
      sys.exit("error: the access_type parameter must be ip")
   obj_regexp = re.compile(r'^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$|^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$')
   if (not(obj_regexp.match(in_args.svm))):
      sys.exit("error: the svm parameter must be either an IP address or a hostname")
   obj_regexp = re.compile(r'^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}(/[0-9]{1,2})?$')
   if (not(obj_regexp.match(in_args.access_to))):
      sys.exit("error: the access_to parameter must be an IP address with an optional subnet mask bits suffix")

   # connect to filer
   obj_svm = NaServer(in_args.svm, 1, 3)
   result = obj_svm.set_transport_type('HTTPS')
   if(result and (result.results_errno() != 0)) :
      sys.exit("error: connection to filer failed; " + result.results_reason())
   result = obj_svm.set_style('LOGIN')
   if(result and (result.results_errno() != 0)):
      sys.exit("error: connection to filer failed; " + result.results_reason())
   result = obj_svm.set_admin_user(in_args.username,getpass.getpass())

   # check that the api is reachable
   result = obj_svm.invoke("system-get-version")
   if(result.results_status() == "failed"):
      sys.exit("error: cannot connect to filer; " + result.results_reason())

   # check that the volume with the correct share name exists
   obj_volume_get = NaElement("volume-get-iter")
   obj_desired_attributes = NaElement("query")
   obj_volume_attributes = NaElement("volume-attributes")
   obj_volume_id_attributes = NaElement("volume-id-attributes")
   obj_volume_id_attributes.child_add_string("comment",in_args.name)
   obj_volume_attributes.child_add(obj_volume_id_attributes)
   obj_desired_attributes.child_add(obj_volume_attributes)
   obj_volume_get.child_add(obj_desired_attributes)
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
   obj_regexp = re.compile(r'[a-z_][a-zA-Z0-9_-]*')
   if (not(obj_regexp.match(in_args.username))):
      sys.exit("error: the username must only contain alphanumeric characters or an underscore, and must not start with a number ")
   obj_regexp = re.compile(r'[ \*#"><\|\?\\]')
   if (obj_regexp.search(in_args.name)):
      sys.exit("error: the name parameter cannot contain the characters ' *#\"><|?\\'")
   if ((len(in_args.name)<1) or (len(in_args.name)>255)):
      sys.exit("error: the name parameter must contain between 1 and 255 characters")
   obj_regexp = re.compile(r'^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$|^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$')
   if (not(obj_regexp.match(in_args.svm))):
      sys.exit("error: the svm parameter must be either an IP address or a hostname")

   # connect to filer
   obj_svm = NaServer(in_args.svm, 1, 3)
   result = obj_svm.set_transport_type('HTTPS')
   if(result and (result.results_errno() != 0)) :
      sys.exit("error: connection to filer failed; " + result.results_reason())
   result = obj_svm.set_style('LOGIN')
   if(result and (result.results_errno() != 0)):
      sys.exit("error: connection to filer failed; " + result.results_reason())
   result = obj_svm.set_admin_user(in_args.username,getpass.getpass())

   # check that the api is reachable
   result = obj_svm.invoke("system-get-version")
   if(result.results_status() == "failed"):
      sys.exit("error: cannot connect to filer; " + result.results_reason())

   # check that the volume with the correct share name exists
   obj_volume_get = NaElement("volume-get-iter")
   obj_desired_attributes = NaElement("query")
   obj_volume_attributes = NaElement("volume-attributes")
   obj_volume_id_attributes = NaElement("volume-id-attributes")
   obj_volume_id_attributes.child_add_string("comment",in_args.name)
   obj_volume_attributes.child_add(obj_volume_id_attributes)
   obj_desired_attributes.child_add(obj_volume_attributes)
   obj_volume_get.child_add(obj_desired_attributes)
   result = obj_svm.invoke_elem(obj_volume_get)
   if(result.results_status() == "failed"):
      sys.exit("error: cannot execute api; " + result.results_reason())
   if(result.child_get_int("num-records")<1):
      sys.exit("error: share with name " + in_args.name + " is not found")
   if(result.child_get_int("num-records")>1):
      sys.exit("error: more than one share with name " + in_args.name + " is found")

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

   ### TODO: add successful stdout output

#####
##### procedure create_share
#####

def create_share(in_args):

   # type and syntax checking on command line args
   obj_regexp = re.compile(r'[a-z_][a-zA-Z0-9_-]*')
   if (not(obj_regexp.match(in_args.username))):
      sys.exit("error: the username must only contain alphanumeric characters or an underscore, and must not start with a number ")
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
   obj_regexp = re.compile(r'^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$|^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$')
   if (not(obj_regexp.match(in_args.svm))):
      sys.exit("error: the svm parameter must be either an IP address or a hostname")

   # connect to filer
   obj_svm = NaServer(in_args.svm, 1, 3)
   result = obj_svm.set_transport_type('HTTPS')
   if(result and (result.results_errno() != 0)) :
      sys.exit("error: connection to filer failed; " + result.results_reason())
   result = obj_svm.set_style('LOGIN')
   if(result and (result.results_errno() != 0)):
      sys.exit("error: connection to filer failed; " + result.results_reason())
   result = obj_svm.set_admin_user(in_args.username,getpass.getpass())

   # check that the api is reachable
   result = obj_svm.invoke("system-get-version")
   if(result.results_status() == "failed"):
      sys.exit("error: cannot connect to filer; " + result.results_reason())

   # check that the junction path does not already exist
   string_uuid = str(uuid.uuid1()).strip()
   result = obj_svm.invoke("volume-get-iter")
   if(result.results_status() == "failed"):
      sys.exit("error: api request failed; " + result.results_reason())
   for volume in result.child_get("attributes-list").children_get():
      if (volume.child_get("volume-id-attributes").child_get_string("name").strip() == string_uuid):
         sys.exit("error: volume UUID clash; already exists")
      if (volume.child_get("volume-state-attributes").child_get_string("is-junction-active")):
         if (volume.child_get("volume-id-attributes").child_get_string("junction-path").strip().replace("/","") == in_args.name.strip()):
            sys.exit("error: share name already exists as junction path")

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
   print "+------------------------------------+----------------------------------------------------------------------------------+"


###
### main
###

# argparse instantiation
parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers()
create_parser = subparsers.add_parser("create")
create_parser.add_argument("name", help="the name of the new share")
create_parser.add_argument("size", help="the size of the share in GB")
create_parser.add_argument("type", help="the service level; value | capacity")
create_parser.add_argument("svm", help="the hostname or IP address of the NetApp SVM")
create_parser.add_argument("username", help="the admin username")
create_parser.set_defaults(func=create_share)
delete_parser = subparsers.add_parser("delete")
delete_parser.add_argument("name", help="the name of the share to delete")
delete_parser.add_argument("svm", help="the hostname or the IP address of the NetApp SVM")
delete_parser.add_argument("username", help="the admin username")
delete_parser.set_defaults(func=delete_share)
delete_parser = subparsers.add_parser("list")
delete_parser.add_argument("svm", help="the hostname or the IP address of the NetApp SVM")
delete_parser.add_argument("username", help="the admin username")
delete_parser.set_defaults(func=list_share)
delete_parser = subparsers.add_parser("access_allow")
delete_parser.add_argument("name", help="the name of the share to modify access on")
delete_parser.add_argument("access_type", help="the protocol type for this access list entry; ip")
delete_parser.add_argument("access_to", help="the address range for this access list entry; <address>[/suffix]")
delete_parser.add_argument("svm", help="the hostname or the IP address of the NetApp SVM")
delete_parser.add_argument("username", help="the admin username")
delete_parser.set_defaults(func=access_allow_share)

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
