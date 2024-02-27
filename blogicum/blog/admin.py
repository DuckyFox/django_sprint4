from django.contrib import admin

from .models import Post, Category, Location


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'text',
        'pub_date',
        'is_published',
        'category',
        'location'
    )
    list_editable = (
        'is_published',
        'category',
        'pub_date'
    )

    search_fields = ('title',)

    list_filter = ('category',)
    list_display_links = ('title',)


# Register custom admin view
admin.site.register(Post, PostAdmin)
admin.site.register(Category)
admin.site.register(Location)
