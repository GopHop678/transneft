import os
from django.conf import settings
from django.http import HttpResponse, FileResponse
from django.utils.deprecation import MiddlewareMixin


class RangeFileMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if request.path.startswith(settings.MEDIA_URL) and response.status_code == 200:
            if 'HTTP_RANGE' in request.META:
                # Обработка Range-запросов (упрощенная версия)
                path = os.path.join(settings.MEDIA_ROOT, request.path.replace(settings.MEDIA_URL, ''))
                file_size = os.path.getsize(path)
                range_header = request.META['HTTP_RANGE'].split('=')[1]
                start, end = range_header.split('-')
                start = int(start)
                end = int(end) if end else file_size - 1
                length = end - start + 1

                with open(path, 'rb') as f:
                    f.seek(start)
                    data = f.read(length)

                response = HttpResponse(data, status=206, content_type=response['Content-Type'])
                response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
                response['Content-Length'] = length
                response['Accept-Ranges'] = 'bytes'
            else:
                response['Accept-Ranges'] = 'bytes'
        return response