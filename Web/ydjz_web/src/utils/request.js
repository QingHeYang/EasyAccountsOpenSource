import axios from "axios";
import { Notify } from 'vant';

function request (options){
  return axios(options).then(response=>{
      if (response.data.code!=0){
          Notify({ type: 'warning', message: response.data.code+"\n"+response.data.msg, duration: 800,});
          caches()
      }
    return response
  })
    .catch(err=>{
      const {response : {status,statusText}} = err;
      Notify({ type: 'warning', message: status +statusText+"\n"+options.url, duration: 800,});
      return Promise.reject(err)
    })
}

export default request;
