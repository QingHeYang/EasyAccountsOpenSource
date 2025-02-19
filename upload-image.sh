docker push 775495797/easyaccounts-nginx:latest && 
docker tag 775495797/easyaccounts-nginx:latest registry.cn-beijing.aliyuncs.com/easy_accounts/easyaccounts-nginx:latest &&
docker push registry.cn-beijing.aliyuncs.com/easy_accounts/easyaccounts-nginx:latest &&
docker push 775495797/easyaccounts-webhook:latest &&
docker tag 775495797/easyaccounts-webhook:latest  registry.cn-beijing.aliyuncs.com/easy_accounts/easyaccounts-webhook:latest &&
docker push registry.cn-beijing.aliyuncs.com/easy_accounts/easyaccounts-webhook:latest && 
docker push 775495797/easyaccounts-server:latest && 
docker push registry.cn-beijing.aliyuncs.com/easy_accounts/easyaccounts-server:latest && 
docker tag 775495797/easyaccounts-server:latest registry.cn-beijing.aliyuncs.com/easy_accounts/easyaccounts-server:latest && 
docker push registry.cn-beijing.aliyuncs.com/easy_accounts/mysql:8.0.31