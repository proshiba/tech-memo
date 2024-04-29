#! /bin/bash
sudo sed -i '1s/^/PubkeyAcceptedAlgorithms=+ssh-rsa\n/' /etc/ssh/sshd_config