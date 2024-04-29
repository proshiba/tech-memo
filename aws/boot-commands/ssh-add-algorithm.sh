#! /bin/bash
sudo sed -i '1s/^/PubkeyAcceptedAlgorithms=+ssh-rsa\n/' /etc/ssh/sshd_config

# teratermなど、ssh-rsaしか対応していないターミナルで接続するとき用。
# 参考: https://help.arena.ne.jp/hc/ja/articles/7134065589271-Tera-Term%E3%81%A7%E3%82%A4%E3%83%B3%E3%82%B9%E3%82%BF%E3%83%B3%E3%82%B9%E3%81%B8SSH%E6%8E%A5%E7%B6%9A-%E3%83%AD%E3%82%B0%E3%82%A4%E3%83%B3%E3%81%8C%E3%81%A7%E3%81%8D%E3%81%BE%E3%81%9B%E3%82%93