from prometheus_client import Counter
from prometheus_client import Histogram

PROJECT_COUNTER_METRIC = Counter(
    'file_check_service_project_counter', 'how many times the project was checked', ['project']
)
FILE_SIZE_HISTOGRAM = Histogram('file_check_service_file_size', 'file size in bytes', ['bytes'])
REQUEST_TIME = Histogram(
    'file_check_service_requests_time', 'Number of seconds that request takes', ['path', 'method', 'status']
)
