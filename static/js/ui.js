
const spinner = document.getElementById("loading");
const answerBox = document.getElementById("answer");
//const confidenceBox = document.getElementById("confidence");
//const sourceBox = document.getElementById("source");
const confidenceBox1 = document.getElementById("confidence1");
const sourceBox1 = document.getElementById("source1");
const latencyBox = document.getElementById("latency_total");


export function showLoading(){
    spinner.style.display = "block";
    
}

export function hideLoading(){
    spinner.style.display = "none";
}

export function displayAnswer(result){
    answerBox.textContent=result.answer;
    //confidenceBox.textContent=result.confidence;
    confidenceBox1.textContent=result.confidence;
    latencyBox.textContent = result.latency;
    if(result.source){
       //sourceBox.textContent= `Source:${result.source} (Chunk ${result.chunk_id})`;
       sourceBox1.textContent= `Source:${result.source} (Chunk ${result.chunk_id})`;

    }else{
        //sourceBox.textContent= "";
        sourceBox1.textContent = "";
    }
    
}

