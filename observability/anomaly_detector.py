from config.config import MAX_GENERATION_LATENCY,MAX_TOTAL_LATENCY

class AnomalyDetector:
	RULES = {
		"slow_query":lambda log:log['latency']['total']>MAX_TOTAL_LATENCY,
		"low_confidence":lambda log:log['confidence'] in ['LOW','low'],
		"rewrite_failed" : lambda log:log['rewrite_triggered'] and log['confidence'] in ['LOW','low'],
		"empty_retrieval" : lambda log: len(log['chunk_ids']) == 0,
		"generation_slow" : lambda log: log['latency']['generation'] > MAX_GENERATION_LATENCY
		}
		
	@staticmethod
	def detect(log:dict)->list:
		anomalies = []
		for name,rule in AnomalyDetector.RULES.items():
			try:
				if rule(log):
					anomalies.append(name)
			except Exception:
				pass
		return anomalies