import axios from "axios";
import {showNotify} from 'vant';
import store from '@/store';


function request (options){
  return axios(options).then(response=>{
      if (response.data.code!=0){
          showNotify({ type: 'warning', message: response.data.code+"\n"+response.data.msg, duration: 800,});
          if (response.data.code === 4010||response.data.code === 4011) {
              store.commit('setRedirectToVerify', true);
          }
          caches()
      }
    return response
  })
    .catch(err=>{
      const {response : {status,statusText}} = err;
      showNotify({ type: 'warning', message: status +statusText+"\n"+options.url, duration: 800,});
      return Promise.reject(err)
    })
}

export default request;
