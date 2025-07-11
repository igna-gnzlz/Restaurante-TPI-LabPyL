from django.utils import timezone

class DateTimeUtils:
    @staticmethod
    def get_local_date():
        return timezone.localtime().date()

    @staticmethod
    def get_local_time():
        return timezone.localtime().time()
    
    @staticmethod
    def get_local_datetime():
        return timezone.localtime()
