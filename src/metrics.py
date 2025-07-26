from prometheus_client import Histogram

FILE_SIZE_HISTOGRAM = Histogram('file_check_service_file_size', 'file size in bytes', ['bytes'])
REQUEST_TIME = Histogram(
    'file_check_service_requests_time', 'Number of seconds that request takes', ['path', 'method', 'status']
)
