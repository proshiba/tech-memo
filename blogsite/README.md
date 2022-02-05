# 主にWordPressに関するメモ

ブログサイトとしてWordPressを作成しているが、そこで設定したことをここにメモするというストロングスタイル  
当たり前だが、センシティブなものは公開しない。公開してたら泣くことになる。。。

■linux権限の設定  

```
chown apache:apache -R /var/www/html/wordpress
```

■selinux関連の設定  
```
sudo semanage fcontext -a -t httpd_sys_rw_content_t "/var/www/html/wordpress/(xmlrpc.php|wp-blog-header.php|readme.html|wp-signup.php|index.php|wp-cron.php|wp-config-sample.php|wp-login.php|wp-settings.php|license.txt|wp-mail.php|wp-links-opml.php|wp-load.php|wp-activate.php|wp-trackback.php|wp-comments-post.php)?"
sudo semanage fcontext -a -t httpd_sys_rw_content_t "/var/www/html/wordpress/wp-content(/.*)?"
sudo semanage fcontext -a -t httpd_sys_rw_content_t "/var/www/html/wordpress/wp-includes(/.*)?"
sudo semanage fcontext -a -t httpd_sys_rw_content_t "/var/www/html/wordpress/wp-admin(/.*)?"
sudo restorecon -R /var/www/html/wordpress
```

