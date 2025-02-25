from django.contrib import admin
from .models import SmartMeter, ProvisioningToken, Transaction


class ProvisioningTokenAdmin(admin.ModelAdmin):
    readonly_fields = ("token",)


class TransactionAdmin(admin.ModelAdmin):
    pass


admin.site.register(ProvisioningToken, ProvisioningTokenAdmin)
admin.site.register(SmartMeter)
admin.site.register(Transaction, TransactionAdmin)
