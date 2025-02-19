#除了.git文件夹，其他文件都同步  
rsync -av --exclude=.git --exclude=upload-image.sh --exclude=OtpAuth --exclude=ydjz_web_desktop ../EasyAccountsBuild/ ../EasyAccountsOpenSource/
