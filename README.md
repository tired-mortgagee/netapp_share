# netapp_share
Simple provisioning script for ONTAP similar in function to OpenStack Manila's ONTAP driver

This assumes that a NetApp SVM has already been provisioned for your OpenStack tenancy, that you can ping the SVM's IP address, 
and that the password of the 'vsadmin' user has been delivered to you.

The first thing that you need to run on each SVM is netapp_init.py. This initialises the SVM (enabled the NFS daemon for example). 
This only needs to be executed once. You will be prompted to change the password.

`./netapp_init.py <SVM_IP> vsadmin`

Now you can run the netapp_share.py script. This script implements the following OpenStack Manila commands in as similar a way as 
is practical to the NetApp ONTAP Manila driver in OpenStack.
* create (create a share NFS ONLY CURRENTLY)
* delete (delete a share)
* list (lists all existing shares on the SVM)
* access_allow (allow access to the share from an IP range)
* extend (increase the size of an existing share)
* shrink (decrease the size of an existing share)
* quota_show (show the provisioning quota in GB for the tenant in this SVM)
* show (show details for a share)

The netapp_share.py script gives you the choice of interactive authentication or certificate-based authentication. If you want to 
use certificate authentication then you need to make sure that you have both the PEM and KEY file, and that the CN of the certificate
matches the user on the SVM (i.e. vsadmin). There is a procedure that describes how to install a client certificate for your SVM in the 
file procedures.md in this repo.

For example, to create a NFS share called "mytest" with a size of 10GB using certificate authentication run the following command.

` ./netapp_share.py create -cert vsadmin.pem,vsadmin.key mytest 10 value mysvm.domain.local`

`+------------------------------------+------------------------------------------------------------------------+`

`| Property                           | Value                                                                  |`

`+------------------------------------+------------------------------------------------------------------------+`

`| status                             | available                                                              |`

`| export_locations                   | path = 10.0.0.5:/841b0820-a453-11e9-8845-0050569d4dd9                  |`

`|                                    | share_instance_id = 841b0820-a453-11e9-8845-0050569d4dd9               |`

`| size                               | 10                                                                     |`

`| name                               | mytest                                                                 |`

`| extra-specs                        | tier = value tier                                                      |`

`+------------------------------------+------------------------------------------------------------------------+`

The 'tier' in the above example refers to the backend disk type being used. In out platform, 'value' refers to a tier that
uses SAS drives and 'capacity' refers to a tier that uses NL-SAS drives. In this example the SVM IP address is 10.0.0.5 and 
your /etc/hosts file has been updated to resolve mysvm.domain.local to this address.

You can now mount the NFS share on your client. Don't forget to update /etc/fstab.

`mount -t nfs 10.0.0.5:/841b0820-a453-11e9-8845-0050569d4dd9 /mnt/mymount`

The following example shows how to list all of the shares currently provisioned in your SVM using interactive authentication

`./netapp_share.py list mysvm.domain.local`
`login as: vsadmin`
`Password: ************`
`+----------------------------------------------+----------------+-----------+`

`| ID                                           | Name           | Size      |`

`+----------------------------------------------+----------------+-----------+`

`| share_841b0820_a453_11e9_8845_0050569d4dd9   | mytest         | 10        |`

`| share_a7655a20_a39e_11e9_8d25_0050569d4dd9   | quack          | 10        |`

`+----------------------------------------------+----------------+-----------+`




