#除了.git文件夹，其他文件都同步  
rsync -av --exclude=.git --exclude=upload-image.sh ../EasyAccountsBuild/ ../EasyAccountsOpenSource/
