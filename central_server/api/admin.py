from django.contrib import admin
from .models import SmartMeter, ClusterRegistration, BCOrder, BCTransaction


class ClusterRegistrationAdmin(admin.ModelAdmin):
    readonly_fields = ("token",)


admin.site.register(ClusterRegistration, ClusterRegistrationAdmin)
admin.site.register(SmartMeter)
admin.site.register(BCOrder)
admin.site.register(BCTransaction)
