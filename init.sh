#!/bin/zsh

brew install ansible git python3 font-source-code-pro-for-powerline
ansible-playbook -i localhost playbook.yml

