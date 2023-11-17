#!/bin/bash

echo "installing ansible hosts inventory"
sudo mkdir /inventory
sudo chown -R nzeer:nzeer /inventory
cd /inventory
git clone git@github.com:nzeer/inventory.git .

echo "beginning repos installation"
cd ~
mkdir ~/repos
sudo ln -s ~/repos /

cd ~/repos

#playbooks
echo "installing playbooks repo"
git clone git@github.com:nzeer/semaphore-repo.git
# dot files
echo "installing dotfiles repo"
git clone git@github.com:nzeer/dotfiles.git
# system configs
echo "installing system configs repo"
git clone git@github.com:nzeer/configs.git
# scripts
echo "installing scripts repo"
git clone git@github.com:nzeer/scripts.git
# ansible cfg
echo "installing ansible repo"
git clone git@github.com:nzeer/ansible.git

#yay
echo "installing yay"
sudo pacman -S --needed git base-devel
git clone https://aur.archlinux.org/yay.git
cd yay
makepkg -si
echo "Done."

cd ~

ln -s ~/repos/dotfiles/.oh-my-bash ~
ln -s ~/repos/dotfiles/oh-my-bash-config/bashrc ~/.bashrc

ln -s ~/repos/dotfiles/.bash.d ~
ln -s ~/repos/dotfiles/.tmux.conf ~

# system configs
sudo mkdir /etc/ansible
sudo cp ~/repos/ansible/config/ansible.cfg /etc/ansible/
mkdir ~/.ansible
mkdir ~/.config
ln -s ~/repos/dotfiles/nvim ~/.config/

#setup pacman
sudo mv /etc/pacman.conf /etc/pacman.conf.bak
sudo cp ~/repos/configs/pacman/pacman.*conf /etc/


