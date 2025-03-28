from django.contrib import admin
from .models import SmartMeter, Transaction, ClusterRegistration


class ClusterRegistrationAdmin(admin.ModelAdmin):
    readonly_fields = ("token",)


class TransactionAdmin(admin.ModelAdmin):
    pass


admin.site.register(ClusterRegistration, ClusterRegistrationAdmin)
admin.site.register(SmartMeter)
admin.site.register(Transaction, TransactionAdmin)
