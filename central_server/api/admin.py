from django.contrib import admin
from .models import SmartMeter, Transaction, ClusterRegistration, BCOrder, BCTransaction


class ClusterRegistrationAdmin(admin.ModelAdmin):
    readonly_fields = ("token",)


class TransactionAdmin(admin.ModelAdmin):
    pass


admin.site.register(ClusterRegistration, ClusterRegistrationAdmin)
admin.site.register(SmartMeter)
admin.site.register(BCOrder)
admin.site.register(BCTransaction)
admin.site.register(Transaction, TransactionAdmin)
