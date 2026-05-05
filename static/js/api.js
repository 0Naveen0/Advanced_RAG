import {API_BASE_URL} from "./config.js";
// const test_result ={
    // answer : "This is answer",
    // confidence: "HIGH",
    // source:"File.txt",
	// chunk_id:"1"
// }
 export async function askQuestion(query){
	 console.log(`Query->${query}`);
	 console.log(`API->${API_BASE_URL}/ask`);
     const response = await fetch(`${API_BASE_URL}/ask`,{
         method:"POST",
         headers:{
             "Content-Type":"application/json"
         },
         body:JSON.stringify({query})
     });
     if(!response.ok){
         throw new Error('API Request Failed');
     }
     return await response.json();
 }

// export  function askQuestion(query){
   
    // return  test_result;
// }


