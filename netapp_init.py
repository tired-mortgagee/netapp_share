#!/usr/bin/python

#########################################################################################
#########################################################################################
##
## NetApp SVM Initialisation Script - For OpenStack Deployments
##
## tired.mortgagee@gmail.com
## v0.2 15.04.2019
## change log at bottom of this file
##
## current limitations
## - password can only be entered interactively
## - amatuer attempt
##

#####
##### includes
#####

from NaServer import *
import argparse
import getpass

#####
##### command line argument parsing
#####

# argparse instantiation
parser = argparse.ArgumentParser()
parser.add_argument("svm", help="the hostname or IP address of the NetApp SVM")
parser.add_argument("username", help="the admin user provided for the SVM")
#parser.add_argument("password", help="the password for the admin user")
ns_args = parser.parse_args()

# type and syntax checking on command line args
obj_regexp = re.compile(r'[a-z_][a-zA-Z0-9_-]*')
if (not(obj_regexp.match(ns_args.username))):
   sys.exit("error: the username must only contain alphanumeric characters or an underscore, and must not start with a number ")
obj_regexp = re.compile(r'^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$|^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$')
if (not(obj_regexp.match(ns_args.svm))):
   sys.exit("error: the svm parameter must be either an IP address or a hostname")

#####
##### netapp api calls
#####

# connect to filer
obj_svm = NaServer(ns_args.svm, 1, 3)
result = obj_svm.set_transport_type('HTTPS')
if (result and (result.results_errno() != 0)) :
   sys.exit("error: connection to svm failed; " + result.results_reason())
result = obj_svm.set_style('LOGIN')
if (result and (result.results_errno() != 0)):
   sys.exit("error: connection to svm failed; " + result.results_reason())
result = obj_svm.set_admin_user(ns_args.username,getpass.getpass())

# check that the api is reachable
result = obj_svm.invoke("system-get-version")
if(result.results_status() == "failed"):
   sys.exit("error: cannot execute api; " + result.results_reason())

# check that nfs service is enabled
result = obj_svm.invoke("nfs-status")
if(result.results_status() == "failed"):
   sys.exit("error: cannot execute api; " + result.results_reason())

# enable nfs service 
if (result.child_get_string("is-enabled") == "false"):
   obj_nfs_service_create = NaElement("nfs-service-create")
   obj_nfs_service_create.child_add_string("is-nfsv3-enabled","false")
   obj_nfs_service_create.child_add_string("is-nfsv40-enabled","true")
   obj_nfs_service_create.child_add_string("is-nfsv40-acl-enabled","true")
   obj_nfs_service_create.child_add_string("is-nfsv41-enabled","true")
   obj_nfs_service_create.child_add_string("is-nfsv41-acl-enabled","true")
   result = obj_svm.invoke_elem(obj_nfs_service_create)
   if(result.results_status() == "failed"):
      sys.exit("error: cannot execute api; " + result.results_reason())   
   print "NFS service enabled"
else:
   print "NFS service already enabled"

# check that open export-policy is created
obj_export_policy_get = NaElement("export-policy-get")
obj_export_policy_get.child_add_string("policy-name","open")
result = obj_svm.invoke_elem(obj_export_policy_get)

# create open export-policy
if(result.results_status() == "failed"):
   obj_export_policy_create = NaElement("export-policy-create")
   obj_export_policy_create.child_add_string("policy-name","open")
   result = obj_svm.invoke_elem(obj_export_policy_create)
   if(result.results_status() == "failed"):
      sys.exit("error: cannot execute api; " + result.results_reason())
   obj_rorule = NaElement("ro-rule")
   obj_rorule.child_add_string("security-flavor","sys")
   obj_rwrule = NaElement("rw-rule")
   obj_rwrule.child_add_string("security-flavor","sys")
   obj_secrule = NaElement("super-user-security")
   obj_secrule.child_add_string("security-flavor","sys")
   obj_export_rule_create = NaElement("export-rule-create")
   obj_export_rule_create.child_add_string("policy-name","open")
   obj_export_rule_create.child_add_string("client-match","0.0.0.0/0")
   obj_export_rule_create.child_add(obj_rorule)
   obj_export_rule_create.child_add(obj_rwrule)
   obj_export_rule_create.child_add(obj_secrule)
   result = obj_svm.invoke_elem(obj_export_rule_create)
   if(result.results_status() == "failed"):
      sys.exit("error: cannot execute api; " + result.results_reason())   
print "created open export-policy"

# update default export-policy
obj_rorule = NaElement("ro-rule")
obj_rorule.child_add_string("security-flavor","none")
obj_rwrule = NaElement("rw-rule")
obj_rwrule.child_add_string("security-flavor","never")
obj_export_rule_create = NaElement("export-rule-create")
obj_export_rule_create.child_add_string("policy-name","default")
obj_export_rule_create.child_add_string("client-match","0.0.0.0/0")
obj_export_rule_create.child_add(obj_rorule)
obj_export_rule_create.child_add(obj_rwrule)
result = obj_svm.invoke_elem(obj_export_rule_create)
if(result.results_status() == "failed"):
      sys.exit("error: cannot execute api; " + result.results_reason())
print "updated default export-policy"

print "initialisation successfully completed"

#########################################################################################
#########################################################################################
##
## Change Log
##
## 2019.04.10   Initial release
## 2019.04.15   No changes in this file, version increment to align with netapp_share.py

