from evaluate.eval_runner import EvalRunner
from evaluate.report import Report

if __name__ == "__main__":
  runner = EvalRunner(dataset_path="evaluate/dataset.json")
  results = runner.run()
  print("*"*50)
  print(results)
  print("*"*50)
  Report.generate(results,output_path="evaluate/finalreport05200426.json")

# from evaluate.eval_retrieval import EvalRunner
# # from evaluate.report import Report

# if __name__ == "__main__":
#   runner = EvalRunner(dataset_path="evaluate/dataset.json")
#   results = runner.run()
#   print("*"*50)
#   print(results)
#   print("*"*50)
#   # Report.generate(results,output_path="evaluate/finalreport.json")