checkup.config = {
	"timeframe": 1 * time.Day,
	"refresh_interval": 60,
	"storage": {
		"url": "https://bcdc-checkup.data.gov.bc.ca"
	},
	"status_text": {
		"healthy": "Service Up",
		"degraded": "Degraded Service",
		"down": "Service Disruption"
	}
};
