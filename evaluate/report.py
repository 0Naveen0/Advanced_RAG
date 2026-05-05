import json
from datetime import datetime
class Report:
	@staticmethod
	def generate(results:list,output_path:str=None):
		total = len(results)
		domain = [r for r in results if not r['should_refuse']]
		off_domain = [r for r in results if r['should_refuse']]
		
		#Aggregate Metrics
		avg_precision = Report._avg(domain,'precision')
		avg_recall = Report._avg(domain,'recall')
		avg_f1 = Report._avg(domain,'f1')
		avg_kw = Report._avg(domain,'keyword_match')
		avg_latency = Report._avg(results,'latency_seconds')
		
		#Refusal accuracy
		refusal_accuracy = sum(1 for r in off_domain if r['refusal_correct'])/len(off_domain) if off_domain else 0.0
		#Rewrite	Stat
		rewrite_total = sum(1 for r in results if r['rewrite_triggered'])
		rewrite_helped = sum(1 for r in results if r['rewrite_triggered'] and r['f1']>0)
		# Difficulty checks
		difficulty_breakdown = Report._breakdown_by(domain,'difficulty_level')
		
		# Category checks
		category_breakdown = Report._breakdown_by(domain,'category')
		
		report = {
					'timestamp':datetime.now().isoformat(),
					'total_queries':total,
					'summary':{
								'precision':round(avg_precision,3),
								'recall':round(avg_recall,3),
								'f1':round(avg_f1,3),
								'keyword_match':round(avg_kw,3),
								'avg_latency_second':round(avg_latency),
								'refusal_accuracy':round(refusal_accuracy),
								'rewrite_trigger_rate':round(rewrite_total,3),
								'rewrite_success_rate':round(rewrite_helped/rewrite_total,3) if rewrite_total else 0.0,
								},
					'by_difficulty':difficulty_breakdown,
					'by_category':category_breakdown,
					'failures':[r for r in results if r['f1']==0 and not r['should_refuse']],
					'raw_results':results					
					}
					
		Report._print_summary(report)
		if output_path:
			import os
			os.makedirs(os.path.dirname(output_path),exist_ok=True)
			with open(output_path,"w",encoding="utf-8")	as f:
				json.dump(report,f,indent=2,ensure_ascii=False)
				print(f"\n[Report] Saved to {output_path}")
		return report
	
	@staticmethod	
	def _avg(items:list,key:str)->float:
		if not items:
			return 0.0
		return sum(i[key] for i in items)/len(items)
	
	
	@staticmethod
	def _breakdown_by(items:list,key:str)->dict:
		groups = {}
		for item in items:
			group = item.get(key,'unknown')
			if group not in groups:
				groups[group]=[]
			groups[group].append(item)
		
		return {group:{'count':len(group_items),'precision':round(Report._avg(group_items,'precision'),3),'recall':round(Report._avg(group_items,'recall'),3),'f1':round(Report._avg(group_items,'f1'),3),}
		for group,group_items in groups.items()}
		
		
	@staticmethod
	def _print_summary(report:dict):
		s= report['summary']
		print("\n"+"="*50)
		print("EVALUATION REPORT")
		print("="*50)
		print(f"Total Queries : {report['total_queries']}")
		print(f"Precision: {s["precision"]}")
		print(f"Recall: {s["recall"]}")
		print(f"F1: {s["f1"]}")
		print(f"Keyword Match: {s["keyword_match"]}")
		print(f"Avg Latency: {s["avg_latency_second"]}s")
		print(f"Refusal Accuracy: {s["refusal_accuracy"]}")
		print(f"Rewrite Trigger: {s["rewrite_trigger_rate"]}")
		print(f"Rewrite Sucess %: {s["rewrite_success_rate"]}")
		print("="*50)