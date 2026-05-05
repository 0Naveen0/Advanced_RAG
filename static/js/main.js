import {askQuestion} from "./api.js";
import {displayAnswer,showLoading,hideLoading} from "./ui.js";

const input = document.getElementById("query_input");
const form = document.getElementById("query_form");


form.addEventListener("submit",
    async (event) =>{
		// console.log(input.value)
        event.preventDefault();
        var query = input.value;
        showLoading();
        try{
            const result = await askQuestion(query);
			// console.log(result)
            displayAnswer(result);        
        
        }catch(error){
            alert("Error Fetching Data");
        }finally{
            hideLoading();
    }


});