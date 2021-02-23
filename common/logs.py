from pythonjsonlogger.jsonlogger import JsonFormatter


class LogFormatter(JsonFormatter):

    def add_fields(self, log_record: dict, record, message_dict):
        super().add_fields(log_record, record, message_dict)

        log_record['uri'] = record.request.path
        log_record['method'] = record.request.method
        log_record['params'] = dict(GET=dict(record.request.GET), POST=dict(record.request.POST))
        log_record['user'] = record.request.user.pk
        log_record['headers'] = dict(record.request.headers)

        log_record.pop('request')
