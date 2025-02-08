from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin

from .models import News


@admin.register(News)
class NewsAdmin(SummernoteModelAdmin):
    list_display = (
        "id",
        "title",
        "publication_date",
        "author",
    )
    list_display_links = ("id", "title")
    list_filter = ("publication_date", "author")
    search_fields = ("title", "content")
    summernote_fields = "content"
    readonly_fields = (
        "publication_date",
        "author",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "main_image",
                    "content",
                ),
            },
        ),
        (
            "Date information",
            {
                "fields": (
                    "publication_date",
                    "author",
                ),
            },
        ),
    )

    def save_form(self, request, form, change):
        form.instance.author = request.user
        return super().save_form(request, form, change)
