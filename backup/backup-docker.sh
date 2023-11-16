#!/bin/bash
####################################
#
# Backup to NFS mount script.
#
####################################

# What to backup. 
backup_files="/var/lib/docker /home/nzeer/docker"

# Where to backup to.
dest="/home/backup"

# Create archive filename.
datetime=$(date +%F)
#time=$(date +%H%M)
#file=$(file)
archive_file="$datetime-docker.tar.gz"
archive_path="$dest/$archive_file"

echo $archive_file
echo $archive_path

# backup info
backup_user="nzeer"
backup_server="172.16.0.70"
backup_storage_location="/home/backup"
backup_destination="$backup_user@$backup_server:$backup_storage_location"

# Print start status message.
echo "Backing up $backup_files to $archive_path on $backup_destination"
date
echo

# Backup the files using tar.
sudo tar -cvzf $archive_path $backup_files
sudo rsync $archive_path $backup_destination
# Print end status message.
echo
echo "Backup finished"
date
