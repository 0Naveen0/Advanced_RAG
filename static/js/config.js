
//export const API_BASE_URL = "https://skinny-boaster-periscope.ngrok-free.dev" // NGROK URL
//export const API_BASE_URL = "https://rag-architecture-v2.onrender.com" // Render URL

//const isLocalDev = window.location.hostname==='localhost' || window.location.hostname==='127.0.0.1';
//export const API_BASE_URL = isLocalDev ? "https://skinny-boaster-periscope.ngrok-free.dev" : "https://rag-architecture-v2.onrender.com";

const isRender = window.location.hostname.endsWith('.onrender.com');
export const API_BASE_URL = isRender ? "https://rag-architecture-v2.onrender.com" : "https://skinny-boaster-periscope.ngrok-free.dev" ;
