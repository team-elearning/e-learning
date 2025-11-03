// import axios from 'axios';


// const instance = axios.create({
//     baseURL: '/api',
//     timeout: 10000,
// });


// export default instance;
import axios from 'axios'
const http = axios.create({
  baseURL: '/api',                
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' }
})
export default http
