# install kvmd fan
1、if you use pikvm image, login as root
```
su -
rw
git clone https://github.com/ThomasVon2021/blikvm.git
cd blikvm/package/kvmd-fan
bash install.sh
ro
```

2、if you want to disable fan
```
systemctl disable kvmd-fan
```

3、if you want to start fan
```
systemctl enable kvmd-fan
```

4、if you want to see the fan work status
```
systemctl status kvmd-fan
```
